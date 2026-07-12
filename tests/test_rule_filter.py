from __future__ import annotations

import pytest

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


@pytest.mark.parametrize(
    ("source_name", "title", "expected_keyword"),
    [
        ("gpuopen", "AMD FSR Upscaling 4.1 is available", "fsr"),
        ("directx", "Direct3D Shader Model 6.10 preview", "direct3d"),
        ("vulkan", "Vulkan ray tracing acceleration structures", "vulkan"),
        (
            "siggraph_realtime",
            "Real-time neural rendering for interactive worlds",
            "neural rendering",
        ),
        ("siggraph_research", "A new path tracing sampling method", "path tracing"),
    ],
)
def test_rule_filter_covers_new_official_sources(
    sample_papers: list[PaperItem],
    source_name: str,
    title: str,
    expected_keyword: str,
) -> None:
    paper = sample_papers[0].model_copy(
        update={"source_name": source_name, "title": title, "abstract": "Technical update."}
    )

    result = score_paper(paper, threshold=5)

    assert result.is_candidate
    assert expected_keyword in result.positive_matches
