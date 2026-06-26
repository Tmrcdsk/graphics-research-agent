from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InsertPaperResult:
    paper_id: int
    is_new: bool


@dataclass(frozen=True)
class PublishLogRecord:
    paper_id: int
    channel: str
    status: str
    external_message_id: str | None
    error: str | None
