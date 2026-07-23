from __future__ import annotations

import pytest

from app.config import Settings
from app.sources.source_factory import MultiSource, build_default_source, build_sources


def test_build_sources_from_enabled_sources() -> None:
    settings = Settings(
        enabled_sources_raw=(
            "arxiv,unreal,nvidia,gpuopen,directx,vulkan,siggraph_realtime,"
            "siggraph_research,gdc,gdc_vault,advances"
        ),
        dry_run=True,
    )

    sources = build_sources(settings)

    assert [source.source_name for source in sources] == [
        "arxiv",
        "unreal",
        "nvidia",
        "gpuopen",
        "directx",
        "vulkan",
        "siggraph_realtime",
        "siggraph_research",
        "gdc",
        "gdc_vault",
        "advances",
    ]


def test_build_default_source_returns_multi_source_for_multiple_sources() -> None:
    settings = Settings(enabled_sources_raw="unreal,nvidia", dry_run=True)

    source = build_default_source(settings)

    assert isinstance(source, MultiSource)
    assert source.source_name == "unreal,nvidia"


def test_build_sources_deduplicates_source_aliases() -> None:
    settings = Settings(
        enabled_sources_raw="epic,unreal,advances,advances_rtr",
        dry_run=True,
    )

    sources = build_sources(settings)

    assert [source.source_name for source in sources] == ["unreal", "advances"]


def test_build_sources_rejects_unknown_source_name() -> None:
    settings = Settings(enabled_sources_raw="arxiv,gpuopne", dry_run=True)

    with pytest.raises(ValueError, match="gpuopne"):
        build_sources(settings)


class _StubSource:
    def __init__(self, source_name: str, *, fail: bool = False) -> None:
        self.source_name = source_name
        self._fail = fail

    async def fetch_recent(self) -> list[object]:
        if self._fail:
            raise RuntimeError(f"{self.source_name} unavailable")
        return []


@pytest.mark.asyncio
async def test_multi_source_allows_successful_empty_source_when_another_fails() -> None:
    source = MultiSource([_StubSource("failed", fail=True), _StubSource("empty")])

    assert await source.fetch_recent() == []


@pytest.mark.asyncio
async def test_multi_source_raises_when_every_source_fails() -> None:
    source = MultiSource([_StubSource("first", fail=True), _StubSource("second", fail=True)])

    with pytest.raises(RuntimeError, match="first, second"):
        await source.fetch_recent()
