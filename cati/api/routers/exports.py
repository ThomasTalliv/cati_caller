"""Export trigger and download endpoints."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cati.api.dependencies import db_session, require_api_key
from cati.survey.models import Export

router = APIRouter(prefix="/api/v1/exports", tags=["exports"], dependencies=[Depends(require_api_key)])

ExportFormat = Literal["txt", "excel", "word", "gsheets"]


class ExportRequest(BaseModel):
    survey_id: uuid.UUID
    format: ExportFormat
    call_ids: list[uuid.UUID] | None = None


class ExportOut(BaseModel):
    id: uuid.UUID
    survey_id: uuid.UUID
    format: str
    status: str
    file_path: str | None
    external_url: str | None
    call_count: int | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


@router.post("", response_model=ExportOut, status_code=status.HTTP_202_ACCEPTED)
async def request_export(
    body: ExportRequest,
    session: AsyncSession = Depends(db_session),
) -> ExportOut:
    export = Export(
        survey_id=body.survey_id,
        format=body.format,
        status="pending",
    )
    session.add(export)
    await session.commit()
    await session.refresh(export)

    from cati.tasks.export_tasks import generate_export
    generate_export.delay(
        str(export.id),
        str(body.survey_id),
        body.format,
        [str(c) for c in body.call_ids] if body.call_ids else None,
    )

    return ExportOut.model_validate(export)


@router.get("", response_model=list[ExportOut])
async def list_exports(session: AsyncSession = Depends(db_session)) -> list[ExportOut]:
    result = await session.execute(select(Export).order_by(Export.created_at.desc()))
    return [ExportOut.model_validate(e) for e in result.scalars().all()]


@router.get("/{export_id}", response_model=ExportOut)
async def get_export(
    export_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> ExportOut:
    result = await session.execute(select(Export).where(Export.id == export_id))
    export = result.scalar_one_or_none()
    if export is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    return ExportOut.model_validate(export)


@router.get("/{export_id}/download")
async def download_export(
    export_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> FileResponse:
    result = await session.execute(select(Export).where(Export.id == export_id))
    export = result.scalar_one_or_none()
    if export is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    if export.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Export is not ready (status: {export.status})",
        )
    if export.external_url:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=export.external_url)
    if not export.file_path or not os.path.exists(export.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found")

    media_types = {
        "txt": "text/plain",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    media_type = media_types.get(export.format, "application/octet-stream")
    return FileResponse(
        path=export.file_path,
        media_type=media_type,
        filename=os.path.basename(export.file_path),
    )
