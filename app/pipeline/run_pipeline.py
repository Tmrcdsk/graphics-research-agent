from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from app.config import Settings, get_settings
from app.llm.deepseek_client import DeepSeekClient, DeepSeekError
from app.llm.prompts import CLASSIFICATION_PROMPT_VERSION, SUMMARY_PROMPT_VERSION
from app.llm.schemas import ClassificationResult, ReadPriority, SummaryResult
from app.pipeline.classify import fallback_classification_for_dry_run
from app.pipeline.dedupe import NewPaper, insert_new_papers
from app.pipeline.rule_filter import RuleFilterResult, score_paper
from app.pipeline.summarize import fallback_summary_for_dry_run
from app.publishers.telegram import TelegramPublisher, render_telegram_message
from app.sources.models import PaperItem
from app.sources.source_factory import build_default_source
from app.storage.db import Database, init_database

logger = logging.getLogger(__name__)

PUBLISHABLE_PRIORITIES = {ReadPriority.MUST_READ, ReadPriority.READ_LATER}


class Source(Protocol):
    source_name: str

    async def fetch_recent(self) -> list[PaperItem]: ...


class LlmClient(Protocol):
    is_configured: bool

    async def classify_paper(self, paper: PaperItem) -> ClassificationResult: ...

    async def summarize_paper(
        self, paper: PaperItem, classification: ClassificationResult
    ) -> SummaryResult: ...


class Publisher(Protocol):
    channel: str

    async def send_message(self, message: str): ...


@dataclass(frozen=True)
class CandidatePaper:
    new_paper: NewPaper
    rule_result: RuleFilterResult


@dataclass(frozen=True)
class SummaryCandidate:
    paper_id: int
    paper: PaperItem
    rule_result: RuleFilterResult
    classification: ClassificationResult
    summary: SummaryResult


@dataclass
class PipelineStats:
    status: str = "running"
    fetched_count: int = 0
    new_count: int = 0
    duplicate_count: int = 0
    candidate_count: int = 0
    summarized_count: int = 0
    pushed_count: int = 0
    failed_count: int = 0
    error: str | None = None


async def run_once(
    *,
    settings: Settings | None = None,
    source: Source | None = None,
    llm_client: LlmClient | None = None,
    publisher: Publisher | None = None,
    database: Database | None = None,
) -> PipelineStats:
    settings = settings or get_settings()
    source = source or build_default_source(settings)
    llm_client = llm_client or DeepSeekClient(settings)
    publisher = publisher or TelegramPublisher(settings)

    owns_database = database is None
    database = database or init_database(settings)
    run_id = database.create_source_run(source.source_name)
    stats = PipelineStats()

    logger.info("Pipeline run started")
    try:
        papers = await source.fetch_recent()
        stats.fetched_count = len(papers)

        dedupe_result = insert_new_papers(database, papers)
        stats.new_count = len(dedupe_result.new_papers)
        stats.duplicate_count = dedupe_result.duplicate_count
        logger.info("New papers=%s duplicates=%s", stats.new_count, stats.duplicate_count)

        candidates = _select_rule_candidates(dedupe_result.new_papers, settings)
        stats.candidate_count = len(candidates)
        logger.info("Rule-filter candidates=%s", stats.candidate_count)

        summary_candidates = await _classify_and_summarize_candidates(
            candidates=candidates,
            settings=settings,
            llm_client=llm_client,
            database=database,
        )
        stats.summarized_count = len(summary_candidates)
        logger.info("Validated summaries=%s", stats.summarized_count)

        selected = select_for_push(summary_candidates, settings)
        stats.pushed_count = await _publish_selected(selected, database, publisher)

        stats.status = "success"
        database.finish_source_run(
            run_id,
            status="success",
            fetched_count=stats.fetched_count,
            new_count=stats.new_count,
            candidate_count=stats.candidate_count,
            pushed_count=stats.pushed_count,
        )
        logger.info("Pipeline run finished pushed=%s", stats.pushed_count)
        return stats
    except Exception as exc:  # noqa: BLE001 - pipeline must close source_runs on any failure.
        stats.status = "failed"
        stats.error = str(exc)
        stats.failed_count += 1
        database.finish_source_run(
            run_id,
            status="failed",
            fetched_count=stats.fetched_count,
            new_count=stats.new_count,
            candidate_count=stats.candidate_count,
            pushed_count=stats.pushed_count,
            error=str(exc),
        )
        logger.exception("Pipeline run failed")
        return stats
    finally:
        if owns_database:
            database.close()


def _select_rule_candidates(new_papers: list[NewPaper], settings: Settings) -> list[CandidatePaper]:
    candidates: list[CandidatePaper] = []
    for new_paper in new_papers:
        rule_result = score_paper(new_paper.paper, threshold=settings.rule_filter_threshold)
        if rule_result.is_candidate:
            candidates.append(CandidatePaper(new_paper=new_paper, rule_result=rule_result))
        else:
            logger.info(
                "Item below rule threshold source=%s item_id=%s score=%s",
                new_paper.paper.source_name,
                new_paper.paper.item_id,
                rule_result.score,
            )
    return candidates


async def _classify_and_summarize_candidates(
    *,
    candidates: list[CandidatePaper],
    settings: Settings,
    llm_client: LlmClient,
    database: Database,
) -> list[SummaryCandidate]:
    summary_candidates: list[SummaryCandidate] = []
    for candidate in candidates:
        paper = candidate.new_paper.paper
        try:
            classification, summary = await _classify_and_summarize_one(
                paper=paper,
                rule_result=candidate.rule_result,
                settings=settings,
                llm_client=llm_client,
            )
        except DeepSeekError as exc:
            logger.warning(
                "Skipping item after DeepSeek failure source=%s item_id=%s error=%s",
                paper.source_name,
                paper.item_id,
                exc,
            )
            continue

        if summary.read_priority not in PUBLISHABLE_PRIORITIES:
            logger.info(
                "Skipping non-publishable summary source=%s item_id=%s priority=%s",
                paper.source_name,
                paper.item_id,
                summary.read_priority.value,
            )
            continue

        database.save_summary(
            paper_id=candidate.new_paper.paper_id,
            model_name=settings.deepseek_model,
            prompt_version=f"{CLASSIFICATION_PROMPT_VERSION}+{SUMMARY_PROMPT_VERSION}",
            classification=classification.model_dump(mode="json"),
            summary=summary.model_dump(mode="json"),
            read_priority=summary.read_priority.value,
            relevance_score=candidate.rule_result.score,
            job_relevance_score=summary.job_relevance_score,
        )
        summary_candidates.append(
            SummaryCandidate(
                paper_id=candidate.new_paper.paper_id,
                paper=paper,
                rule_result=candidate.rule_result,
                classification=classification,
                summary=summary,
            )
        )
    return summary_candidates


async def _classify_and_summarize_one(
    *,
    paper: PaperItem,
    rule_result: RuleFilterResult,
    settings: Settings,
    llm_client: LlmClient,
) -> tuple[ClassificationResult, SummaryResult]:
    if getattr(llm_client, "is_configured", False):
        classification = await llm_client.classify_paper(paper)
        if classification.read_priority not in PUBLISHABLE_PRIORITIES:
            return classification, _archive_summary_from_classification(paper, classification)
        summary = await llm_client.summarize_paper(paper, classification)
        return classification, summary

    if settings.dry_run:
        logger.warning("DeepSeek is not configured; using DRY_RUN fallback summary")
        classification = fallback_classification_for_dry_run(paper, rule_result)
        summary = fallback_summary_for_dry_run(paper, classification)
        return classification, summary

    raise DeepSeekError("DeepSeek is not configured and DRY_RUN=false")


def _archive_summary_from_classification(
    paper: PaperItem, classification: ClassificationResult
) -> SummaryResult:
    return SummaryResult(
        title_zh=paper.title,
        one_sentence="Classification marked this paper as not publishable.",
        problem="Not summarized because read_priority is archive_only or skip.",
        method="No summary requested.",
        relation_to_user_goal=classification.reason,
        likely_usefulness="Not selected for Telegram push.",
        uncertainty=classification.uncertainty,
        read_priority=classification.read_priority,
        job_relevance_score=classification.job_relevance_score,
        novelty_score=classification.novelty_score,
    )


def select_for_push(
    candidates: list[SummaryCandidate],
    settings: Settings,
) -> list[SummaryCandidate]:
    sorted_candidates = sorted(
        candidates,
        key=lambda item: (
            0 if item.summary.read_priority == ReadPriority.MUST_READ else 1,
            -item.summary.job_relevance_score,
            -item.summary.novelty_score,
            -item.paper.published_at.timestamp(),
        ),
    )
    selected: list[SummaryCandidate] = []
    must_read_count = 0
    read_later_count = 0
    for candidate in sorted_candidates:
        if candidate.summary.read_priority == ReadPriority.MUST_READ:
            if must_read_count >= settings.max_push_must_read:
                continue
            must_read_count += 1
            selected.append(candidate)
        elif candidate.summary.read_priority == ReadPriority.READ_LATER:
            if read_later_count >= settings.max_push_read_later:
                continue
            read_later_count += 1
            selected.append(candidate)
    return selected


async def _publish_selected(
    selected: list[SummaryCandidate],
    database: Database,
    publisher: Publisher,
) -> int:
    pushed_count = 0
    for candidate in selected:
        if database.has_successful_publish(candidate.paper_id, publisher.channel):
            logger.info("Skipping already published paper_id=%s", candidate.paper_id)
            continue

        message = render_telegram_message(
            candidate.paper,
            candidate.classification,
            candidate.summary,
        )
        try:
            result = await publisher.send_message(message)
            database.record_publish_log(
                paper_id=candidate.paper_id,
                channel=publisher.channel,
                status=result.status,
                external_message_id=result.external_message_id,
                error=result.error,
            )
            pushed_count += 1
        except Exception as exc:  # noqa: BLE001 - record publisher failures and keep going.
            database.record_publish_log(
                paper_id=candidate.paper_id,
                channel=publisher.channel,
                status="failed",
                error=str(exc),
            )
            logger.warning("Telegram publish failed paper_id=%s error=%s", candidate.paper_id, exc)
    return pushed_count
