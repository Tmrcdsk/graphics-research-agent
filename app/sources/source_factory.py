from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from app.config import Settings
from app.sources.advances_source import AdvancesSource
from app.sources.arxiv_source import ArxivSource
from app.sources.feed_source import FeedSourceConfig, NewsFeedSource
from app.sources.gdc_vault_source import GdcVaultSource
from app.sources.models import PaperItem

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OfficialFeedSpec:
    source_name: str
    source_label: str
    settings_url_field: str
    default_author: str
    aliases: tuple[str, ...] = ()
    required_any_terms: tuple[str, ...] = ()


OFFICIAL_FEED_SPECS = (
    OfficialFeedSpec(
        source_name="unreal",
        source_label="Unreal Engine",
        settings_url_field="unreal_feed_url",
        default_author="Epic Games",
        aliases=("epic",),
    ),
    OfficialFeedSpec(
        source_name="nvidia",
        source_label="NVIDIA Developer Blog",
        settings_url_field="nvidia_feed_url",
        default_author="NVIDIA",
    ),
    OfficialFeedSpec(
        source_name="gpuopen",
        source_label="AMD GPUOpen",
        settings_url_field="gpuopen_feed_url",
        default_author="AMD",
    ),
    OfficialFeedSpec(
        source_name="directx",
        source_label="DirectX Developer Blog",
        settings_url_field="directx_feed_url",
        default_author="Microsoft",
    ),
    OfficialFeedSpec(
        source_name="vulkan",
        source_label="Khronos Vulkan News",
        settings_url_field="vulkan_feed_url",
        default_author="Khronos Group",
    ),
    OfficialFeedSpec(
        source_name="siggraph_realtime",
        source_label="ACM SIGGRAPH Real-Time",
        settings_url_field="siggraph_realtime_feed_url",
        default_author="ACM SIGGRAPH",
    ),
    OfficialFeedSpec(
        source_name="siggraph_research",
        source_label="ACM SIGGRAPH Research",
        settings_url_field="siggraph_research_feed_url",
        default_author="ACM SIGGRAPH",
    ),
    OfficialFeedSpec(
        source_name="gdc",
        source_label="GDC via Game Developer",
        settings_url_field="gdc_feed_url",
        default_author="Game Developer",
        required_any_terms=("gdc", "game developers conference"),
    ),
)


class Source(Protocol):
    source_name: str

    async def fetch_recent(self) -> list[PaperItem]: ...


class MultiSource:
    source_name = "multi"

    def __init__(self, sources: list[Source]) -> None:
        self._sources = sources
        self.source_name = ",".join(getattr(source, "source_name", "unknown") for source in sources)

    async def fetch_recent(self) -> list[PaperItem]:
        items: list[PaperItem] = []
        failures: list[str] = []
        successful_sources = 0
        for source in self._sources:
            source_name = getattr(source, "source_name", "unknown")
            try:
                fetched = await source.fetch_recent()
            except Exception as exc:  # noqa: BLE001 - isolate feed failures across sources.
                logger.warning("Source failed source=%s error=%s", source_name, exc)
                failures.append(source_name)
                continue
            successful_sources += 1
            items.extend(fetched)

        if successful_sources == 0 and failures:
            raise RuntimeError(f"All configured sources failed: {', '.join(failures)}")
        return items


def build_sources(settings: Settings) -> list[Source]:
    sources: list[Source] = []
    enabled = set(settings.enabled_sources)
    known_names = {"arxiv", "gdc_vault", "advances", "advances_rtr"}
    for spec in OFFICIAL_FEED_SPECS:
        known_names.add(spec.source_name)
        known_names.update(spec.aliases)

    unknown = sorted(enabled - known_names)
    if unknown:
        raise ValueError(f"Unknown ENABLED_SOURCES values: {', '.join(unknown)}")

    if "arxiv" in enabled:
        sources.append(ArxivSource(settings))
    for spec in OFFICIAL_FEED_SPECS:
        names = {spec.source_name, *spec.aliases}
        if not enabled.intersection(names):
            continue
        sources.append(
            NewsFeedSource(
                settings,
                FeedSourceConfig(
                    source_name=spec.source_name,
                    source_label=spec.source_label,
                    feed_url=getattr(settings, spec.settings_url_field),
                    default_author=spec.default_author,
                    required_any_terms=spec.required_any_terms,
                ),
            )
        )
    if "gdc_vault" in enabled:
        sources.append(GdcVaultSource(settings))
    if enabled.intersection({"advances", "advances_rtr"}):
        sources.append(AdvancesSource(settings))
    return sources


def build_default_source(settings: Settings) -> Source:
    sources = build_sources(settings)
    if not sources:
        raise ValueError("No sources enabled. Set ENABLED_SOURCES to include at least one source.")
    if len(sources) == 1:
        return sources[0]
    return MultiSource(sources)
