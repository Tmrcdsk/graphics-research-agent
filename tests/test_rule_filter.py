from __future__ import annotations

from app.pipeline.rule_filter import score_paper
from app.sources.models import PaperItem


def test_rule_filter_scores_rendering_paper_as_candidate(sample_papers: list[PaperItem]) -> None:
    result = score_paper(sample_papers[0], threshold=5)

    assert result.is_candidate
    assert result.score >= 5
    assert "path tracing" in result.positive_matches
    assert "restir" in result.positive_matches


def test_rule_filter_penalizes_medical_and_language_model_noise(
    sample_papers: list[PaperItem],
) -> None:
    result = score_paper(sample_papers[1], threshold=5)

    assert not result.is_candidate
    assert result.score < 5
    assert "medical" in result.negative_matches
    assert "ct" in result.negative_matches
    assert "language model" in result.negative_matches
