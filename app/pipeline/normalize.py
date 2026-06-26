from __future__ import annotations

from app.sources.arxiv_source import normalize_whitespace
from app.sources.models import PaperItem
from app.utils.hashing import stable_title_hash


def normalize_paper(paper: PaperItem) -> PaperItem:
    title = normalize_whitespace(paper.title)
    abstract = normalize_whitespace(paper.abstract)
    return paper.model_copy(
        update={
            "title": title,
            "abstract": abstract,
            "title_hash": stable_title_hash(title),
        }
    )
