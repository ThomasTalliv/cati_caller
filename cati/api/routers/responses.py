"""Response and transcript read endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from cati.api.dependencies import db_session, require_api_key
from cati.db.repositories.response_repo import ResponseRepository

router = APIRouter(prefix="/api/v1", tags=["responses"], dependencies=[Depends(require_api_key)])


class ResponseOut(BaseModel):
    id: uuid.UUID
    call_id: uuid.UUID
    question_key: str
    raw_transcript: str | None
    parsed_value: Any
    is_refused: bool
    is_skipped: bool
    confidence: float | None
    retries: int
    asked_at: datetime

    model_config = {"from_attributes": True}


class TranscriptTurnOut(BaseModel):
    id: uuid.UUID
    call_id: uuid.UUID
    speaker: str
    text: str
    audio_offset_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/calls/{call_id}/responses", response_model=list[ResponseOut])
async def get_call_responses(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> list[ResponseOut]:
    repo = ResponseRepository(session)
    responses = await repo.list_for_call(call_id)
    return [ResponseOut.model_validate(r) for r in responses]


@router.get("/calls/{call_id}/transcript", response_model=list[TranscriptTurnOut])
async def get_call_transcript(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> list[TranscriptTurnOut]:
    repo = ResponseRepository(session)
    turns = await repo.list_transcript(call_id)
    return [TranscriptTurnOut.model_validate(t) for t in turns]


@router.get("/surveys/{survey_id}/responses", response_model=list[ResponseOut])
async def get_survey_responses(
    survey_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> list[ResponseOut]:
    repo = ResponseRepository(session)
    responses = await repo.list_for_survey(survey_id)
    return [ResponseOut.model_validate(r) for r in responses]


@router.get("/surveys/{survey_id}/stats")
async def get_survey_stats(
    survey_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> dict:
    from sqlalchemy import select, func
    from cati.survey.models import Call

    result = await session.execute(
        select(
            func.count(Call.id).label("total"),
            func.sum(
                (Call.status == "completed").cast(type_=None)
            ).label("completed"),
        ).where(Call.survey_id == survey_id)
    )
    row = result.one()
    total = row.total or 0
    completed = row.completed or 0
    return {
        "survey_id": str(survey_id),
        "total_calls": total,
        "completed_calls": completed,
        "completion_rate": round(completed / total, 3) if total > 0 else 0.0,
    }
