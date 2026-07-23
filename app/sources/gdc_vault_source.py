from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.config import Settings
from app.sources.arxiv_source import normalize_whitespace
from app.sources.http_client import build_http_client, fetch_text
from app.sources.models import PaperItem
from app.utils.hashing import normalize_for_hashing, stable_title_hash

logger = logging.getLogger(__name__)

_PLAY_PATH = re.compile(r"^/play/(?P<session_id>\d+)(?:/|$)")
_MEDIA_PRIORITY = {"slides": 4, "presentation": 3, "video": 2, "audio": 1}
_RENDERING_CATALOG_TERMS = (
    "render",
    "graphics",
    "shader",
    "lighting",
    "illumination",
    "ray tracing",
    "path tracing",
    "radiance",
    "texture",
    "material",
    "gpu",
    "visual effects",
    "vfx",
    "volumetric",
    "shadow",
    "geometry",
    "mesh",
    "anti-alias",
    "upscal",
    "frame generation",
    "60 fps",
    "tessellation",
    "occlusion",
    "unreal engine",
    "ue5",
    "directx",
    "vulkan",
    "weather system",
)


@dataclass(frozen=True)
class GdcVaultCatalogEntry:
    session_id: int
    title: str
    authors: list[str]
    company: str | None
    track: str | None
    conference: str
    media_type: str
    url: str
    catalog_url: str
    year: int


def _split_names(value: str) -> list[str]:
    names = [
        normalize_whitespace(part)
        for part in re.split(r"\s*(?:,|;|\band\b)\s*", value)
        if normalize_whitespace(part)
    ]
    return list(dict.fromkeys(names))


def _media_type(session_link: object) -> str:
    image = session_link.select_one(".media_type_image")  # type: ignore[attr-defined]
    if image is None:
        return "session"
    classes = [str(value).casefold() for value in image.get("class", [])]
    return next((value for value in classes if value != "media_type_image"), "session")


def parse_gdc_vault_catalog(
    html_text: str,
    *,
    catalog_url: str,
    year: int,
) -> list[GdcVaultCatalogEntry]:
    soup = BeautifulSoup(html_text, "html.parser")
    entries_by_title: dict[str, GdcVaultCatalogEntry] = {}

    for link in soup.select("a.session_item[href]"):
        href = str(link.get("href", "")).strip()
        absolute_url = urljoin(catalog_url, href)
        parsed_url = urlparse(absolute_url)
        match = _PLAY_PATH.match(parsed_url.path)
        if parsed_url.hostname not in {"gdcvault.com", "www.gdcvault.com"} or match is None:
            continue

        info = link.select_one(".conference_info")
        if info is None:
            continue
        title_element = info.find("strong")
        title = (
            normalize_whitespace(title_element.get_text(" ", strip=True))
            if title_element is not None
            else ""
        )
        if not title:
            continue

        conference_element = info.select_one(".conference_name")
        conference = (
            normalize_whitespace(conference_element.get_text(" ", strip=True))
            if conference_element is not None
            else f"Game Developers Conference {year}"
        )
        track_element = info.select_one(".track_name")
        track = (
            normalize_whitespace(track_element.get_text(" ", strip=True))
            if track_element is not None
            else None
        )

        by_line = None
        for span in info.find_all("span"):
            emphasis = span.find("em")
            if emphasis is not None and emphasis.get_text(" ", strip=True).casefold() == "by":
                by_line = span
                break
        company: str | None = None
        authors: list[str] = []
        if by_line is not None:
            company_element = by_line.find("strong")
            if company_element is not None:
                company = normalize_whitespace(company_element.get_text(" ", strip=True)).strip(
                    "()"
                )
            by_text = normalize_whitespace(by_line.get_text(" ", strip=True))
            author_text = re.sub(r"^by\s+", "", by_text, flags=re.IGNORECASE)
            if company:
                author_text = re.sub(
                    rf"\s*\({re.escape(company)}\)\s*$",
                    "",
                    author_text,
                    flags=re.IGNORECASE,
                )
            authors = _split_names(author_text)

        entry = GdcVaultCatalogEntry(
            session_id=int(match.group("session_id")),
            title=title,
            authors=authors,
            company=company,
            track=track,
            conference=conference,
            media_type=_media_type(link),
            url=absolute_url,
            catalog_url=catalog_url,
            year=year,
        )
        title_key = normalize_for_hashing(title)
        current = entries_by_title.get(title_key)
        if current is None or _MEDIA_PRIORITY.get(entry.media_type, 0) > _MEDIA_PRIORITY.get(
            current.media_type, 0
        ):
            entries_by_title[title_key] = entry

    return sorted(entries_by_title.values(), key=lambda entry: entry.session_id, reverse=True)


def is_rendering_catalog_entry(entry: GdcVaultCatalogEntry) -> bool:
    title = entry.title.casefold()
    return any(term in title for term in _RENDERING_CATALOG_TERMS)


def _detail_values(html_text: str | None) -> dict[str, str]:
    if not html_text:
        return {}
    soup = BeautifulSoup(html_text, "html.parser")
    values: dict[str, str] = {}

    for field, property_name in (("title", "og:title"), ("description", "og:description")):
        element = soup.find("meta", attrs={"property": property_name})
        if element is not None and element.get("content"):
            values[field] = normalize_whitespace(str(element["content"]))

    overview = soup.select_one("dl.overview-section dd")
    if overview is not None:
        values["overview"] = normalize_whitespace(overview.get_text(" ", strip=True))

    player_info = soup.select_one("dl.player-info")
    if player_info is not None:
        for label in player_info.find_all("dt"):
            value = label.find_next_sibling("dd")
            if value is None:
                continue
            key = normalize_whitespace(label.get_text(" ", strip=True)).rstrip(":").casefold()
            values[key] = normalize_whitespace(value.get_text(" ", strip=True))
    return values


def build_gdc_vault_paper(
    entry: GdcVaultCatalogEntry,
    detail_html: str | None,
) -> PaperItem:
    details = _detail_values(detail_html)
    title = details.get("session name") or details.get("title") or entry.title
    authors = _split_names(details.get("speaker(s)", "")) or entry.authors or ["GDC"]
    abstract = (
        details.get("overview")
        or details.get("description")
        or f"GDC Vault session: {title}. Track: {entry.track or 'unspecified'}."
    )
    categories = [
        value
        for value in (
            "GDC Vault",
            entry.conference,
            details.get("track / format") or entry.track,
            entry.media_type,
        )
        if value
    ]

    return PaperItem(
        source_name="gdc_vault",
        source_id=str(entry.session_id),
        arxiv_id=f"gdc_vault:{entry.session_id}",
        title=title,
        authors=authors,
        abstract=abstract,
        categories=list(dict.fromkeys(categories)),
        published_at=datetime(entry.year, 1, 1, tzinfo=UTC),
        updated_at=None,
        abs_url=entry.url,
        pdf_url=None,
        title_hash=stable_title_hash(title),
        raw={
            "catalog_url": entry.catalog_url,
            "conference_year": entry.year,
            "date_precision": "year",
            "company": details.get("company name(s)") or entry.company,
            "media_type": entry.media_type,
        },
    )


class GdcVaultSource:
    source_name = "gdc_vault"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def fetch_recent(self) -> list[PaperItem]:
        logger.info("Fetching GDC Vault catalogs years=%s", self._settings.gdc_vault_years)
        entries: list[GdcVaultCatalogEntry] = []
        successful_catalogs = 0

        async with build_http_client(self._settings) as client:
            for year in self._settings.gdc_vault_years:
                catalog_url = f"{self._settings.gdc_vault_base_url}/browse/gdc-{year % 100:02d}"
                try:
                    html_text = await fetch_text(
                        client,
                        self._settings,
                        catalog_url,
                        allow_not_found=True,
                    )
                except Exception as exc:  # noqa: BLE001 - isolate annual catalog failures.
                    logger.warning("GDC Vault catalog failed year=%s error=%s", year, exc)
                    continue
                if html_text is None:
                    logger.info("GDC Vault catalog not published year=%s", year)
                    continue
                successful_catalogs += 1
                entries.extend(
                    parse_gdc_vault_catalog(html_text, catalog_url=catalog_url, year=year)
                )

            if successful_catalogs == 0:
                raise RuntimeError("No configured GDC Vault annual catalog was available")

            entries_by_title: dict[str, GdcVaultCatalogEntry] = {}
            for entry in entries:
                key = normalize_for_hashing(entry.title)
                current = entries_by_title.get(key)
                if current is None or (entry.year, _MEDIA_PRIORITY.get(entry.media_type, 0)) > (
                    current.year,
                    _MEDIA_PRIORITY.get(current.media_type, 0),
                ):
                    entries_by_title[key] = entry

            candidates = sorted(
                (entry for entry in entries_by_title.values() if is_rendering_catalog_entry(entry)),
                key=lambda entry: (entry.year, entry.session_id),
                reverse=True,
            )[: self._settings.max_feed_results]
            semaphore = asyncio.Semaphore(4)

            async def enrich(entry: GdcVaultCatalogEntry) -> PaperItem:
                detail_html: str | None = None
                async with semaphore:
                    try:
                        detail_html = await fetch_text(client, self._settings, entry.url)
                    except Exception as exc:  # noqa: BLE001 - catalog metadata is a valid fallback.
                        logger.warning(
                            "GDC Vault detail failed session_id=%s error=%s",
                            entry.session_id,
                            exc,
                        )
                return build_gdc_vault_paper(entry, detail_html)

            items = list(await asyncio.gather(*(enrich(entry) for entry in candidates)))

        logger.info(
            "Fetched GDC Vault catalog entries=%s rendering_candidates=%s",
            len(entries_by_title),
            len(items),
        )
        return items
