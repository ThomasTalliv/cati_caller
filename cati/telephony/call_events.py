"""Webhook handlers for SignalWire call status callbacks."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Form, Query, Response

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/webhooks/signalwire", tags=["webhooks"])


@router.post("/call-status")
async def call_status_webhook(
    CallSid: str = Form(default=""),
    CallStatus: str = Form(default=""),
    CallDuration: str | None = Form(default=None),
    call_id: uuid.UUID | None = Query(default=None),
) -> Response:
    """Receive SignalWire call status updates (answered, completed, failed, etc.)."""
    log.info(
        "signalwire_call_status",
        signalwire_sid=CallSid,
        status=CallStatus,
        call_id=str(call_id),
    )

    if call_id is None:
        return Response(status_code=204)

    from cati.db.session import get_session_factory
    from cati.db.repositories.call_repo import CallRepository

    status_map = {
        "in-progress": "in_progress",
        "completed": "completed",
        "busy": "no_answer",
        "no-answer": "no_answer",
        "failed": "failed",
        "canceled": "failed",
    }
    internal_status = status_map.get(CallStatus.lower(), CallStatus.lower())

    kwargs = {}
    if CallStatus.lower() in ("completed", "busy", "no-answer", "failed", "canceled"):
        kwargs["ended_at"] = datetime.now(timezone.utc)
    if CallDuration:
        try:
            kwargs["duration_s"] = int(CallDuration)
        except ValueError:
            pass

    factory = get_session_factory()
    async with factory() as session:
        repo = CallRepository(session)
        await repo.update_status(call_id, internal_status, **kwargs)

    # Trigger post-call analysis if completed
    if internal_status == "completed":
        from cati.tasks.analysis_tasks import run_call_analysis
        run_call_analysis.delay(str(call_id))

    return Response(status_code=204)


@router.post("/agent")
async def agent_webhook(
    call_id: uuid.UUID | None = Query(default=None),
    survey_id: uuid.UUID | None = Query(default=None),
) -> dict:
    """SWAIG tool callback — SignalWire passes control to the agent."""
    log.info("signalwire_agent_webhook", call_id=str(call_id), survey_id=str(survey_id))

    if call_id is None or survey_id is None:
        return {"response": "Missing call_id or survey_id", "stop": True}

    from cati.telephony.signalwire_agent import CATIAgent
    agent = CATIAgent(call_id=call_id, survey_id=survey_id, phone_number="")
    await agent.initialize()
    greeting_audio = await agent.on_call_answered()

    # Return TwiML-compatible response
    return {
        "response": "Survey started",
        "action": "play_audio",
        "audio_base64": greeting_audio.hex() if greeting_audio else "",
    }
