"""Post-call AI analysis — optimised for minimal LLM token usage.

Cost optimisation vs. original design:
  Before: 1 summarise call + 1 sentiment call per response = N+1 LLM calls/interview
  After:  1 combined call that returns summary + all sentiments in one JSON response
          → saves ~7 LLM round trips per interview (≈ 87% fewer analysis calls)
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_COMBINED_ANALYSIS_PROMPT = """\
You are analysing a completed telephone survey interview.
Respond with a single JSON object — no markdown, no prose outside the JSON.

JSON schema:
{{
  "summary": "<2-3 sentence plain-language summary of the whole interview>",
  "overall_sentiment": "<positive|neutral|negative>",
  "per_question_sentiment": {{
    "<question_key>": "<positive|neutral|negative>"
  }},
  "key_themes": ["<theme1>", "<theme2>"],
  "completion_quality": "<complete|partial|refused>"
}}

Transcript:
{transcript}

Structured responses:
{responses_json}
"""

_CLUSTER_PROMPT = """\
You are analysing open-ended survey responses. Group them into 3-7 distinct themes.
Return ONLY a JSON array of theme strings, e.g. ["Price concerns", "Good service", ...].

Responses:
{texts}
"""


class CallAnalyzer:
    """Runs the full post-call analysis pipeline for a single call."""

    def __init__(self, llm=None) -> None:
        self._llm = llm

    def _get_llm(self):
        if self._llm is None:
            from cati.llm.router import get_llm_provider
            self._llm = get_llm_provider()
        return self._llm

    async def analyze_call(self, call_id: uuid.UUID) -> dict[str, Any]:
        """Run full analysis for one completed call in a SINGLE LLM call."""
        from cati.db.session import get_session_factory
        from cati.db.repositories.response_repo import ResponseRepository
        from cati.db.repositories.call_repo import CallRepository
        from cati.survey.models import AnalysisReport

        factory = get_session_factory()
        async with factory() as session:
            call_repo = CallRepository(session)
            resp_repo = ResponseRepository(session)
            call = await call_repo.get(call_id)
            if call is None:
                raise ValueError(f"Call {call_id} not found")
            responses = await resp_repo.list_for_call(call_id)
            transcript = await resp_repo.list_transcript(call_id)

        transcript_text = "\n".join(
            f"[{t.speaker.upper()}] {t.text}" for t in transcript
        )
        responses_json = json.dumps(
            [
                {
                    "question_key": r.question_key,
                    "parsed_value": r.parsed_value,
                    "is_refused": r.is_refused,
                    "raw": r.raw_transcript,
                }
                for r in responses
            ],
            ensure_ascii=False,
        )

        llm = self._get_llm()
        prompt = _COMBINED_ANALYSIS_PROMPT.format(
            transcript=transcript_text,
            responses_json=responses_json,
        )

        try:
            from cati.llm.base import Message
            raw = await llm.complete([Message(role="user", content=prompt)], max_tokens=512)
            report_content = _parse_analysis_json(raw)
        except Exception as exc:
            log.warning("analysis_llm_failed", call_id=str(call_id), error=str(exc))
            report_content = _fallback_report(responses)

        report_content["call_id"] = str(call_id)

        async with factory() as session:
            report = AnalysisReport(
                call_id=call_id,
                survey_id=call.survey_id,
                report_type="call_summary",
                llm_provider=llm.provider_name,
                llm_model=llm.model_name,
                content=report_content,
            )
            session.add(report)
            await session.commit()

        log.info("call_analysis_complete", call_id=str(call_id))
        return report_content

    async def analyze_survey(self, survey_id: uuid.UUID) -> dict[str, Any]:
        """Run aggregate analysis across all completed calls for a survey."""
        from cati.db.session import get_session_factory
        from cati.db.repositories.response_repo import ResponseRepository
        from cati.survey.models import AnalysisReport

        factory = get_session_factory()
        async with factory() as session:
            resp_repo = ResponseRepository(session)
            all_responses = await resp_repo.list_for_survey(survey_id)

        llm = self._get_llm()

        # Cluster open-ended responses per question (single LLM call per question key)
        open_ended: dict[str, list[str]] = {}
        for r in all_responses:
            if r.raw_transcript and not r.is_refused:
                open_ended.setdefault(r.question_key, []).append(r.raw_transcript)

        themes: dict[str, list[str]] = {}
        for key, texts in open_ended.items():
            themes[key] = await _cluster_open_ended(texts, llm)

        # Numeric aggregates — no LLM needed
        numeric_values: dict[str, list[float]] = {}
        for r in all_responses:
            if isinstance(r.parsed_value, (int, float)):
                numeric_values.setdefault(r.question_key, []).append(float(r.parsed_value))

        numeric_stats: dict[str, dict] = {}
        for key, vals in numeric_values.items():
            svals = sorted(vals)
            n = len(svals)
            numeric_stats[key] = {
                "count": n,
                "mean": round(sum(vals) / n, 2),
                "median": svals[n // 2],
                "min": min(vals),
                "max": max(vals),
                "std_dev": round(_std_dev(vals), 2),
            }

        # Yes/no distributions — no LLM needed
        yesno_dist: dict[str, dict] = {}
        for r in all_responses:
            if r.parsed_value in ("yes", "no"):
                dist = yesno_dist.setdefault(r.question_key, {"yes": 0, "no": 0, "refused": 0})
                dist[r.parsed_value] += 1
        for r in all_responses:
            if r.is_refused and r.question_key in yesno_dist:
                yesno_dist[r.question_key]["refused"] += 1

        report_content = {
            "survey_id": str(survey_id),
            "total_responses": len(all_responses),
            "open_ended_themes": themes,
            "numeric_stats": numeric_stats,
            "yes_no_distribution": yesno_dist,
        }

        async with factory() as session:
            report = AnalysisReport(
                survey_id=survey_id,
                report_type="survey_aggregate",
                llm_provider=llm.provider_name,
                llm_model=llm.model_name,
                content=report_content,
            )
            session.add(report)
            await session.commit()

        return report_content


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_analysis_json(raw: str) -> dict[str, Any]:
    """Extract JSON object from LLM output."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"summary": raw[:500], "parse_error": True}


def _fallback_report(responses) -> dict[str, Any]:
    """Minimal report when LLM is unavailable."""
    return {
        "summary": f"Interview completed with {len(responses)} responses.",
        "overall_sentiment": "neutral",
        "per_question_sentiment": {},
        "key_themes": [],
        "completion_quality": "complete" if responses else "partial",
    }


async def _cluster_open_ended(texts: list[str], llm) -> list[str]:
    """Cluster open-ended responses into themes using one LLM call."""
    if not texts:
        return []
    # Cap at 200 responses to stay within token limits
    sample = texts[:200]
    joined = "\n".join(f"- {t}" for t in sample)
    prompt = _CLUSTER_PROMPT.format(texts=joined)
    try:
        from cati.llm.base import Message
        raw = await llm.complete([Message(role="user", content=prompt)], max_tokens=256)
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as exc:
        log.warning("cluster_llm_failed", error=str(exc))
    return []


def _std_dev(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    mean = sum(vals) / len(vals)
    variance = sum((v - mean) ** 2 for v in vals) / len(vals)
    return variance ** 0.5
