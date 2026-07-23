from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.config import Settings
from app.sources.arxiv_source import normalize_whitespace
from app.sources.http_client import build_http_client, fetch_text
from app.sources.models import PaperItem
from app.utils.hashing import stable_title_hash

logger = logging.getLogger(__name__)

_MATERIAL_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".zip"}
_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"


def _course_date(soup: BeautifulSoup, year: int) -> datetime:
    text = soup.get_text(" ", strip=True)
    match = re.search(rf"\b(\d{{1,2}})\s+({_MONTHS})\s+({year})\b", text, re.IGNORECASE)
    if match is None:
        return datetime(year, 8, 1, tzinfo=UTC)
    parsed = datetime.strptime(" ".join(match.groups()), "%d %B %Y")
    return parsed.replace(tzinfo=UTC)


def _talk_authors(anchor: object, title: str) -> list[str]:
    parent = anchor.find_parent(["p", "div", "td", "li"])  # type: ignore[attr-defined]
    if parent is None:
        return ["Advances course speaker"]
    text = parent.get_text("\n", strip=True)
    title_position = text.find(title)
    remainder = text[title_position + len(title) :] if title_position >= 0 else text
    authors: list[str] = []
    for line in remainder.splitlines():
        matches = re.findall(r"([^()]+?)\s*\([^()]+\)", line)
        for match in matches:
            name = normalize_whitespace(match).strip(" ,;&")
            if name:
                authors.append(name)
    return list(dict.fromkeys(authors)) or ["Advances course speaker"]


def _talk_details(target: object, page_url: str) -> tuple[str | None, list[str]]:
    abstract: str | None = None
    materials: list[str] = []

    for element in target.find_all_next():  # type: ignore[attr-defined]
        if element is not target and element.name == "a" and element.get("name"):
            break
        if element.name in {"p", "div", "td", "li"} and abstract is None:
            text = normalize_whitespace(element.get_text(" ", strip=True))
            match = re.match(r"^abstract\s*:?\s*(.+)$", text, re.IGNORECASE)
            if match:
                abstract = match.group(1)
        if element.name == "a" and element.get("href"):
            material_url = urljoin(page_url, str(element["href"]).strip())
            suffix = PurePosixPath(urlparse(material_url).path).suffix.casefold()
            if suffix in _MATERIAL_EXTENSIONS and material_url not in materials:
                materials.append(material_url)
    return abstract, materials


def parse_advances_course(
    html_text: str,
    *,
    page_url: str,
    year: int,
) -> list[PaperItem]:
    soup = BeautifulSoup(html_text, "html.parser")
    published_at = _course_date(soup, year)
    items: list[PaperItem] = []
    seen_anchors: set[str] = set()

    for anchor in soup.select('a[href^="#"]'):
        anchor_id = str(anchor.get("href", "")).removeprefix("#").strip()
        if not anchor_id or anchor_id in seen_anchors:
            continue
        target = soup.find("a", attrs={"name": anchor_id})
        if target is None:
            continue

        title = normalize_whitespace(anchor.get_text(" ", strip=True))
        if not title:
            continue
        abstract, materials = _talk_details(target, page_url)
        if abstract is None and not materials:
            continue
        seen_anchors.add(anchor_id)
        abstract_text = abstract or f"Technical talk from the {year} course."
        item_url = f"{page_url}#{anchor_id}"
        pdf_url = next(
            (
                material
                for material in materials
                if PurePosixPath(urlparse(material).path).suffix.casefold() == ".pdf"
            ),
            None,
        )
        items.append(
            PaperItem(
                source_name="advances",
                source_id=f"{year}:{anchor_id}",
                arxiv_id=f"advances:{year}:{anchor_id}",
                title=title,
                authors=_talk_authors(anchor, title),
                abstract=abstract_text,
                categories=[
                    "Advances in Real-Time Rendering in Games",
                    f"SIGGRAPH {year}",
                ],
                published_at=published_at,
                updated_at=None,
                abs_url=item_url,
                pdf_url=pdf_url,
                title_hash=stable_title_hash(title),
                raw={
                    "course_page_url": page_url,
                    "conference_year": year,
                    "materials": materials,
                },
            )
        )
    return items


class AdvancesSource:
    source_name = "advances"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def fetch_recent(self) -> list[PaperItem]:
        logger.info(
            "Fetching Advances in Real-Time Rendering course pages years=%s",
            self._settings.advances_years,
        )
        items: list[PaperItem] = []
        successful_pages = 0

        async with build_http_client(self._settings) as client:
            for year in self._settings.advances_years:
                page_url = f"{self._settings.advances_base_url}/s{year}/index.html"
                try:
                    html_text = await fetch_text(
                        client,
                        self._settings,
                        page_url,
                        allow_not_found=True,
                    )
                except Exception as exc:  # noqa: BLE001 - isolate annual page failures.
                    logger.warning("Advances course page failed year=%s error=%s", year, exc)
                    continue
                if html_text is None:
                    logger.info("Advances course page not published year=%s", year)
                    continue
                successful_pages += 1
                items.extend(parse_advances_course(html_text, page_url=page_url, year=year))

        if successful_pages == 0:
            raise RuntimeError("No configured Advances course page was available")

        deduplicated: list[PaperItem] = []
        seen_ids: set[str] = set()
        for item in items:
            if item.item_id in seen_ids:
                continue
            seen_ids.add(item.item_id)
            deduplicated.append(item)

        selected = deduplicated[: self._settings.max_feed_results]
        logger.info(
            "Fetched Advances course talks=%s selected=%s",
            len(deduplicated),
            len(selected),
        )
        return selected
