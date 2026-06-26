from __future__ import annotations

from app.llm.schemas import ClassificationResult, SummaryResult
from app.sources.models import PaperItem


def fallback_summary_for_dry_run(
    paper: PaperItem, classification: ClassificationResult
) -> SummaryResult:
    return SummaryResult(
        title_zh=paper.title,
        one_sentence=(
            "DRY_RUN local fallback: rule filtering marked this paper as relevant "
            "to the rendering learning goal."
        ),
        problem=(
            "A real summary requires DeepSeek to return validated structured JSON; "
            "the current environment has no DeepSeek API key."
        ),
        method=(
            "This fallback uses only the title, abstract, and rule-filter keywords. "
            "It does not call an external LLM."
        ),
        relation_to_user_goal=(
            "The item matched keywords related to real-time rendering, graphics "
            "pipelines, or adjacent technical areas."
        ),
        likely_usefulness=("Useful for validating the arXiv to SQLite to Telegram dry-run loop."),
        uncertainty=(
            "This is dry-run fallback content and should not be used for live "
            "recommendations or technical judgment."
        ),
        read_priority=classification.read_priority,
        job_relevance_score=classification.job_relevance_score,
        novelty_score=classification.novelty_score,
    )
