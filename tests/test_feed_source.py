from __future__ import annotations

from pathlib import Path

import pytest

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


@pytest.mark.parametrize(
    ("fixture_name", "source_name", "source_label", "default_author", "title_fragment"),
    [
        ("gpuopen_feed.xml", "gpuopen", "AMD GPUOpen", "AMD", "FSR Upscaling"),
        (
            "directx_feed.xml",
            "directx",
            "DirectX Developer Blog",
            "Microsoft",
            "Shader Model",
        ),
        (
            "vulkan_feed.xml",
            "vulkan",
            "Khronos Vulkan News",
            "Khronos Group",
            "Vulkan Ray Tracing",
        ),
        (
            "siggraph_realtime_feed.xml",
            "siggraph_realtime",
            "ACM SIGGRAPH Real-Time",
            "ACM SIGGRAPH",
            "Real-Time Neural Rendering",
        ),
        (
            "siggraph_research_feed.xml",
            "siggraph_research",
            "ACM SIGGRAPH Research",
            "ACM SIGGRAPH",
            "Path Tracing",
        ),
    ],
)
def test_parse_each_official_feed_fixture(
    fixture_dir: Path,
    fixture_name: str,
    source_name: str,
    source_label: str,
    default_author: str,
    title_fragment: str,
) -> None:
    config = FeedSourceConfig(
        source_name=source_name,
        source_label=source_label,
        feed_url=f"https://example.test/{source_name}.xml",
        default_author=default_author,
    )

    items = parse_news_feed((fixture_dir / fixture_name).read_text(encoding="utf-8"), config)

    assert len(items) == 1
    item = items[0]
    assert item.source_name == source_name
    assert item.arxiv_id.startswith(f"{source_name}:")
    assert title_fragment in item.title
    assert item.authors
    assert item.abstract
    assert item.abs_url.startswith("https://")
    assert source_label in item.categories
