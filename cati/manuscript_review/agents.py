"""Review agent runner — sends manuscript chunks to LLM agents."""
from __future__ import annotations

import asyncio

import structlog

from cati.llm.base import LLMProvider, Message
from cati.manuscript_review.models import (
    AgentReview,
    AgentRole,
    ExpertEdit,
    ExpertRole,
    ManuscriptChunk,
)
from cati.manuscript_review.prompts import (
    AGENT_DISPLAY_NAMES,
    EXPERT_DISPLAY_NAMES,
    get_expert_prompt,
    get_review_agent_prompt,
)

log = structlog.get_logger(__name__)

# Hook specialist only needs the first ~4000 words.
_HOOK_WORD_LIMIT = 4000

# Max tokens for review output — generous to allow detailed reviews.
_REVIEW_MAX_TOKENS = 8192

# Max tokens for expert editing output.
_EXPERT_MAX_TOKENS = 8192


def _truncate_to_words(text: str, max_words: int) -> str:
    """Truncate text to approximately *max_words* words."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def _build_chunk_context(chunks: list[ManuscriptChunk]) -> str:
    """Concatenate manuscript chunks into a single text block."""
    parts: list[str] = []
    for chunk in chunks:
        header = f"--- {chunk.chapter} (del {chunk.chunk_index + 1}/{chunk.total_chunks}) ---"
        parts.append(f"{header}\n{chunk.content}")
    return "\n\n".join(parts)


async def run_review_agent(
    llm: LLMProvider,
    role: AgentRole,
    chunks: list[ManuscriptChunk],
) -> AgentReview:
    """Run a single review agent on the provided manuscript chunks.

    For the hook specialist, only the first ~4000 words are sent.
    For all other agents, the full text (all chunks) is sent.
    """
    agent_name = AGENT_DISPLAY_NAMES[role]
    system_prompt = get_review_agent_prompt(role)

    manuscript_text = _build_chunk_context(chunks)

    if role == AgentRole.HOOK_SPECIALIST:
        manuscript_text = _truncate_to_words(manuscript_text, _HOOK_WORD_LIMIT)

    user_message = (
        f"Her er manuskriptet du skal gennemgå:\n\n{manuscript_text}\n\n"
        f"Udfør din review som {agent_name}."
    )

    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=user_message),
    ]

    log.info("review_agent_start", agent=role.value, chunks=len(chunks))
    raw_output = await llm.complete(messages, max_tokens=_REVIEW_MAX_TOKENS)
    log.info("review_agent_complete", agent=role.value, output_len=len(raw_output))

    return AgentReview(
        agent_role=role,
        agent_name=agent_name,
        overall_assessment="",  # Parsed from raw_output downstream
        critical_findings=[],
        significant_findings=[],
        observations=[],
        summary_points=[],
        raw_output=raw_output,
    )


async def run_all_review_agents(
    llm: LLMProvider,
    chunks: list[ManuscriptChunk],
) -> dict[str, AgentReview]:
    """Run all 5 review agents in parallel and return their reviews."""
    tasks = {
        role: run_review_agent(llm, role, chunks) for role in AgentRole
    }
    results: dict[str, AgentReview] = {}
    completed = await asyncio.gather(*tasks.values(), return_exceptions=True)

    for role, result in zip(tasks.keys(), completed):
        if isinstance(result, Exception):
            log.error("review_agent_failed", agent=role.value, error=str(result))
            results[role.value] = AgentReview(
                agent_role=role,
                agent_name=AGENT_DISPLAY_NAMES[role],
                overall_assessment="",
                critical_findings=[],
                significant_findings=[],
                observations=[],
                summary_points=[],
                raw_output=f"FEJL: {result}",
            )
        else:
            results[role.value] = result

    return results


async def run_expert_editor(
    llm: LLMProvider,
    role: ExpertRole,
    manuscript_text: str,
    review_context: str,
) -> ExpertEdit:
    """Run a single expert editor on manuscript text with review context.

    Args:
        llm: LLM provider instance.
        role: Which expert editor to run.
        manuscript_text: The manuscript text to edit.
        review_context: Relevant review comments from Phase 1 agents.
    """
    expert_name = EXPERT_DISPLAY_NAMES[role]
    system_prompt = get_expert_prompt(role)

    user_message = (
        f"Her er manuskriptteksten:\n\n{manuscript_text}\n\n"
        f"---\n\n"
        f"Her er review-kommentarerne:\n\n{review_context}\n\n"
        f"---\n\n"
        f"Udfør din redigering som {expert_name}."
    )

    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=user_message),
    ]

    log.info("expert_editor_start", expert=role.value)
    raw_output = await llm.complete(messages, max_tokens=_EXPERT_MAX_TOKENS)
    log.info("expert_editor_complete", expert=role.value, output_len=len(raw_output))

    return ExpertEdit(
        expert_role=role,
        expert_name=expert_name,
        changes=[],
        editor_notes="",
        raw_output=raw_output,
    )
