from __future__ import annotations

import logging

from app.config import Settings
from app.sources.arxiv_source import ArxivSource
from app.sources.feed_source import FeedSourceConfig, NewsFeedSource
from app.sources.models import PaperItem

logger = logging.getLogger(__name__)


class MultiSource:
    source_name = "multi"

    def __init__(self, sources: list[object]) -> None:
        self._sources = sources
        self.source_name = ",".join(getattr(source, "source_name", "unknown") for source in sources)

    async def fetch_recent(self) -> list[PaperItem]:
        items: list[PaperItem] = []
        failures: list[str] = []
        for source in self._sources:
            source_name = getattr(source, "source_name", "unknown")
            try:
                fetched = await source.fetch_recent()
            except Exception as exc:  # noqa: BLE001 - isolate feed failures across sources.
                logger.warning("Source failed source=%s error=%s", source_name, exc)
                failures.append(source_name)
                continue
            items.extend(fetched)

        if not items and failures:
            raise RuntimeError(f"All configured sources failed: {', '.join(failures)}")
        return items


def build_sources(settings: Settings) -> list[object]:
    sources: list[object] = []
    enabled = set(settings.enabled_sources)
    if "arxiv" in enabled:
        sources.append(ArxivSource(settings))
    if "unreal" in enabled or "epic" in enabled:
        sources.append(
            NewsFeedSource(
                settings,
                FeedSourceConfig(
                    source_name="unreal",
                    source_label="Unreal Engine",
                    feed_url=settings.unreal_feed_url,
                    default_author="Epic Games",
                ),
            )
        )
    if "nvidia" in enabled:
        sources.append(
            NewsFeedSource(
                settings,
                FeedSourceConfig(
                    source_name="nvidia",
                    source_label="NVIDIA Developer Blog",
                    feed_url=settings.nvidia_feed_url,
                    default_author="NVIDIA",
                ),
            )
        )
    return sources


def build_default_source(settings: Settings) -> object:
    sources = build_sources(settings)
    if not sources:
        raise ValueError("No sources enabled. Set ENABLED_SOURCES to include at least one source.")
    if len(sources) == 1:
        return sources[0]
    return MultiSource(sources)
