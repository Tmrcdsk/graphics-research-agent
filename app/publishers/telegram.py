from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import Settings
from app.llm.schemas import ClassificationResult, ReadPriority, SummaryResult
from app.sources.models import PaperItem
from app.utils.markdown_escape import escape_html

logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_LIMIT = 4096
SAFE_CHUNK_LIMIT = 3900


class TelegramConfigurationError(RuntimeError):
    """Raised when Telegram publishing is requested without credentials."""


class TelegramPublishError(RuntimeError):
    """Raised when Telegram API returns a failed response."""


@dataclass(frozen=True)
class TelegramSendResult:
    status: str
    external_message_id: str | None = None
    error: str | None = None


def format_priority(priority: ReadPriority) -> str:
    return {
        ReadPriority.MUST_READ: "Must Read",
        ReadPriority.READ_LATER: "Read Later",
        ReadPriority.ARCHIVE_ONLY: "Archive Only",
        ReadPriority.SKIP: "Skip",
    }[priority]


def render_telegram_message(
    paper: PaperItem,
    classification: ClassificationResult,
    summary: SummaryResult,
) -> str:
    tags = ", ".join(classification.sub_tags) if classification.sub_tags else "None"
    lines = [
        "<b>Graphics Research</b>",
        "",
        f"<b>[{format_priority(summary.read_priority)}] {escape_html(summary.title_zh)}</b>",
        "",
        f"来源：{escape_html(paper.source_name)}",
        "",
        f"一句话：{escape_html(summary.one_sentence)}",
        "",
        f"问题：{escape_html(summary.problem)}",
        "",
        f"方法：{escape_html(summary.method)}",
        "",
        f"为什么推给你：{escape_html(summary.relation_to_user_goal)}",
        "",
        "可能价值：",
        escape_html(summary.likely_usefulness),
        "",
        f"不确定点：{escape_html(summary.uncertainty)}",
        "",
        f"标签：{escape_html(tags)}",
        "",
        "相关度：",
        f"岗位相关度：{summary.job_relevance_score}/5",
        f"新颖度：{summary.novelty_score}/5",
        "",
        f"链接：{escape_html(paper.item_url)}",
    ]
    if paper.pdf_url:
        lines.append(f"PDF: {escape_html(paper.pdf_url)}")
    return "\n".join(lines)


def split_message(message: str, limit: int = SAFE_CHUNK_LIMIT) -> list[str]:
    if len(message) <= limit:
        return [message]

    chunks: list[str] = []
    current = ""
    for paragraph in message.split("\n\n"):
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= limit:
            current = paragraph
        else:
            chunks.extend(
                paragraph[index : index + limit] for index in range(0, len(paragraph), limit)
            )
            current = ""
    if current:
        chunks.append(current)
    return chunks


class TelegramPublisher:
    channel = "telegram"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_message(self, message: str) -> TelegramSendResult:
        if self._settings.dry_run:
            logger.info("DRY_RUN Telegram message:\n%s", message)
            return TelegramSendResult(status="dry_run")

        if not self._settings.telegram_configured:
            raise TelegramConfigurationError(
                "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required when DRY_RUN=false"
            )

        message_ids: list[str] = []
        for chunk in split_message(message, limit=SAFE_CHUNK_LIMIT):
            message_id = await self._send_chunk(chunk)
            if message_id:
                message_ids.append(message_id)
        return TelegramSendResult(
            status="success",
            external_message_id=",".join(message_ids) or None,
        )

    async def _send_chunk(self, chunk: str) -> str | None:
        assert self._settings.telegram_bot_token is not None
        assert self._settings.telegram_chat_id is not None

        url = f"https://api.telegram.org/bot{self._settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self._settings.telegram_chat_id,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }

        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            stop=stop_after_attempt(self._settings.http_retry_attempts),
            reraise=True,
        ):
            with attempt:
                async with httpx.AsyncClient(timeout=self._settings.http_timeout_seconds) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    if not isinstance(data, dict) or data.get("ok") is not True:
                        raise TelegramPublishError("Telegram API returned ok=false")
                    result = data.get("result")
                    if isinstance(result, dict) and "message_id" in result:
                        return str(result["message_id"])
                    return None

        raise TelegramPublishError("Telegram sendMessage did not return")
