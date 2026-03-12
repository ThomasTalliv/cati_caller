"""Celery tasks for async export generation."""
from __future__ import annotations

import asyncio
import uuid

import structlog

from cati.tasks.worker import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(name="cati.tasks.export_tasks.generate_export", bind=True, max_retries=3)
def generate_export(
    self,
    export_id: str,
    survey_id: str,
    format: str,
    call_ids: list[str] | None = None,
) -> dict:
    """Generate an export file and update the Export record."""
    return asyncio.get_event_loop().run_until_complete(
        _generate_export_async(
            uuid.UUID(export_id),
            uuid.UUID(survey_id),
            format,
            [uuid.UUID(c) for c in call_ids] if call_ids else None,
        )
    )


async def _generate_export_async(
    export_id: uuid.UUID,
    survey_id: uuid.UUID,
    format: str,
    call_ids: list[uuid.UUID] | None,
) -> dict:
    from cati.export import get_exporter
    from cati.db.session import get_session_factory
    from cati.survey.models import Export
    from sqlalchemy import select
    from datetime import datetime, timezone

    factory = get_session_factory()

    try:
        exporter = get_exporter(format)
        result = await exporter.export(survey_id, call_ids=call_ids)

        async with factory() as session:
            q = await session.execute(select(Export).where(Export.id == export_id))
            export = q.scalar_one_or_none()
            if export:
                export.status = "completed"
                export.file_path = result.file_path
                export.external_url = result.external_url
                export.completed_at = datetime.now(timezone.utc)
                await session.commit()

        log.info("export_completed", export_id=str(export_id), format=format)
        return {"export_id": str(export_id), "status": "completed"}

    except Exception as exc:
        async with factory() as session:
            q = await session.execute(select(Export).where(Export.id == export_id))
            export = q.scalar_one_or_none()
            if export:
                export.status = "failed"
                await session.commit()
        log.error("export_failed", export_id=str(export_id), error=str(exc))
        raise
