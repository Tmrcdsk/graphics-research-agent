from __future__ import annotations

from app.config import Settings
from app.pipeline.run_pipeline import run_once
from app.sources.models import PaperItem
from app.storage.db import Database


class FixtureSource:
    source_name = "arxiv"

    def __init__(self, papers: list[PaperItem]) -> None:
        self._papers = papers

    async def fetch_recent(self) -> list[PaperItem]:
        return self._papers


class MultiFixtureSource:
    source_name = "fixture-arxiv,fixture-news"

    def __init__(self, papers: list[PaperItem]) -> None:
        self._papers = papers

    async def fetch_recent(self) -> list[PaperItem]:
        return self._papers


async def test_pipeline_dry_run_with_fixtures(
    temp_settings: Settings,
    temp_database: Database,
    sample_papers: list[PaperItem],
) -> None:
    stats = await run_once(
        settings=temp_settings,
        source=FixtureSource(sample_papers),
        database=temp_database,
    )

    assert stats.status == "success"
    assert stats.fetched_count == 2
    assert stats.new_count == 2
    assert stats.candidate_count == 1
    assert stats.summarized_count == 1
    assert stats.pushed_count == 1
    assert temp_database.count_rows("papers") == 2
    assert temp_database.count_rows("summaries") == 1
    assert temp_database.list_publish_logs()[0].status == "dry_run"


async def test_pipeline_does_not_reprocess_duplicate_papers(
    temp_settings: Settings,
    temp_database: Database,
    sample_papers: list[PaperItem],
) -> None:
    source = FixtureSource(sample_papers)

    first = await run_once(settings=temp_settings, source=source, database=temp_database)
    second = await run_once(settings=temp_settings, source=source, database=temp_database)

    assert first.pushed_count == 1
    assert second.new_count == 0
    assert second.candidate_count == 0
    assert second.pushed_count == 0
    assert temp_database.count_rows("papers") == 2
    assert temp_database.count_rows("summaries") == 1


async def test_pipeline_dry_run_with_news_feed_item(
    temp_settings: Settings,
    temp_database: Database,
    sample_papers: list[PaperItem],
) -> None:
    news_item = sample_papers[0].model_copy(
        update={
            "source_name": "nvidia",
            "source_id": "rtx-rendering",
            "arxiv_id": "nvidia:rtx-rendering",
            "title": "NVIDIA RTX Neural Rendering and DLSS Ray Reconstruction",
            "abstract": (
                "NVIDIA discusses RTX rendering, DLSS ray reconstruction, "
                "hardware ray tracing, and neural radiance cache."
            ),
            "categories": ["NVIDIA Developer Blog", "Graphics"],
            "abs_url": "https://developer.nvidia.com/blog/example-rtx-rendering",
        }
    )

    stats = await run_once(
        settings=temp_settings,
        source=MultiFixtureSource([news_item]),
        database=temp_database,
    )

    assert stats.status == "success"
    assert stats.fetched_count == 1
    assert stats.new_count == 1
    assert stats.candidate_count == 1
    assert stats.pushed_count == 1
