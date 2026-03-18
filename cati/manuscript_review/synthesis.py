"""Review synthesis — combines all agent reviews into a prioritized action list."""
from __future__ import annotations

import structlog

from cati.llm.base import LLMProvider, Message
from cati.manuscript_review.models import AgentReview, ReviewSynthesis
from cati.manuscript_review.prompts import SYNTHESIS_PROMPT

log = structlog.get_logger(__name__)

_SYNTHESIS_MAX_TOKENS = 8192


def _build_synthesis_input(reviews: dict[str, AgentReview]) -> str:
    """Concatenate all agent reviews into a single input for the synthesis prompt."""
    parts: list[str] = []
    for role_key, review in reviews.items():
        parts.append(
            f"=== REVIEW FRA: {review.agent_name} ({role_key}) ===\n\n"
            f"{review.raw_output}\n"
        )
    return "\n\n".join(parts)


async def synthesize_reviews(
    llm: LLMProvider,
    reviews: dict[str, AgentReview],
) -> ReviewSynthesis:
    """Combine all review agent outputs into a single prioritized synthesis.

    This is the bridge between Phase 1 (review) and Phase 2 (editing).
    The synthesis prompt instructs the LLM to deduplicate, resolve conflicts,
    and assign P1/P2/P3 priorities to each finding.
    """
    review_input = _build_synthesis_input(reviews)

    messages = [
        Message(role="system", content=SYNTHESIS_PROMPT),
        Message(
            role="user",
            content=(
                f"Her er de 5 review-dokumenter du skal syntetisere:\n\n"
                f"{review_input}\n\n"
                f"Lav nu en samlet Review-Syntese med prioriteret handlingsliste."
            ),
        ),
    ]

    log.info("synthesis_start", review_count=len(reviews))
    raw_output = await llm.complete(messages, max_tokens=_SYNTHESIS_MAX_TOKENS)
    log.info("synthesis_complete", output_len=len(raw_output))

    return ReviewSynthesis(
        p1_critical=[],
        p2_significant=[],
        p3_polish=[],
        raw_output=raw_output,
    )
