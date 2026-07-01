from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PaperItem(BaseModel):
    source_name: str = "arxiv"
    source_id: str | None = None
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

    @property
    def item_id(self) -> str:
        return self.source_id or self.arxiv_id

    @property
    def item_url(self) -> str:
        return self.abs_url


class SourceFetchResult(BaseModel):
    source_name: str = "arxiv"
    items: list[PaperItem] = Field(default_factory=list)
