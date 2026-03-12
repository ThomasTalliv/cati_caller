"""Pydantic schemas for survey API endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

QuestionType = Literal[
    "open_ended", "single_choice", "multiple_choice", "numeric", "yes_no", "rating_scale", "date"
]


# ── Request schemas ────────────────────────────────────────────────────────────

class QuestionCreate(BaseModel):
    question_key: str = Field(min_length=1, max_length=100)
    question_type: QuestionType
    text: str = Field(min_length=1)
    rephrasing: str | None = None
    options: list[dict[str, Any]] | None = None
    validation: dict[str, Any] | None = None
    required: bool = True
    max_retries: int = Field(default=2, ge=0, le=10)


class SkipRuleCreate(BaseModel):
    source_question_key: str
    condition_expr: str = Field(min_length=1)
    target_question_key: str | None = None
    priority: int = 0


class SurveyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    language: str = "en"
    intro_text: str | None = None
    outro_text: str | None = None
    max_duration_s: int = Field(default=900, ge=60, le=3600)
    metadata: dict[str, Any] = Field(default_factory=dict)
    questions: list[QuestionCreate] = Field(default_factory=list)
    skip_rules: list[SkipRuleCreate] = Field(default_factory=list)


class SurveyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    language: str | None = None
    intro_text: str | None = None
    outro_text: str | None = None
    max_duration_s: int | None = Field(default=None, ge=60, le=3600)


class QuestionReorder(BaseModel):
    question_ids: list[uuid.UUID]


# ── Response schemas ───────────────────────────────────────────────────────────

class QuestionOut(BaseModel):
    id: uuid.UUID
    survey_id: uuid.UUID
    position: int
    question_key: str
    question_type: str
    text: str
    rephrasing: str | None
    options: list[dict[str, Any]] | None
    validation: dict[str, Any] | None
    required: bool
    max_retries: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SkipRuleOut(BaseModel):
    id: uuid.UUID
    survey_id: uuid.UUID
    source_question_id: uuid.UUID
    target_question_id: uuid.UUID | None
    condition_expr: str
    priority: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SurveyOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    status: str
    language: str
    intro_text: str | None
    outro_text: str | None
    max_duration_s: int
    metadata: dict[str, Any] = Field(alias="metadata_")
    created_at: datetime
    updated_at: datetime
    questions: list[QuestionOut] = Field(default_factory=list)
    skip_rules: list[SkipRuleOut] = Field(default_factory=list)

    model_config = {"from_attributes": True, "populate_by_name": True}


class SurveyListItem(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    language: str
    created_at: datetime
    question_count: int = 0

    model_config = {"from_attributes": True}
