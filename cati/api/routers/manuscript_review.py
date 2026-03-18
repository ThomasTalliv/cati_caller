"""API endpoints for the multiagent manuscript review system."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from cati.api.dependencies import require_api_key

router = APIRouter(
    prefix="/api/v1/manuscript-review",
    tags=["manuscript-review"],
    dependencies=[Depends(require_api_key)],
)

# In-memory session store (swap for Redis/DB in production).
_sessions: dict[str, dict] = {}


class StartReviewRequest(BaseModel):
    manuscript_path: str = Field(
        ..., description="Absolute path to the manuscript file (.txt or .md)"
    )
    phase: Literal["full", "review_only", "synthesis_only", "editing_only"] = Field(
        default="full",
        description="Which phase(s) to run. 'full' runs the complete pipeline.",
    )


class StartReviewResponse(BaseModel):
    session_id: str
    status: str
    message: str


class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    manuscript_path: str
    review_agents_completed: list[str]
    synthesis_available: bool
    expert_edits_completed: list[str]


class AgentReviewResponse(BaseModel):
    agent_name: str
    agent_role: str
    raw_output: str


class SynthesisResponse(BaseModel):
    raw_output: str


class ExpertEditResponse(BaseModel):
    expert_name: str
    expert_role: str
    raw_output: str


@router.post("/start", status_code=status.HTTP_202_ACCEPTED, response_model=StartReviewResponse)
async def start_review(request: StartReviewRequest) -> StartReviewResponse:
    """Start a manuscript review pipeline.

    Launches the multiagent review system. The pipeline runs asynchronously
    via Celery. Poll the status endpoint to track progress.
    """
    path = Path(request.manuscript_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Manuscript file not found: {request.manuscript_path}",
        )

    from cati.tasks.manuscript_tasks import run_manuscript_review

    task = run_manuscript_review.delay(request.manuscript_path, request.phase)
    session_id = task.id

    _sessions[session_id] = {
        "status": "queued",
        "manuscript_path": request.manuscript_path,
        "phase": request.phase,
    }

    return StartReviewResponse(
        session_id=session_id,
        status="queued",
        message=f"Review pipeline '{request.phase}' started for {path.name}",
    )


@router.get("/sessions/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str) -> SessionStatusResponse:
    """Get the current status of a review session."""
    from cati.tasks.manuscript_tasks import get_session_data

    session_data = get_session_data(session_id)
    if session_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    return SessionStatusResponse(
        session_id=session_id,
        status=session_data.get("status", "unknown"),
        manuscript_path=session_data.get("manuscript_path", ""),
        review_agents_completed=list(session_data.get("agent_reviews", {}).keys()),
        synthesis_available=session_data.get("synthesis") is not None,
        expert_edits_completed=list(session_data.get("expert_edits", {}).keys()),
    )


@router.get("/sessions/{session_id}/reviews/{agent_role}", response_model=AgentReviewResponse)
async def get_agent_review(session_id: str, agent_role: str) -> AgentReviewResponse:
    """Get the review output from a specific agent."""
    from cati.tasks.manuscript_tasks import get_session_data

    session_data = get_session_data(session_id)
    if session_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    reviews = session_data.get("agent_reviews", {})
    review = reviews.get(agent_role)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review not found for agent: {agent_role}",
        )

    return AgentReviewResponse(
        agent_name=review.get("agent_name", agent_role),
        agent_role=agent_role,
        raw_output=review.get("raw_output", ""),
    )


@router.get("/sessions/{session_id}/synthesis", response_model=SynthesisResponse)
async def get_synthesis(session_id: str) -> SynthesisResponse:
    """Get the review synthesis."""
    from cati.tasks.manuscript_tasks import get_session_data

    session_data = get_session_data(session_id)
    if session_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    synthesis = session_data.get("synthesis")
    if synthesis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synthesis not yet available",
        )

    return SynthesisResponse(raw_output=synthesis.get("raw_output", ""))


@router.get("/sessions/{session_id}/edits/{expert_role}", response_model=ExpertEditResponse)
async def get_expert_edit(session_id: str, expert_role: str) -> ExpertEditResponse:
    """Get the output from a specific expert editor."""
    from cati.tasks.manuscript_tasks import get_session_data

    session_data = get_session_data(session_id)
    if session_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    edits = session_data.get("expert_edits", {})
    edit = edits.get(expert_role)
    if edit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edit not found for expert: {expert_role}",
        )

    return ExpertEditResponse(
        expert_name=edit.get("expert_name", expert_role),
        expert_role=expert_role,
        raw_output=edit.get("raw_output", ""),
    )
