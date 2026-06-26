from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PaperItem(BaseModel):
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    published_at: datetime
    updated_at: datetime | None = None
    abs_url: str
    pdf_url: str | None = None
    title_hash: str
    raw: dict[str, Any] | None = None


class SourceFetchResult(BaseModel):
    source_name: str = "arxiv"
    items: list[PaperItem] = Field(default_factory=list)
