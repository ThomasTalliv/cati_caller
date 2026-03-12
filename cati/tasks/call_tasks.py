"""Celery tasks for scheduling and dispatching outbound call batches."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any

import structlog

from cati.tasks.worker import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(bind=True, name="cati.tasks.call_tasks.dispatch_batch", max_retries=3)
def dispatch_batch(
    self,
    survey_id: str,
    batch_id: str,
    contacts: list[dict[str, Any]],
    concurrency: int = 5,
) -> dict:
    """Dispatch a batch of outbound calls with concurrency control."""
    return asyncio.get_event_loop().run_until_complete(
        _dispatch_batch_async(
            uuid.UUID(survey_id),
            uuid.UUID(batch_id),
            contacts,
            concurrency,
        )
    )


async def _dispatch_batch_async(
    survey_id: uuid.UUID,
    batch_id: uuid.UUID,
    contacts: list[dict[str, Any]],
    concurrency: int,
) -> dict:
    from cati.db.session import get_session_factory
    from cati.db.repositories.call_repo import CallRepository
    from cati.telephony.call_manager import CallManager

    factory = get_session_factory()
    async with factory() as session:
        repo = CallRepository(session)
        await repo.update_batch_status(batch_id, "running")

    manager = CallManager()
    sem = asyncio.Semaphore(concurrency)
    results = {"dispatched": 0, "failed": 0}

    async def dial_one(contact: dict) -> None:
        async with sem:
            try:
                phone = contact.get("phone_number", "")
                contact_id = contact.get("contact_id")
                if contact_id:
                    contact_id = uuid.UUID(str(contact_id))
                await manager.initiate_call(
                    survey_id=survey_id,
                    phone_number=phone,
                    batch_id=batch_id,
                    contact_id=contact_id,
                )
                results["dispatched"] += 1
            except Exception as exc:
                log.error("batch_call_failed", phone=contact.get("phone_number"), error=str(exc))
                results["failed"] += 1
            # Small delay to avoid hammering the telephony API
            await asyncio.sleep(0.5)

    await asyncio.gather(*[dial_one(c) for c in contacts])

    async with factory() as session:
        repo = CallRepository(session)
        await repo.update_batch_status(batch_id, "completed")

    log.info("batch_completed", batch_id=str(batch_id), **results)
    return results
