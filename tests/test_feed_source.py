from __future__ import annotations

from pathlib import Path

from app.sources.feed_source import FeedSourceConfig, parse_news_feed


def test_parse_news_feed_extracts_source_metadata(fixture_dir: Path) -> None:
    config = FeedSourceConfig(
        source_name="unreal",
        source_label="Unreal Engine",
        feed_url="https://www.unrealengine.com/rss",
        default_author="Epic Games",
    )

    items = parse_news_feed(
        (fixture_dir / "news_feed_sample.xml").read_text(encoding="utf-8"),
        config,
    )

    assert len(items) == 2
    first = items[0]
    assert first.source_name == "unreal"
    assert first.source_id == "unreal-mega-lights-1"
    assert first.arxiv_id.startswith("unreal:")
    assert first.title == "Unreal Engine 5 Mega Lights and Path Tracer Updates"
    assert first.abs_url == "https://www.unrealengine.com/en-US/example/mega-lights"
    assert first.authors == ["Epic Games"]
    assert "Unreal Engine" in first.categories
    assert "hardware ray tracing" in first.abstract
    assert "<p>" not in first.abstract


def test_parse_news_feed_uses_default_author(fixture_dir: Path) -> None:
    config = FeedSourceConfig(
        source_name="nvidia",
        source_label="NVIDIA Developer Blog",
        feed_url="https://developer.nvidia.com/blog/feed/",
        default_author="NVIDIA",
    )

    items = parse_news_feed(
        (fixture_dir / "news_feed_sample.xml").read_text(encoding="utf-8"),
        config,
    )

    assert items[1].authors == ["NVIDIA"]
    assert items[1].source_name == "nvidia"
    assert items[1].arxiv_id.startswith("nvidia:")
