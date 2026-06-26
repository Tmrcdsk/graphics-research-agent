from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import Settings
from app.llm.deepseek_client import DeepSeekClient, _extract_message_content, _parse_json_object
from app.llm.schemas import ClassificationResult, ReadPriority
from app.sources.models import PaperItem


def test_classification_schema_validates_fixture(fixture_dir: Path) -> None:
    response = json.loads(
        (fixture_dir / "deepseek_classification_response.json").read_text(encoding="utf-8")
    )
    content = _extract_message_content(response)
    classification = ClassificationResult.model_validate(_parse_json_object(content))

    assert classification.read_priority == ReadPriority.MUST_READ
    assert classification.job_relevance_score == 5
    assert classification.is_rendering_related


@pytest.mark.asyncio
async def test_deepseek_invalid_json_retries_once(sample_papers: list[PaperItem]) -> None:
    settings = Settings(deepseek_api_key="test-key", dry_run=False)
    client = DeepSeekClient(settings)
    responses = [
        "{invalid-json",
        json.dumps(
            {
                "is_graphics_related": True,
                "is_rendering_related": True,
                "main_category": "rendering",
                "sub_tags": ["ReSTIR"],
                "technical_keywords": ["reservoir"],
                "novelty_score": 4,
                "job_relevance_score": 5,
                "read_priority": "must_read",
                "reason": "Relevant.",
                "uncertainty": "Abstract only.",
            }
        ),
    ]

    async def fake_content(_prompt: str) -> str:
        return responses.pop(0)

    client._chat_completion_content = fake_content  # type: ignore[method-assign]

    result = await client.classify_paper(sample_papers[0])

    assert result.read_priority == ReadPriority.MUST_READ
    assert responses == []


def test_classification_schema_rejects_invalid_priority() -> None:
    with pytest.raises(ValueError):
        ClassificationResult.model_validate(
            {
                "is_graphics_related": True,
                "is_rendering_related": True,
                "main_category": "rendering",
                "sub_tags": [],
                "technical_keywords": [],
                "novelty_score": 3,
                "job_relevance_score": 3,
                "read_priority": "urgent",
                "reason": "Invalid.",
                "uncertainty": "Invalid.",
            }
        )
