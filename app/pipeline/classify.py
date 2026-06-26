from __future__ import annotations

from app.llm.schemas import ClassificationResult, ReadPriority
from app.pipeline.rule_filter import RuleFilterResult
from app.sources.models import PaperItem


def fallback_classification_for_dry_run(
    paper: PaperItem, rule_result: RuleFilterResult
) -> ClassificationResult:
    priority = ReadPriority.MUST_READ if rule_result.score >= 12 else ReadPriority.READ_LATER
    tags = rule_result.positive_matches[:8] or ["rendering"]
    score = max(1, min(5, 2 + rule_result.score // 5))
    return ClassificationResult(
        is_graphics_related=True,
        is_rendering_related=True,
        main_category="computer graphics / rendering",
        sub_tags=tags,
        technical_keywords=tags,
        novelty_score=score,
        job_relevance_score=score,
        read_priority=priority,
        reason=(
            "Dry-run fallback based on rule-filter matches because DeepSeek is not configured."
        ),
        uncertainty="This is not an LLM classification and must not be treated as final.",
    )
