from __future__ import annotations

from dataclasses import dataclass

from app.pipeline.normalize import normalize_paper
from app.sources.models import PaperItem
from app.storage.db import Database


@dataclass(frozen=True)
class NewPaper:
    paper_id: int
    paper: PaperItem


@dataclass(frozen=True)
class DedupeResult:
    new_papers: list[NewPaper]
    duplicate_count: int


def insert_new_papers(database: Database, papers: list[PaperItem]) -> DedupeResult:
    new_papers: list[NewPaper] = []
    duplicate_count = 0
    for paper in papers:
        normalized = normalize_paper(paper)
        result = database.insert_paper(normalized)
        if result.is_new:
            new_papers.append(NewPaper(paper_id=result.paper_id, paper=normalized))
        else:
            duplicate_count += 1
    return DedupeResult(new_papers=new_papers, duplicate_count=duplicate_count)
