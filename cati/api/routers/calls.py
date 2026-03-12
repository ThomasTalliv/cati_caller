"""Call initiation and monitoring endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from cati.api.dependencies import db_session, require_api_key
from cati.api.schemas.call import BatchInitiate, BatchOut, CallInitiate, CallOut
from cati.db.repositories.call_repo import CallRepository

router = APIRouter(prefix="/api/v1", tags=["calls"], dependencies=[Depends(require_api_key)])


@router.post("/calls/initiate", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def initiate_call(body: CallInitiate) -> dict:
    from cati.telephony.call_manager import get_call_manager
    manager = get_call_manager()
    try:
        call_id = await manager.initiate_call(
            survey_id=body.survey_id,
            phone_number=body.phone_number,
            contact_id=body.contact_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return {"call_id": str(call_id), "status": "dialing"}


@router.post("/calls/batch", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def initiate_batch(body: BatchInitiate) -> dict:
    from cati.telephony.call_manager import get_call_manager
    manager = get_call_manager()
    batch_id = await manager.initiate_batch(
        survey_id=body.survey_id,
        contacts=body.contacts,
        batch_name=body.name,
        concurrency=body.concurrency,
    )
    return {"batch_id": str(batch_id), "status": "dispatched", "total": len(body.contacts)}


@router.get("/calls", response_model=list[CallOut])
async def list_calls(
    survey_id: uuid.UUID | None = None,
    call_status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(db_session),
) -> list[CallOut]:
    repo = CallRepository(session)
    calls = await repo.list(survey_id=survey_id, status=call_status, limit=limit, offset=offset)
    return [CallOut.model_validate(c) for c in calls]


@router.get("/calls/{call_id}", response_model=CallOut)
async def get_call(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> CallOut:
    repo = CallRepository(session)
    call = await repo.get(call_id)
    if call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")
    return CallOut.model_validate(call)


@router.delete("/calls/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_call(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> None:
    repo = CallRepository(session)
    call = await repo.get(call_id)
    if call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")
    if call.status not in ("pending", "dialing"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel a call with status {call.status!r}",
        )
    await repo.update_status(call_id, "failed", failure_reason="Cancelled by user")


@router.get("/batches", response_model=list[BatchOut])
async def list_batches(
    session: AsyncSession = Depends(db_session),
) -> list[BatchOut]:
    from sqlalchemy import select
    from cati.survey.models import CallBatch
    result = await session.execute(select(CallBatch).order_by(CallBatch.created_at.desc()))
    return [BatchOut.model_validate(b) for b in result.scalars().all()]


@router.get("/batches/{batch_id}", response_model=BatchOut)
async def get_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> BatchOut:
    repo = CallRepository(session)
    batch = await repo.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return BatchOut.model_validate(batch)


@router.post("/batches/{batch_id}/pause", status_code=status.HTTP_204_NO_CONTENT)
async def pause_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> None:
    repo = CallRepository(session)
    await repo.update_batch_status(batch_id, "paused")


@router.post("/batches/{batch_id}/resume", status_code=status.HTTP_204_NO_CONTENT)
async def resume_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> None:
    repo = CallRepository(session)
    await repo.update_batch_status(batch_id, "running")
