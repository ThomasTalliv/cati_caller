"""Post-call AI analysis orchestrator."""
from __future__ import annotations

import uuid
from typing import Any

import structlog

log = structlog.get_logger(__name__)


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
        """Run full analysis for one completed call. Returns the report dict."""
        from cati.db.session import get_session_factory
        from cati.db.repositories.response_repo import ResponseRepository
        from cati.db.repositories.call_repo import CallRepository
        from cati.analysis.summarizer import summarize_transcript
        from cati.analysis.sentiment import analyze_sentiment
        from cati.analysis.report_builder import build_call_report
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

        llm = self._get_llm()

        # 1. Summarize transcript
        transcript_text = "\n".join(
            f"[{t.speaker.upper()}] {t.text}" for t in transcript
        )
        summary = await summarize_transcript(transcript_text, llm)

        # 2. Sentiment per response
        sentiments = {}
        for r in responses:
            if r.raw_transcript:
                sentiments[r.question_key] = await analyze_sentiment(r.raw_transcript, llm)

        # 3. Build report
        report_content = build_call_report(
            call_id=call_id,
            responses=responses,
            summary=summary,
            sentiments=sentiments,
        )

        # 4. Persist to DB
        async with factory() as session:
            from sqlalchemy import select
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
        from cati.db.repositories.call_repo import CallRepository
        from cati.analysis.categorizer import cluster_open_ended
        from cati.survey.models import AnalysisReport

        factory = get_session_factory()
        async with factory() as session:
            resp_repo = ResponseRepository(session)
            all_responses = await resp_repo.list_for_survey(survey_id)

        llm = self._get_llm()

        # Group open-ended responses by question
        open_ended: dict[str, list[str]] = {}
        for r in all_responses:
            if r.raw_transcript:
                open_ended.setdefault(r.question_key, []).append(r.raw_transcript)

        themes: dict[str, list[str]] = {}
        for key, texts in open_ended.items():
            themes[key] = await cluster_open_ended(texts, llm)

        # Numeric aggregates
        numeric_stats: dict[str, dict] = {}
        numeric_values: dict[str, list[float]] = {}
        for r in all_responses:
            if isinstance(r.parsed_value, (int, float)):
                numeric_values.setdefault(r.question_key, []).append(float(r.parsed_value))
        for key, vals in numeric_values.items():
            numeric_stats[key] = {
                "count": len(vals),
                "mean": sum(vals) / len(vals),
                "min": min(vals),
                "max": max(vals),
            }

        report_content = {
            "survey_id": str(survey_id),
            "total_responses": len(all_responses),
            "open_ended_themes": themes,
            "numeric_stats": numeric_stats,
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
