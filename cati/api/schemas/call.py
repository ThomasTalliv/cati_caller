"""Pydantic schemas for call and batch endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CallInitiate(BaseModel):
    survey_id: uuid.UUID
    phone_number: str
    contact_id: uuid.UUID | None = None


class BatchInitiate(BaseModel):
    survey_id: uuid.UUID
    name: str | None = None
    contacts: list[dict[str, Any]] = Field(min_length=1)
    concurrency: int = Field(default=5, ge=1, le=50)


class CallOut(BaseModel):
    id: uuid.UUID
    survey_id: uuid.UUID
    phone_number: str
    status: str
    signalwire_call_id: str | None
    started_at: datetime | None
    answered_at: datetime | None
    ended_at: datetime | None
    duration_s: int | None
    attempt_number: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BatchOut(BaseModel):
    id: uuid.UUID
    survey_id: uuid.UUID
    name: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
