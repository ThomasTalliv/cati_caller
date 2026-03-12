"""Outbound call orchestration and retry logic."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from cati.utils.phone import is_valid_e164, normalize_e164

log = structlog.get_logger(__name__)

_RETRY_DELAYS_S = [900, 900, 900]  # 15 min between retries, 3 attempts


class CallManager:
    """Manages outbound call initiation via SignalWire."""

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            from config.settings import get_settings
            from signalwire.rest import Client  # type: ignore[import]
            s = get_settings().signalwire
            self._client = Client(s.project_id, s.api_token, signalwire_space_url=s.space_url)
        return self._client

    async def initiate_call(
        self,
        survey_id: uuid.UUID,
        phone_number: str,
        *,
        batch_id: uuid.UUID | None = None,
        contact_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        """Create a call record and dial the respondent.

        Returns the internal call_id.
        """
        from cati.db.session import get_session_factory
        from cati.db.repositories.call_repo import CallRepository
        from cati.survey.models import Contact
        from config.settings import get_settings
        from sqlalchemy import select

        # Normalise and validate
        e164 = normalize_e164(phone_number)
        if not is_valid_e164(e164):
            raise ValueError(f"Invalid phone number: {phone_number!r}")

        settings = get_settings()
        factory = get_session_factory()

        # DNC enforcement — check contact record if contact_id given, otherwise check by phone
        async with factory() as session:
            if contact_id is not None:
                dnc_result = await session.execute(
                    select(Contact).where(Contact.id == contact_id)
                )
                contact_obj = dnc_result.scalar_one_or_none()
                if contact_obj is not None and contact_obj.do_not_call:
                    log.warning("dnc_blocked", phone=e164, contact_id=str(contact_id))
                    raise ValueError(f"Phone number {e164} is on the Do-Not-Call list")
            else:
                dnc_result = await session.execute(
                    select(Contact).where(Contact.phone_number == e164, Contact.do_not_call.is_(True))
                )
                if dnc_result.scalar_one_or_none() is not None:
                    log.warning("dnc_blocked", phone=e164)
                    raise ValueError(f"Phone number {e164} is on the Do-Not-Call list")

        # Create DB record first
        async with factory() as session:
            repo = CallRepository(session)
            call = await repo.create_call(
                survey_id=survey_id,
                phone_number=e164,
                batch_id=batch_id,
                contact_id=contact_id,
            )
            call_id = call.id

        log.info("initiating_call", call_id=str(call_id), phone=e164)

        # Dial via SignalWire
        try:
            sw_call = await asyncio.get_event_loop().run_in_executor(
                None,
                self._dial_sync,
                e164,
                settings,
                call_id,
                survey_id,
            )
            sw_call_id = getattr(sw_call, "sid", str(uuid.uuid4()))

            async with factory() as session:
                repo = CallRepository(session)
                await repo.update_status(
                    call_id,
                    "dialing",
                    signalwire_call_id=sw_call_id,
                    started_at=datetime.now(timezone.utc),
                )

        except Exception as exc:
            log.error("call_initiation_failed", call_id=str(call_id), error=str(exc))
            async with factory() as session:
                repo = CallRepository(session)
                await repo.update_status(call_id, "failed", failure_reason=str(exc))
            raise

        return call_id

    def _dial_sync(
        self,
        to: str,
        settings: Any,
        call_id: uuid.UUID,
        survey_id: uuid.UUID,
    ):
        """Synchronous SignalWire dial call."""
        client = self._get_client()
        webhook_url = (
            f"{settings.signalwire.webhook_base_url}"
            f"/webhooks/signalwire/agent?call_id={call_id}&survey_id={survey_id}"
        )
        return client.calls.create(
            to=to,
            from_=settings.signalwire.outbound_number,
            url=webhook_url,
            method="POST",
        )

    async def initiate_batch(
        self,
        survey_id: uuid.UUID,
        contacts: list[dict[str, Any]],
        *,
        batch_name: str | None = None,
        concurrency: int = 5,
    ) -> uuid.UUID:
        """Schedule a batch of calls with concurrency control.

        Args:
            contacts: List of dicts with keys: phone_number, contact_id (optional).
        Returns:
            batch_id
        """
        from cati.db.session import get_session_factory
        from cati.db.repositories.call_repo import CallRepository
        from cati.tasks.call_tasks import dispatch_batch

        factory = get_session_factory()
        async with factory() as session:
            repo = CallRepository(session)
            batch = await repo.create_batch(
                survey_id=survey_id,
                name=batch_name,
                config={"concurrency": concurrency, "total": len(contacts)},
            )
            batch_id = batch.id

        # Kick off async Celery task
        dispatch_batch.delay(
            str(survey_id), str(batch_id), contacts, concurrency
        )
        log.info("batch_dispatched", batch_id=str(batch_id), total=len(contacts))
        return batch_id


def get_call_manager() -> CallManager:
    return CallManager()
