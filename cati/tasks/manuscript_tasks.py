"""Celery tasks for the multiagent manuscript review pipeline."""
from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from typing import Any

import structlog

from cati.tasks.worker import celery_app

log = structlog.get_logger(__name__)

# Redis-backed session store keyed by task id.
_SESSION_KEY_PREFIX = "manuscript_review:"


def _store_session(task_id: str, data: dict) -> None:
    """Persist session data to Redis (via Celery backend)."""
    from cati.tasks.worker import celery_app

    backend = celery_app.backend
    key = f"{_SESSION_KEY_PREFIX}{task_id}"
    backend.set(key, json.dumps(data, default=str))


def get_session_data(task_id: str) -> dict | None:
    """Retrieve session data from Redis."""
    from cati.tasks.worker import celery_app

    backend = celery_app.backend
    key = f"{_SESSION_KEY_PREFIX}{task_id}"
    raw = backend.get(key)
    if raw is None:
        return None
    return json.loads(raw)


@celery_app.task(
    name="cati.tasks.manuscript_tasks.run_manuscript_review",
    bind=True,
    max_retries=1,
    time_limit=3600,
    soft_time_limit=3300,
)
def run_manuscript_review(self, manuscript_path: str, phase: str = "full") -> dict:
    """Run the manuscript review pipeline as a Celery task.

    Args:
        manuscript_path: Path to the manuscript file.
        phase: One of 'full', 'review_only', 'synthesis_only', 'editing_only'.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            _run_pipeline_async(self.request.id, manuscript_path, phase)
        )
    finally:
        loop.close()


async def _run_pipeline_async(task_id: str, manuscript_path: str, phase: str) -> dict:
    """Async implementation of the review pipeline."""
    from cati.llm.router import get_llm_provider
    from cati.manuscript_review.manuscript_loader import load_manuscript
    from cati.manuscript_review.models import ReviewSession
    from cati.manuscript_review.orchestrator import (
        run_phase1_review,
        run_phase2_editing,
        run_synthesis,
    )

    llm = get_llm_provider()
    chunks = load_manuscript(manuscript_path)

    session = ReviewSession(
        manuscript_path=manuscript_path,
        chunks=chunks,
    )

    # Update status
    _store_session(task_id, _session_to_dict(session))

    try:
        if phase in ("full", "review_only"):
            session = await run_phase1_review(llm, session)
            _store_session(task_id, _session_to_dict(session))
            log.info("manuscript_phase1_complete", task_id=task_id)

        if phase in ("full", "synthesis_only"):
            session = await run_synthesis(llm, session)
            _store_session(task_id, _session_to_dict(session))
            log.info("manuscript_synthesis_complete", task_id=task_id)

        if phase in ("full", "editing_only"):
            session = await run_phase2_editing(llm, session)
            _store_session(task_id, _session_to_dict(session))
            log.info("manuscript_phase2_complete", task_id=task_id)

    except Exception as exc:
        log.error("manuscript_pipeline_failed", task_id=task_id, error=str(exc))
        session.status = "failed"
        _store_session(task_id, _session_to_dict(session))
        raise

    return _session_to_dict(session)


def _session_to_dict(session) -> dict:
    """Convert a ReviewSession to a JSON-serializable dict."""
    result: dict[str, Any] = {
        "manuscript_path": session.manuscript_path,
        "status": session.status,
        "chunk_count": len(session.chunks),
        "total_words": sum(c.word_count for c in session.chunks),
    }

    # Agent reviews
    agent_reviews: dict[str, dict] = {}
    for key, review in session.agent_reviews.items():
        agent_reviews[key] = {
            "agent_name": review.agent_name,
            "agent_role": review.agent_role.value if hasattr(review.agent_role, "value") else str(review.agent_role),
            "raw_output": review.raw_output,
        }
    result["agent_reviews"] = agent_reviews

    # Synthesis
    if session.synthesis:
        result["synthesis"] = {
            "raw_output": session.synthesis.raw_output,
        }
    else:
        result["synthesis"] = None

    # Expert edits
    expert_edits: dict[str, dict] = {}
    for key, edit in session.expert_edits.items():
        expert_edits[key] = {
            "expert_name": edit.expert_name,
            "expert_role": edit.expert_role.value if hasattr(edit.expert_role, "value") else str(edit.expert_role),
            "raw_output": edit.raw_output,
        }
    result["expert_edits"] = expert_edits

    return result
