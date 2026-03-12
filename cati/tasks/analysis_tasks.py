"""Celery tasks for post-call AI analysis."""
from __future__ import annotations

import asyncio
import uuid

import structlog

from cati.tasks.worker import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(name="cati.tasks.analysis_tasks.run_call_analysis", bind=True, max_retries=3)
def run_call_analysis(self, call_id: str) -> dict:
    """Run full analysis for a single completed call."""
    return asyncio.get_event_loop().run_until_complete(
        _analyze_call_async(uuid.UUID(call_id))
    )


@celery_app.task(name="cati.tasks.analysis_tasks.run_survey_analysis", bind=True, max_retries=3)
def run_survey_analysis(self, survey_id: str) -> dict:
    """Run aggregate analysis for all calls in a survey."""
    return asyncio.get_event_loop().run_until_complete(
        _analyze_survey_async(uuid.UUID(survey_id))
    )


async def _analyze_call_async(call_id: uuid.UUID) -> dict:
    from cati.analysis.analyzer import CallAnalyzer
    analyzer = CallAnalyzer()
    try:
        return await analyzer.analyze_call(call_id)
    except Exception as exc:
        log.error("call_analysis_failed", call_id=str(call_id), error=str(exc))
        raise


async def _analyze_survey_async(survey_id: uuid.UUID) -> dict:
    from cati.analysis.analyzer import CallAnalyzer
    analyzer = CallAnalyzer()
    try:
        return await analyzer.analyze_survey(survey_id)
    except Exception as exc:
        log.error("survey_analysis_failed", survey_id=str(survey_id), error=str(exc))
        raise
