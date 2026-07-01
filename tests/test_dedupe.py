from __future__ import annotations

from app.pipeline.dedupe import insert_new_papers
from app.sources.models import PaperItem
from app.storage.db import Database


def test_dedupe_by_arxiv_id(temp_database: Database, sample_papers: list[PaperItem]) -> None:
    first = sample_papers[0]

    first_result = insert_new_papers(temp_database, [first])
    second_result = insert_new_papers(temp_database, [first])

    assert len(first_result.new_papers) == 1
    assert len(second_result.new_papers) == 0
    assert second_result.duplicate_count == 1
    assert temp_database.count_rows("papers") == 1


def test_dedupe_by_title_hash(temp_database: Database, sample_papers: list[PaperItem]) -> None:
    first = sample_papers[0]
    same_title = first.model_copy(
        update={
            "arxiv_id": "2606.99999",
            "abs_url": "http://arxiv.org/abs/2606.99999v1",
            "pdf_url": "http://arxiv.org/pdf/2606.99999v1",
        }
    )

    result = insert_new_papers(temp_database, [first, same_title])

    assert len(result.new_papers) == 1
    assert result.duplicate_count == 1
    assert temp_database.count_rows("papers") == 1


def test_dedupe_by_source_id(temp_database: Database, sample_papers: list[PaperItem]) -> None:
    first = sample_papers[0].model_copy(
        update={
            "source_name": "unreal",
            "source_id": "same-source-item",
            "arxiv_id": "unreal:first",
            "abs_url": "https://www.unrealengine.com/en-US/first",
            "title": "First Unreal Rendering Article",
            "title_hash": "first-hash",
        }
    )
    duplicate = first.model_copy(
        update={
            "arxiv_id": "unreal:second",
            "abs_url": "https://www.unrealengine.com/en-US/second",
            "title": "Second Unreal Rendering Article",
            "title_hash": "second-hash",
        }
    )

    result = insert_new_papers(temp_database, [first, duplicate])

    assert len(result.new_papers) == 1
    assert result.duplicate_count == 1
    assert temp_database.count_rows("papers") == 1
