from __future__ import annotations

import json

from app.llm.schemas import ClassificationResult
from app.sources.models import PaperItem

CLASSIFICATION_PROMPT_VERSION = "classification_v1"
SUMMARY_PROMPT_VERSION = "summary_v1"


def _authors(paper: PaperItem) -> str:
    return ", ".join(paper.authors) if paper.authors else "Unknown"


def _categories(paper: PaperItem) -> str:
    return ", ".join(paper.categories) if paper.categories else "Unknown"


def build_classification_prompt(paper: PaperItem) -> str:
    return f"""You are a critical technical assistant for reading computer graphics papers.

User profile:
- The user is learning toward game engine / real-time rendering engineering.
- The user cares about Vulkan, Unreal Engine, ReSTIR, GPU rendering pipelines,
  ray tracing, path tracing, global illumination, denoising, shaders, materials,
  and real-time graphics systems.
- The user does not want noisy recommendations from generic AI, medical imaging,
  remote sensing, pure 3D vision reconstruction, OCR, or unrelated machine learning.

Task:
Given the paper metadata below, decide whether this paper should be pushed to the user.

Paper title:
{paper.title}

Authors:
{_authors(paper)}

arXiv categories:
{_categories(paper)}

Abstract:
{paper.abstract}

Return JSON only. Do not wrap the JSON in Markdown.

Required JSON fields:
{{
  "is_graphics_related": boolean,
  "is_rendering_related": boolean,
  "main_category": string,
  "sub_tags": string[],
  "technical_keywords": string[],
  "novelty_score": integer from 1 to 5,
  "job_relevance_score": integer from 1 to 5,
  "read_priority": "must_read" | "read_later" | "archive_only" | "skip",
  "reason": string,
  "uncertainty": string
}}

Be conservative. Do not overpraise. If the paper is only weakly related to
rendering, choose archive_only or skip.
"""


def build_summary_prompt(paper: PaperItem, classification: ClassificationResult) -> str:
    classification_json = json.dumps(classification.model_dump(mode="json"), ensure_ascii=False)
    return f"""You are a critical technical assistant summarizing computer graphics
and rendering papers for a Chinese-speaking learner.

The user is learning toward game engine / real-time rendering engineering and
cares about Vulkan, UE rendering, ReSTIR, GPU rendering pipelines, ray tracing,
path tracing, global illumination, denoising, shaders, and materials.

Summarize the paper based only on the provided title and abstract. Do not claim
that the paper has code, benchmarks, or production usability unless it is
explicitly stated in the metadata.

Paper title:
{paper.title}

Authors:
{_authors(paper)}

arXiv categories:
{_categories(paper)}

Abstract:
{paper.abstract}

Classification result:
{classification_json}

Return JSON only. Do not wrap the JSON in Markdown.

Required JSON fields:
{{
  "title_zh": string,
  "one_sentence": string,
  "problem": string,
  "method": string,
  "relation_to_user_goal": string,
  "likely_usefulness": string,
  "uncertainty": string,
  "read_priority": "must_read" | "read_later" | "archive_only" | "skip",
  "job_relevance_score": integer from 1 to 5,
  "novelty_score": integer from 1 to 5
}}

Write the content in Chinese, but keep technical terms such as ReSTIR, path
tracing, BRDF, Vulkan, UE, shader, and GPU in English when appropriate.

Avoid marketing language. Be precise and conservative.
"""
