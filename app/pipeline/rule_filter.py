from __future__ import annotations

import re
from dataclasses import dataclass

from app.sources.models import PaperItem

POSITIVE_KEYWORDS: dict[str, int] = {
    "rendering": 3,
    "real-time rendering": 6,
    "real time rendering": 6,
    "real-time graphics": 6,
    "real time graphics": 6,
    "rendering pipeline": 5,
    "graphics pipeline": 5,
    "rendering architecture": 5,
    "physically based rendering": 6,
    "pbr": 5,
    "gpu optimization": 5,
    "occlusion culling": 5,
    "advanced graphics summit": 5,
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
    "mesh shader": 6,
    "work graph": 5,
    "vulkan": 6,
    "directx": 5,
    "directx 12": 6,
    "direct3d": 6,
    "d3d12": 6,
    "shader model": 6,
    "agility sdk": 5,
    "agilitysdk": 5,
    "unreal engine": 6,
    "ue5": 6,
    "ue 5": 6,
    "unreal": 4,
    "mega lights": 6,
    "path tracer": 5,
    "hardware ray tracing": 6,
    "virtual shadow map": 5,
    "virtualized geometry": 4,
    "lumen": 5,
    "nanite": 5,
    "rtx": 4,
    "dlss": 5,
    "ray reconstruction": 5,
    "opacity micromap": 5,
    "neural radiance cache": 6,
    "fsr": 5,
    "fidelityfx": 6,
    "super resolution": 5,
    "upscaling": 5,
    "frame generation": 5,
    "rasterization": 5,
    "temporal anti-aliasing": 5,
    "screen space reflections": 5,
    "ambient occlusion": 5,
    "volumetric rendering": 5,
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
    text = f"{paper.title}\n{paper.abstract}\n{' '.join(paper.categories)}".casefold()
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
