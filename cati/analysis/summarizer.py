"""Transcript summarization."""
from __future__ import annotations

from cati.llm.base import LLMProvider, Message


async def summarize_transcript(transcript_text: str, llm: LLMProvider) -> str:
    """Summarize a call transcript into a concise paragraph."""
    if not transcript_text.strip():
        return ""

    prompt = f"""Summarize the following CATI survey interview transcript in 2-3 sentences.
Focus on the respondent's key opinions and answers. Be neutral and objective.

Transcript:
{transcript_text[:4000]}

Summary:"""

    return await llm.complete(
        [Message(role="user", content=prompt)],
        max_tokens=300,
    )
