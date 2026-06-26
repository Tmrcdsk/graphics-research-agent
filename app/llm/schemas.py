from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReadPriority(StrEnum):
    MUST_READ = "must_read"
    READ_LATER = "read_later"
    ARCHIVE_ONLY = "archive_only"
    SKIP = "skip"


class ClassificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_graphics_related: bool
    is_rendering_related: bool
    main_category: str
    sub_tags: list[str]
    technical_keywords: list[str]
    novelty_score: int = Field(ge=1, le=5)
    job_relevance_score: int = Field(ge=1, le=5)
    read_priority: ReadPriority
    reason: str
    uncertainty: str


class SummaryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title_zh: str
    one_sentence: str
    problem: str
    method: str
    relation_to_user_goal: str
    likely_usefulness: str
    uncertainty: str
    read_priority: ReadPriority
    job_relevance_score: int = Field(ge=1, le=5)
    novelty_score: int = Field(ge=1, le=5)
