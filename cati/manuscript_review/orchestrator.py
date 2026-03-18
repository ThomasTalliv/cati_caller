"""Orchestrator — coordinates the full two-phase review and editing workflow."""
from __future__ import annotations

from pathlib import Path

import structlog

from cati.llm.base import LLMProvider
from cati.manuscript_review.agents import (
    run_all_review_agents,
    run_expert_editor,
)
from cati.manuscript_review.manuscript_loader import load_manuscript
from cati.manuscript_review.models import (
    AgentRole,
    ExpertRole,
    ReviewSession,
)
from cati.manuscript_review.synthesis import synthesize_reviews

log = structlog.get_logger(__name__)


def _collect_review_context_for_expert(
    session: ReviewSession,
    expert: ExpertRole,
) -> str:
    """Gather relevant review comments for a specific expert editor.

    Each expert receives reviews from the agents most relevant to their work:
    - Opening Architect: Hook-specialist, Narrative, Target Audience
    - Flow Surgeon: Structure, Target Audience, Narrative
    - Voice Polisher: Fact Checker, Target Audience
    """
    relevance_map: dict[ExpertRole, list[str]] = {
        ExpertRole.OPENING_ARCHITECT: [
            AgentRole.HOOK_SPECIALIST.value,
            AgentRole.NARRATIVE_EDITOR.value,
            AgentRole.TARGET_AUDIENCE.value,
        ],
        ExpertRole.FLOW_SURGEON: [
            AgentRole.STRUCTURE_EDITOR.value,
            AgentRole.TARGET_AUDIENCE.value,
            AgentRole.NARRATIVE_EDITOR.value,
        ],
        ExpertRole.VOICE_POLISHER: [
            AgentRole.FACT_CHECKER.value,
            AgentRole.TARGET_AUDIENCE.value,
        ],
    }

    relevant_roles = relevance_map.get(expert, [])
    parts: list[str] = []

    # Include the synthesis if available
    if session.synthesis:
        parts.append(
            f"=== REVIEW-SYNTESE ===\n\n{session.synthesis.raw_output}\n"
        )

    for role_key in relevant_roles:
        review = session.agent_reviews.get(role_key)
        if review:
            parts.append(
                f"=== {review.agent_name} ===\n\n{review.raw_output}\n"
            )

    return "\n\n".join(parts) if parts else "Ingen review-kommentarer tilgængelige."


async def run_phase1_review(
    llm: LLMProvider,
    session: ReviewSession,
) -> ReviewSession:
    """Phase 1: Run all 5 review agents in parallel.

    Each agent reads the manuscript (or a portion of it) and produces
    a structured review according to their specialty.
    """
    log.info("phase1_start", manuscript=session.manuscript_path)
    session.status = "reviewing"

    reviews = await run_all_review_agents(llm, session.chunks)
    session.agent_reviews = reviews

    log.info("phase1_complete", reviews=len(reviews))
    return session


async def run_synthesis(
    llm: LLMProvider,
    session: ReviewSession,
) -> ReviewSession:
    """Synthesis step: Combine all reviews into a prioritized action list."""
    log.info("synthesis_start")
    session.status = "synthesizing"

    synthesis = await synthesize_reviews(llm, session.agent_reviews)
    session.synthesis = synthesis

    log.info("synthesis_complete")
    return session


async def run_phase2_editing(
    llm: LLMProvider,
    session: ReviewSession,
) -> ReviewSession:
    """Phase 2: Run expert editors sequentially.

    The experts run in order:
    1. Opening Architect — rewrites the first ~4000 words
    2. Flow Surgeon — fixes transitions, removes repetition, tightens
    3. Voice Polisher — final language, tone, and consistency pass

    Each expert receives the manuscript text plus relevant review comments.
    """
    log.info("phase2_start")
    session.status = "editing"

    # Build full manuscript text from chunks
    full_text = "\n\n".join(chunk.content for chunk in session.chunks)

    # Expert editors run sequentially — each builds on the previous
    expert_order = [
        ExpertRole.OPENING_ARCHITECT,
        ExpertRole.FLOW_SURGEON,
        ExpertRole.VOICE_POLISHER,
    ]

    for expert_role in expert_order:
        review_context = _collect_review_context_for_expert(session, expert_role)

        # Opening architect only gets the first ~4000 words
        if expert_role == ExpertRole.OPENING_ARCHITECT:
            words = full_text.split()
            text_for_expert = " ".join(words[:4000])
        else:
            text_for_expert = full_text

        edit = await run_expert_editor(llm, expert_role, text_for_expert, review_context)
        session.expert_edits[expert_role.value] = edit

        log.info("expert_complete", expert=expert_role.value)

    session.status = "complete"
    log.info("phase2_complete", edits=len(session.expert_edits))
    return session


async def run_full_pipeline(
    llm: LLMProvider,
    manuscript_path: str | Path,
) -> ReviewSession:
    """Run the complete two-phase review pipeline.

    1. Load and chunk the manuscript
    2. Phase 1: 5 review agents run in parallel
    3. Synthesis: Combine and prioritize findings
    4. Phase 2: 3 expert editors run sequentially

    Args:
        llm: LLM provider for all agents.
        manuscript_path: Path to the manuscript file (.txt or .md).

    Returns:
        A ReviewSession containing all reviews, synthesis, and edits.
    """
    chunks = load_manuscript(manuscript_path)

    session = ReviewSession(
        manuscript_path=str(manuscript_path),
        chunks=chunks,
    )

    # Phase 1: Review
    session = await run_phase1_review(llm, session)

    # Synthesis
    session = await run_synthesis(llm, session)

    # Phase 2: Editing
    session = await run_phase2_editing(llm, session)

    return session
