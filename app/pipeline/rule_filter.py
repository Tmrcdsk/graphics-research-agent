from __future__ import annotations

import re
from dataclasses import dataclass

from app.sources.models import PaperItem

POSITIVE_KEYWORDS: dict[str, int] = {
    "rendering": 3,
    "real-time rendering": 6,
    "real time rendering": 6,
    "path tracing": 6,
    "ray tracing": 6,
    "global illumination": 6,
    "radiance cache": 6,
    "reservoir": 5,
    "restir": 8,
    "rtxdi": 7,
    "denoising": 5,
    "neural rendering": 5,
    "gaussian splatting": 4,
    "brdf": 4,
    "bsdf": 4,
    "material": 3,
    "shader": 5,
    "vulkan": 6,
    "directx": 5,
    "unreal engine": 6,
    "lumen": 5,
    "nanite": 5,
    "dlss": 5,
    "fsr": 5,
}

NEGATIVE_KEYWORDS: dict[str, int] = {
    "medical": -6,
    "ct": -5,
    "mri": -5,
    "remote sensing": -5,
    "satellite": -4,
    "protein": -7,
    "language model": -4,
    "llm": -3,
    "document": -4,
    "ocr": -4,
}


@dataclass(frozen=True)
class RuleFilterResult:
    score: int
    threshold: int
    is_candidate: bool
    positive_matches: list[str]
    negative_matches: list[str]


def _contains_keyword(text: str, keyword: str) -> bool:
    escaped = re.escape(keyword.casefold())
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text) is not None


def score_paper(paper: PaperItem, threshold: int = 5) -> RuleFilterResult:
    text = f"{paper.title}\n{paper.abstract}".casefold()
    score = 0
    positive_matches: list[str] = []
    negative_matches: list[str] = []

    for keyword, weight in POSITIVE_KEYWORDS.items():
        if _contains_keyword(text, keyword):
            score += weight
            positive_matches.append(keyword)

    for keyword, weight in NEGATIVE_KEYWORDS.items():
        if _contains_keyword(text, keyword):
            score += weight
            negative_matches.append(keyword)

    return RuleFilterResult(
        score=score,
        threshold=threshold,
        is_candidate=score >= threshold,
        positive_matches=positive_matches,
        negative_matches=negative_matches,
    )
