from __future__ import annotations

import logging
import re
from calendar import timegm
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

import feedparser
import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import Settings
from app.sources.models import PaperItem
from app.utils.hashing import stable_title_hash

logger = logging.getLogger(__name__)

ARXIV_API_URL = "https://export.arxiv.org/api/query"


class ArxivParseError(ValueError):
    """Raised when arXiv XML cannot be parsed into paper items."""


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_arxiv_id(abs_url_or_id: str) -> str:
    raw = abs_url_or_id.rstrip("/").split("/")[-1]
    return re.sub(r"v\d+$", "", raw)


def _struct_time_to_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(timegm(value), tz=UTC)


def _entry_get(entry: Any, key: str, default: Any = None) -> Any:
    if hasattr(entry, "get"):
        return entry.get(key, default)
    return getattr(entry, key, default)


def _extract_authors(entry: Any) -> list[str]:
    authors = _entry_get(entry, "authors", []) or []
    result: list[str] = []
    for author in authors:
        name = author.get("name") if isinstance(author, dict) else getattr(author, "name", None)
        if name:
            result.append(normalize_whitespace(str(name)))
    return result


def _extract_categories(entry: Any) -> list[str]:
    tags = _entry_get(entry, "tags", []) or []
    categories: list[str] = []
    for tag in tags:
        term = tag.get("term") if isinstance(tag, dict) else getattr(tag, "term", None)
        if term:
            categories.append(str(term))
    return categories


def _extract_pdf_url(entry: Any) -> str | None:
    links = _entry_get(entry, "links", []) or []
    for link in links:
        if not isinstance(link, dict):
            link = dict(link)
        href = link.get("href")
        title = str(link.get("title", "")).lower()
        mime_type = str(link.get("type", "")).lower()
        if href and (title == "pdf" or mime_type == "application/pdf" or "/pdf/" in href):
            return str(href)
    return None


def _extract_primary_category(entry: Any) -> str | None:
    value = _entry_get(entry, "arxiv_primary_category", None)
    if isinstance(value, dict):
        term = value.get("term")
        return str(term) if term else None
    term = getattr(value, "term", None)
    return str(term) if term else None


def parse_arxiv_feed(xml_text: str) -> list[PaperItem]:
    parsed = feedparser.parse(xml_text)
    if parsed.bozo:
        message = getattr(parsed.bozo_exception, "reason", parsed.bozo_exception)
        raise ArxivParseError(f"Malformed arXiv feed: {message}")

    items: list[PaperItem] = []
    for entry in parsed.entries:
        title = normalize_whitespace(str(_entry_get(entry, "title", "")))
        abstract = normalize_whitespace(str(_entry_get(entry, "summary", "")))
        abs_url = str(_entry_get(entry, "id", "")).strip()
        arxiv_id = extract_arxiv_id(abs_url)
        published_at = _struct_time_to_datetime(_entry_get(entry, "published_parsed"))

        if not title or not abstract or not abs_url or not arxiv_id or published_at is None:
            logger.warning("Skipping malformed arXiv entry with missing required fields")
            continue

        items.append(
            PaperItem(
                source_name="arxiv",
                source_id=arxiv_id,
                arxiv_id=arxiv_id,
                title=title,
                authors=_extract_authors(entry),
                abstract=abstract,
                categories=_extract_categories(entry),
                published_at=published_at,
                updated_at=_struct_time_to_datetime(_entry_get(entry, "updated_parsed")),
                abs_url=abs_url,
                pdf_url=_extract_pdf_url(entry),
                title_hash=stable_title_hash(title),
                raw={
                    "id": abs_url,
                    "primary_category": _extract_primary_category(entry),
                },
            )
        )
    return items


class ArxivSource:
    source_name = "arxiv"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_query_url(self) -> str:
        query = " OR ".join(f"cat:{category}" for category in self._settings.arxiv_categories)
        params = {
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": str(self._settings.max_arxiv_results),
        }
        return f"{ARXIV_API_URL}?{urlencode(params)}"

    async def fetch_recent(self) -> list[PaperItem]:
        url = self.build_query_url()
        logger.info(
            "Fetching arXiv feed for categories=%s",
            ",".join(self._settings.arxiv_categories),
        )
        xml_text = await self._fetch_text(url)
        items = parse_arxiv_feed(xml_text)
        logger.info("Fetched %s arXiv items", len(items))
        return items

    async def _fetch_text(self, url: str) -> str:
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            stop=stop_after_attempt(self._settings.http_retry_attempts),
            reraise=True,
        ):
            with attempt:
                timeout = httpx.Timeout(self._settings.http_timeout_seconds)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(
                        url,
                        headers={"User-Agent": "graphics-research-agent/0.1"},
                    )
                    response.raise_for_status()
                    return response.text
        raise RuntimeError("arXiv fetch did not return")
