"""Sentiment analysis for individual responses."""
from __future__ import annotations

from cati.llm.base import LLMProvider, Message


async def analyze_sentiment(text: str, llm: LLMProvider) -> dict:
    """Return sentiment analysis for a single response string.

    Returns dict with keys: label (positive/negative/neutral), score (0.0–1.0).
    """
    if not text.strip():
        return {"label": "neutral", "score": 0.5}

    prompt = f"""Analyze the sentiment of this survey response. Return JSON only.

Response: "{text[:500]}"

Return exactly: {{"label": "positive"|"negative"|"neutral", "score": 0.0-1.0}}"""

    import json
    import re

    try:
        raw = await llm.complete([Message(role="user", content=prompt)], max_tokens=60)
        match = re.search(r"\{.*?\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    return {"label": "neutral", "score": 0.5}
