from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from app.config import Settings
from app.sources.gdc_vault_source import (
    GdcVaultSource,
    build_gdc_vault_paper,
    is_rendering_catalog_entry,
    parse_gdc_vault_catalog,
)


def test_parse_gdc_vault_catalog_deduplicates_media_variants(fixture_dir: Path) -> None:
    entries = parse_gdc_vault_catalog(
        (fixture_dir / "gdc_vault_catalog.html").read_text(encoding="utf-8"),
        catalog_url="https://gdcvault.com/browse/gdc-26",
        year=2026,
    )

    assert len(entries) == 2
    rendering_entry = entries[0]
    assert rendering_entry.session_id == 1035800
    assert rendering_entry.media_type == "slides"
    assert rendering_entry.authors == ["Sheng Feng"]
    assert rendering_entry.company == "MoreFun Studios"
    assert rendering_entry.track == "Visual Development"
    assert rendering_entry.url == ("https://gdcvault.com/play/1035800/Illuminating-Rocos-Legacy")


def test_gdc_vault_catalog_prefilter_keeps_rendering_only(fixture_dir: Path) -> None:
    entries = parse_gdc_vault_catalog(
        (fixture_dir / "gdc_vault_catalog.html").read_text(encoding="utf-8"),
        catalog_url="https://gdcvault.com/browse/gdc-26",
        year=2026,
    )

    assert [is_rendering_catalog_entry(entry) for entry in entries] == [True, False]


def test_build_gdc_vault_paper_uses_detail_overview(fixture_dir: Path) -> None:
    entry = parse_gdc_vault_catalog(
        (fixture_dir / "gdc_vault_catalog.html").read_text(encoding="utf-8"),
        catalog_url="https://gdcvault.com/browse/gdc-26",
        year=2026,
    )[0]

    paper = build_gdc_vault_paper(
        entry,
        (fixture_dir / "gdc_vault_detail.html").read_text(encoding="utf-8"),
    )

    assert paper.source_name == "gdc_vault"
    assert paper.source_id == "1035800"
    assert paper.authors == ["Sheng Feng"]
    assert "radiance caching" in paper.abstract
    assert paper.categories == [
        "GDC Vault",
        "Game Developers Conference 2026",
        "Visual Development",
        "slides",
    ]
    assert paper.published_at.year == 2026
    assert paper.abs_url == entry.url


@pytest.mark.asyncio
@respx.mock
async def test_gdc_vault_source_fetches_only_rendering_details(fixture_dir: Path) -> None:
    settings = Settings(
        enabled_sources_raw="gdc_vault",
        gdc_vault_years_raw="2026",
        max_feed_results=10,
        dry_run=True,
    )
    catalog_route = respx.get("https://gdcvault.com/browse/gdc-26").mock(
        return_value=httpx.Response(
            200,
            text=(fixture_dir / "gdc_vault_catalog.html").read_text(encoding="utf-8"),
        )
    )
    detail_route = respx.get("https://gdcvault.com/play/1035800/Illuminating-Rocos-Legacy").mock(
        return_value=httpx.Response(
            200,
            text=(fixture_dir / "gdc_vault_detail.html").read_text(encoding="utf-8"),
        )
    )

    items = await GdcVaultSource(settings).fetch_recent()

    assert catalog_route.called
    assert detail_route.called
    assert len(items) == 1
    assert items[0].source_name == "gdc_vault"
