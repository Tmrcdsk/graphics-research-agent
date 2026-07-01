from __future__ import annotations

from app.config import Settings
from app.sources.source_factory import MultiSource, build_default_source, build_sources


def test_build_sources_from_enabled_sources() -> None:
    settings = Settings(enabled_sources_raw="arxiv,unreal,nvidia", dry_run=True)

    sources = build_sources(settings)

    assert [source.source_name for source in sources] == ["arxiv", "unreal", "nvidia"]


def test_build_default_source_returns_multi_source_for_multiple_sources() -> None:
    settings = Settings(enabled_sources_raw="unreal,nvidia", dry_run=True)

    source = build_default_source(settings)

    assert isinstance(source, MultiSource)
    assert source.source_name == "unreal,nvidia"
