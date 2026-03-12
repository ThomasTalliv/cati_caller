"""AI analysis trigger and read endpoints."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from cati.api.dependencies import db_session, require_api_key
from cati.survey.models import AnalysisReport

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"], dependencies=[Depends(require_api_key)])


@router.post("/calls/{call_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_call_analysis(call_id: uuid.UUID) -> dict:
    from cati.tasks.analysis_tasks import run_call_analysis
    task = run_call_analysis.delay(str(call_id))
    return {"task_id": task.id, "call_id": str(call_id), "status": "queued"}


@router.get("/calls/{call_id}")
async def get_call_analysis(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> dict:
    result = await session.execute(
        select(AnalysisReport)
        .where(AnalysisReport.call_id == call_id)
        .order_by(AnalysisReport.created_at.desc())
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return {
        "id": str(report.id),
        "call_id": str(report.call_id),
        "report_type": report.report_type,
        "llm_provider": report.llm_provider,
        "llm_model": report.llm_model,
        "content": report.content,
        "created_at": report.created_at.isoformat(),
    }


@router.post("/surveys/{survey_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_survey_analysis(survey_id: uuid.UUID) -> dict:
    from cati.tasks.analysis_tasks import run_survey_analysis
    task = run_survey_analysis.delay(str(survey_id))
    return {"task_id": task.id, "survey_id": str(survey_id), "status": "queued"}


@router.get("/surveys/{survey_id}")
async def get_survey_analysis(
    survey_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> dict:
    result = await session.execute(
        select(AnalysisReport)
        .where(
            AnalysisReport.survey_id == survey_id,
            AnalysisReport.report_type == "survey_aggregate",
        )
        .order_by(AnalysisReport.created_at.desc())
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return {
        "id": str(report.id),
        "survey_id": str(report.survey_id),
        "report_type": report.report_type,
        "content": report.content,
        "created_at": report.created_at.isoformat(),
    }
