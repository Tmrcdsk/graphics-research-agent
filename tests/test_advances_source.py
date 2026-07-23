from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from app.config import Settings
from app.pipeline.rule_filter import score_paper
from app.sources.advances_source import AdvancesSource, parse_advances_course


def test_parse_advances_course_extracts_talks_and_materials(fixture_dir: Path) -> None:
    items = parse_advances_course(
        (fixture_dir / "advances_2026.html").read_text(encoding="utf-8"),
        page_url="https://advances.realtimerendering.com/s2026/index.html",
        year=2026,
    )

    assert len(items) == 2
    first = items[0]
    assert first.source_name == "advances"
    assert first.source_id == "2026:orca_ea_seed"
    assert first.title == "Speeding up Path Tracing via ORCA"
    assert first.authors == ["Jon Greenberg"]
    assert "online radiance cache" in first.abstract
    assert first.abs_url.endswith("/s2026/index.html#orca_ea_seed")
    assert first.pdf_url == ("https://advances.realtimerendering.com/s2026/content/orca-slides.pdf")
    assert first.raw is not None
    assert first.raw["materials"] == [
        "https://advances.realtimerendering.com/s2026/content/orca-slides.pdf",
        "https://advances.realtimerendering.com/s2026/content/orca-slides.pptx",
    ]
    assert first.published_at.isoformat() == "2026-07-21T00:00:00+00:00"


def test_advances_course_category_is_a_rendering_filter_signal(fixture_dir: Path) -> None:
    item = parse_advances_course(
        (fixture_dir / "advances_2026.html").read_text(encoding="utf-8"),
        page_url="https://advances.realtimerendering.com/s2026/index.html",
        year=2026,
    )[0].model_copy(
        update={
            "title": "SLIM: Scaling User-Generated Worlds",
            "abstract": "A production system for adapting content across devices.",
        }
    )

    result = score_paper(item, threshold=5)

    assert result.is_candidate
    assert "real-time rendering" in result.positive_matches


@pytest.mark.asyncio
@respx.mock
async def test_advances_source_uses_configured_years(fixture_dir: Path) -> None:
    settings = Settings(
        enabled_sources_raw="advances",
        advances_years_raw="2026",
        max_feed_results=10,
        dry_run=True,
    )
    route = respx.get("https://advances.realtimerendering.com/s2026/index.html").mock(
        return_value=httpx.Response(
            200,
            text=(fixture_dir / "advances_2026.html").read_text(encoding="utf-8"),
        )
    )

    items = await AdvancesSource(settings).fetch_recent()

    assert route.called
    assert len(items) == 2
    assert all(item.source_name == "advances" for item in items)


@pytest.mark.asyncio
@respx.mock
async def test_advances_source_skips_missing_year_when_another_year_works(
    fixture_dir: Path,
) -> None:
    settings = Settings(
        enabled_sources_raw="advances",
        advances_years_raw="2027,2026",
        max_feed_results=10,
        dry_run=True,
    )
    respx.get("https://advances.realtimerendering.com/s2027/index.html").mock(
        return_value=httpx.Response(404)
    )
    respx.get("https://advances.realtimerendering.com/s2026/index.html").mock(
        return_value=httpx.Response(
            200,
            text=(fixture_dir / "advances_2026.html").read_text(encoding="utf-8"),
        )
    )

    items = await AdvancesSource(settings).fetch_recent()

    assert len(items) == 2
