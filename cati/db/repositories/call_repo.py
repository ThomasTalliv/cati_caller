"""Repository for Call and CallBatch records."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cati.survey.models import Call, CallBatch


class CallRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_call(
        self,
        survey_id: uuid.UUID,
        phone_number: str,
        batch_id: uuid.UUID | None = None,
        contact_id: uuid.UUID | None = None,
    ) -> Call:
        call = Call(
            survey_id=survey_id,
            phone_number=phone_number,
            batch_id=batch_id,
            contact_id=contact_id,
            status="pending",
        )
        self._session.add(call)
        await self._session.commit()
        await self._session.refresh(call)
        return call

    async def get(self, call_id: uuid.UUID) -> Call | None:
        result = await self._session.execute(
            select(Call)
            .options(selectinload(Call.responses), selectinload(Call.transcript_turns))
            .where(Call.id == call_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        survey_id: uuid.UUID | None = None,
        status: str | None = None,
        batch_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Call]:
        query = select(Call).order_by(Call.created_at.desc()).limit(limit).offset(offset)
        if survey_id:
            query = query.where(Call.survey_id == survey_id)
        if status:
            query = query.where(Call.status == status)
        if batch_id:
            query = query.where(Call.batch_id == batch_id)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update_status(self, call_id: uuid.UUID, status: str, **kwargs: Any) -> Call | None:
        call = await self.get(call_id)
        if call is None:
            return None
        call.status = status
        for key, value in kwargs.items():
            if hasattr(call, key):
                setattr(call, key, value)
        await self._session.commit()
        return call

    async def create_batch(
        self,
        survey_id: uuid.UUID,
        name: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> CallBatch:
        batch = CallBatch(
            survey_id=survey_id,
            name=name,
            config=config or {},
        )
        self._session.add(batch)
        await self._session.commit()
        await self._session.refresh(batch)
        return batch

    async def get_batch(self, batch_id: uuid.UUID) -> CallBatch | None:
        result = await self._session.execute(
            select(CallBatch).where(CallBatch.id == batch_id)
        )
        return result.scalar_one_or_none()

    async def update_batch_status(self, batch_id: uuid.UUID, status: str) -> CallBatch | None:
        batch = await self.get_batch(batch_id)
        if batch is None:
            return None
        batch.status = status
        await self._session.commit()
        return batch
