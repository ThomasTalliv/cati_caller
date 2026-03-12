"""Build structured AnalysisReport objects from raw analysis data."""
from __future__ import annotations

import uuid
from typing import Any


def build_call_report(
    call_id: uuid.UUID,
    responses: list,
    summary: str,
    sentiments: dict[str, dict],
) -> dict[str, Any]:
    """Assemble a structured call analysis report."""
    response_details = []
    for r in responses:
        response_details.append({
            "question_key": r.question_key,
            "parsed_value": r.parsed_value,
            "is_refused": r.is_refused,
            "sentiment": sentiments.get(r.question_key),
        })

    refused_count = sum(1 for r in responses if r.is_refused)
    total = len(responses)

    return {
        "call_id": str(call_id),
        "summary": summary,
        "total_questions": total,
        "refused_questions": refused_count,
        "completion_rate": round((total - refused_count) / total, 3) if total > 0 else 0.0,
        "responses": response_details,
        "overall_sentiment": _aggregate_sentiment(sentiments),
    }


def _aggregate_sentiment(sentiments: dict[str, dict]) -> str:
    if not sentiments:
        return "neutral"
    labels = [s.get("label", "neutral") for s in sentiments.values()]
    pos = labels.count("positive")
    neg = labels.count("negative")
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"
