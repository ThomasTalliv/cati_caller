"""Thematic clustering of open-ended survey responses."""
from __future__ import annotations

from cati.llm.base import LLMProvider, Message


async def cluster_open_ended(texts: list[str], llm: LLMProvider) -> list[str]:
    """Identify recurring themes across multiple open-ended responses.

    Returns a list of theme strings (up to 5).
    """
    if not texts:
        return []

    sample = texts[:50]  # limit to 50 responses per cluster
    combined = "\n".join(f"- {t}" for t in sample)

    prompt = f"""You are analyzing open-ended survey responses. Identify up to 5 main themes.

Responses:
{combined[:3000]}

List the themes as a JSON array of strings. Return ONLY the JSON array.
Example: ["Theme 1", "Theme 2", "Theme 3"]"""

    import json
    import re

    try:
        raw = await llm.complete([Message(role="user", content=prompt)], max_tokens=200)
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    return []
