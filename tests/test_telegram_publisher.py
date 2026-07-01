from __future__ import annotations

import pytest

from app.config import Settings
from app.llm.schemas import ClassificationResult, ReadPriority, SummaryResult
from app.publishers.telegram import TelegramPublisher, render_telegram_message, split_message
from app.sources.models import PaperItem


def _classification() -> ClassificationResult:
    return ClassificationResult(
        is_graphics_related=True,
        is_rendering_related=True,
        main_category="rendering",
        sub_tags=["shader", "path tracing"],
        technical_keywords=["shader"],
        novelty_score=4,
        job_relevance_score=5,
        read_priority=ReadPriority.MUST_READ,
        reason="Relevant.",
        uncertainty="Abstract only.",
    )


def _summary() -> SummaryResult:
    return SummaryResult(
        title_zh="测试 <shader> 论文",
        one_sentence="一句话摘要。",
        problem="问题。",
        method="方法。",
        relation_to_user_goal="和 Vulkan / UE 渲染学习相关。",
        likely_usefulness="可用于学习。",
        uncertainty="仅基于摘要。",
        read_priority=ReadPriority.MUST_READ,
        job_relevance_score=5,
        novelty_score=4,
    )


def test_render_telegram_message_escapes_html(sample_papers: list[PaperItem]) -> None:
    message = render_telegram_message(sample_papers[0], _classification(), _summary())

    assert "测试 &lt;shader&gt; 论文" in message
    assert "<shader>" not in message
    assert "岗位相关度：5/5" in message
    assert "来源：arxiv" in message
    assert "链接：http://arxiv.org/abs/2606.00001v1" in message


def test_split_message_keeps_chunks_under_limit() -> None:
    chunks = split_message("a" * 8200, limit=3900)

    assert len(chunks) == 3
    assert all(len(chunk) <= 3900 for chunk in chunks)


@pytest.mark.asyncio
async def test_telegram_dry_run_does_not_send() -> None:
    publisher = TelegramPublisher(Settings(dry_run=True))

    result = await publisher.send_message("dry-run message")

    assert result.status == "dry_run"
    assert result.external_message_id is None
