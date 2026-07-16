from __future__ import annotations

import hashlib
import html
import logging
import re
from calendar import timegm
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import feedparser
import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import Settings
from app.sources.arxiv_source import normalize_whitespace
from app.sources.models import PaperItem
from app.utils.hashing import stable_title_hash
from app.utils.time import utc_now

logger = logging.getLogger(__name__)


class FeedParseError(ValueError):
    """Raised when an RSS/Atom feed cannot be parsed."""


@dataclass(frozen=True)
class FeedSourceConfig:
    source_name: str
    source_label: str
    feed_url: str
    default_author: str
    required_any_terms: tuple[str, ...] = ()


def strip_html(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return normalize_whitespace(html.unescape(without_tags))


def _entry_get(entry: Any, key: str, default: Any = None) -> Any:
    if hasattr(entry, "get"):
        return entry.get(key, default)
    return getattr(entry, key, default)


def _struct_time_to_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(timegm(value), tz=UTC)


def _extract_link(entry: Any) -> str:
    link = str(_entry_get(entry, "link", "")).strip()
    if link:
        return link
    links = _entry_get(entry, "links", []) or []
    for candidate in links:
        href = (
            candidate.get("href")
            if isinstance(candidate, dict)
            else getattr(candidate, "href", None)
        )
        if href:
            return str(href)
    return str(_entry_get(entry, "id", "")).strip()


def _extract_authors(entry: Any, default_author: str) -> list[str]:
    authors = _entry_get(entry, "authors", []) or []
    result: list[str] = []
    for author in authors:
        name = author.get("name") if isinstance(author, dict) else getattr(author, "name", None)
        if name:
            result.append(normalize_whitespace(str(name)))
    if result:
        return result
    author = str(_entry_get(entry, "author", "")).strip()
    return [normalize_whitespace(author)] if author else [default_author]


def _extract_categories(entry: Any, source_label: str) -> list[str]:
    categories = [source_label]
    for tag in _entry_get(entry, "tags", []) or []:
        term = tag.get("term") if isinstance(tag, dict) else getattr(tag, "term", None)
        if term:
            categories.append(normalize_whitespace(str(term)))
    return list(dict.fromkeys(categories))


def _stable_source_item_id(source_name: str, raw_id: str, title: str, link: str) -> str:
    seed = raw_id or link or title
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
    return f"{source_name}:{digest}"


def _matches_required_terms(item: PaperItem, required_terms: tuple[str, ...]) -> bool:
    if not required_terms:
        return True
    text = f"{item.title}\n{item.abstract}".casefold()
    return any(
        re.search(
            rf"(?<![a-z0-9]){re.escape(term.casefold())}(?![a-z0-9])",
            text,
        )
        for term in required_terms
    )


def parse_news_feed(xml_text: str, config: FeedSourceConfig) -> list[PaperItem]:
    parsed = feedparser.parse(xml_text)
    if parsed.bozo and not parsed.entries:
        message = getattr(parsed.bozo_exception, "reason", parsed.bozo_exception)
        raise FeedParseError(f"Malformed {config.source_name} feed: {message}")

    items: list[PaperItem] = []
    for entry in parsed.entries:
        title = strip_html(str(_entry_get(entry, "title", "")))
        link = _extract_link(entry)
        raw_summary = str(_entry_get(entry, "summary", "") or _entry_get(entry, "description", ""))
        summary = strip_html(raw_summary)
        published_at = (
            _struct_time_to_datetime(_entry_get(entry, "published_parsed"))
            or _struct_time_to_datetime(_entry_get(entry, "updated_parsed"))
            or utc_now()
        )
        raw_id = str(_entry_get(entry, "id", "") or _entry_get(entry, "guid", "")).strip()
        source_id = raw_id or link

        if not title or not link or not summary:
            logger.warning("Skipping malformed %s feed entry", config.source_name)
            continue

        synthetic_id = _stable_source_item_id(config.source_name, source_id, title, link)
        items.append(
            PaperItem(
                source_name=config.source_name,
                source_id=source_id,
                arxiv_id=synthetic_id,
                title=title,
                authors=_extract_authors(entry, config.default_author),
                abstract=summary,
                categories=_extract_categories(entry, config.source_label),
                published_at=published_at,
                updated_at=_struct_time_to_datetime(_entry_get(entry, "updated_parsed")),
                abs_url=link,
                pdf_url=None,
                title_hash=stable_title_hash(title),
                raw={
                    "feed_url": config.feed_url,
                    "source_label": config.source_label,
                    "id": raw_id or None,
                },
            )
        )
    return items


class NewsFeedSource:
    def __init__(self, settings: Settings, config: FeedSourceConfig) -> None:
        self._settings = settings
        self._config = config
        self.source_name = config.source_name

    async def fetch_recent(self) -> list[PaperItem]:
        logger.info(
            "Fetching %s feed url=%s",
            self._config.source_name,
            self._config.feed_url,
        )
        xml_text = await self._fetch_text(self._config.feed_url)
        parsed_items = parse_news_feed(xml_text, self._config)
        items = [
            item
            for item in parsed_items
            if _matches_required_terms(item, self._config.required_any_terms)
        ]
        logger.info(
            "Fetched %s %s feed items; selected=%s after source constraints",
            len(parsed_items),
            self._config.source_name,
            len(items),
        )
        return items[: self._settings.max_feed_results]

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
        raise RuntimeError(f"{self._config.source_name} feed fetch did not return")
