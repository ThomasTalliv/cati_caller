"""Repository for Response and TranscriptTurn records."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cati.survey.models import Response, TranscriptTurn


class ResponseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_response(
        self,
        call_id: uuid.UUID,
        question_id: uuid.UUID,
        question_key: str,
        raw_transcript: str | None = None,
        parsed_value: Any = None,
        is_refused: bool = False,
        is_skipped: bool = False,
        confidence: float | None = None,
        retries: int = 0,
    ) -> Response:
        response = Response(
            call_id=call_id,
            question_id=question_id,
            question_key=question_key,
            raw_transcript=raw_transcript,
            parsed_value=parsed_value,
            is_refused=is_refused,
            is_skipped=is_skipped,
            confidence=confidence,
            retries=retries,
        )
        self._session.add(response)
        await self._session.commit()
        await self._session.refresh(response)
        return response

    async def list_for_call(self, call_id: uuid.UUID) -> list[Response]:
        result = await self._session.execute(
            select(Response).where(Response.call_id == call_id).order_by(Response.asked_at)
        )
        return list(result.scalars().all())

    async def list_for_survey(self, survey_id: uuid.UUID) -> list[Response]:
        from cati.survey.models import Call
        result = await self._session.execute(
            select(Response)
            .join(Call, Call.id == Response.call_id)
            .where(Call.survey_id == survey_id)
            .order_by(Response.asked_at)
        )
        return list(result.scalars().all())

    async def add_transcript_turn(
        self,
        call_id: uuid.UUID,
        speaker: str,
        text: str,
        audio_offset_ms: int | None = None,
    ) -> TranscriptTurn:
        turn = TranscriptTurn(
            call_id=call_id,
            speaker=speaker,
            text=text,
            audio_offset_ms=audio_offset_ms,
        )
        self._session.add(turn)
        await self._session.commit()
        await self._session.refresh(turn)
        return turn

    async def list_transcript(self, call_id: uuid.UUID) -> list[TranscriptTurn]:
        result = await self._session.execute(
            select(TranscriptTurn)
            .where(TranscriptTurn.call_id == call_id)
            .order_by(TranscriptTurn.created_at)
        )
        return list(result.scalars().all())
