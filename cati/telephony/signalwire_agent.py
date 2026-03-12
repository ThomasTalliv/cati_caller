"""SignalWire Agents SDK integration — CATIAgent class.

The CATIAgent is a SignalWire AI agent that:
1. Receives inbound audio from the call
2. Passes it through STT → LangGraph interview engine → TTS
3. Streams synthesized audio back to the caller
4. Persists responses via the session manager
"""
from __future__ import annotations

import uuid
from typing import Any

import structlog

log = structlog.get_logger(__name__)


class CATIAgent:
    """AI CATI interviewer built on SignalWire Agents SDK.

    Instantiated per-call. Bridges SignalWire audio streams to the
    LangGraph interview engine.

    Requires: pip install signalwire-agents
    """

    def __init__(
        self,
        call_id: uuid.UUID,
        survey_id: uuid.UUID,
        phone_number: str,
    ) -> None:
        self.call_id = call_id
        self.survey_id = survey_id
        self.phone_number = phone_number
        self._state = None
        self._session_manager = None
        self._tts = None
        self._stt = None
        self._graph = None

    async def initialize(self) -> None:
        """Load survey, build initial InterviewState, warm up audio pipeline."""
        from cati.interview.graph import get_interview_graph
        from cati.interview.session_manager import get_session_manager
        from cati.interview.state import InterviewState
        from cati.voice.stt import get_stt_provider
        from cati.voice.tts import get_tts_provider
        from cati.db.session import get_session_factory
        from cati.db.repositories.survey_repo import SurveyRepository

        self._session_manager = get_session_manager()
        self._tts = get_tts_provider()
        self._stt = get_stt_provider()
        self._graph = get_interview_graph()

        # Load survey from DB
        factory = get_session_factory()
        async with factory() as session:
            repo = SurveyRepository(session)
            survey = await repo.get(self.survey_id)
            if survey is None:
                raise ValueError(f"Survey {self.survey_id} not found")

            questions = [
                {
                    "question_key": q.question_key,
                    "question_type": q.question_type,
                    "text": q.text,
                    "rephrasing": q.rephrasing,
                    "options": q.options,
                    "validation": q.validation,
                    "required": q.required,
                    "max_retries": q.max_retries,
                    "position": q.position,
                }
                for q in survey.questions
            ]
            skip_rules = [
                {
                    "source_question_key": r.source_question.question_key,
                    "condition_expr": r.condition_expr,
                    "target_question_key": r.target_question.question_key if r.target_question else None,
                    "priority": r.priority,
                }
                for r in survey.skip_rules
            ]

        self._state = InterviewState(
            call_id=self.call_id,
            survey_id=self.survey_id,
            questions=questions,
            skip_rules=skip_rules,
            question_keys_in_order=[q["question_key"] for q in questions],
            intro_text=survey.intro_text,
            outro_text=survey.outro_text,
            language=survey.language,
        )
        await self._session_manager.save(self._state)
        log.info("cati_agent_initialized", call_id=str(self.call_id), survey=str(self.survey_id))

    async def on_call_answered(self) -> bytes:
        """Called when the respondent answers. Returns greeting audio bytes."""
        from cati.interview.nodes import greet
        self._state = await greet(self._state)
        await self._session_manager.save(self._state)

        greeting_text = self._state.last_agent_text or ""
        audio = await self._tts.synthesize(greeting_text)
        log.info("call_answered_greeting_sent", call_id=str(self.call_id))
        return audio

    async def on_audio_received(self, audio_bytes: bytes) -> bytes | None:
        """Process a speech segment from the respondent.

        Args:
            audio_bytes: Complete utterance as 16-bit 16kHz PCM.

        Returns:
            Agent response audio bytes, or None if not ready.
        """
        if self._state is None or self._state.is_complete:
            return None

        # Transcribe
        result = await self._stt.transcribe(audio_bytes)
        if not result.text.strip():
            return None

        log.info("respondent_speech", call_id=str(self.call_id), text=result.text[:100])
        self._state.last_respondent_text = result.text

        # Run one step of the interview graph
        from cati.interview.nodes import listen_and_parse, ask_question
        self._state = await listen_and_parse(self._state)

        if self._state.next_node == "ask_question":
            self._state = await ask_question(self._state)
        elif self._state.next_node == "handle_refusal":
            from cati.interview.nodes import handle_refusal
            self._state = await handle_refusal(self._state)
            if self._state.next_node == "ask_question" and self._state.current_question_key:
                self._state = await ask_question(self._state)
        elif self._state.next_node == "handle_unclear":
            from cati.interview.nodes import handle_unclear
            self._state = await handle_unclear(self._state)
            self._state = await ask_question(self._state)
        elif self._state.next_node == "close_interview":
            from cati.interview.nodes import close_interview
            self._state = await close_interview(self._state)

        await self._session_manager.save(self._state)

        agent_text = self._state.last_agent_text or ""
        if not agent_text:
            return None

        audio = await self._tts.synthesize(agent_text)
        return audio

    async def on_call_ended(self) -> None:
        """Persist final responses to DB and trigger analysis."""
        if self._state is None:
            return

        await self._persist_responses()
        await self._session_manager.delete(self.call_id)
        log.info("call_ended_responses_persisted", call_id=str(self.call_id))

    async def _persist_responses(self) -> None:
        """Save all responses and transcript to the database."""
        from cati.db.session import get_session_factory
        from cati.db.repositories.response_repo import ResponseRepository
        from cati.db.repositories.call_repo import CallRepository
        from datetime import datetime, timezone

        factory = get_session_factory()
        async with factory() as session:
            call_repo = CallRepository(session)
            response_repo = ResponseRepository(session)

            await call_repo.update_status(
                self.call_id,
                "completed",
                ended_at=datetime.now(timezone.utc),
            )

            # Save transcript turns
            for turn in self._state.transcript:
                await response_repo.add_transcript_turn(
                    call_id=self.call_id,
                    speaker=turn.speaker,
                    text=turn.text,
                    audio_offset_ms=turn.audio_offset_ms,
                )

            # Save structured responses
            questions_by_key = {q["question_key"]: q for q in self._state.questions}
            for key, value in self._state.responses.items():
                q_def = questions_by_key.get(key)
                if q_def is None:
                    continue
                # We need the question DB ID - look it up separately
                # For now store with the question_key; a join query will resolve IDs
                from cati.db.repositories.survey_repo import SurveyRepository
                repo = SurveyRepository(session)
                survey = await repo.get(self.survey_id)
                if survey:
                    for q in survey.questions:
                        if q.question_key == key:
                            await response_repo.create_response(
                                call_id=self.call_id,
                                question_id=q.id,
                                question_key=key,
                                raw_transcript=None,
                                parsed_value=value,
                                is_refused=(value is None),
                            )
                            break


def build_signalwire_app(survey_id: uuid.UUID):
    """Build a SignalWire agent application for the given survey.

    Returns a configured agent that can be passed to the SignalWire SDK server.
    Requires: pip install signalwire-agents
    """
    try:
        from signalwire_agents import AgentBase  # type: ignore[import]
    except ImportError:
        raise RuntimeError("signalwire-agents is not installed. Run: pip install signalwire-agents")

    from config.settings import get_settings
    settings = get_settings()

    class SurveyCATIAgent(AgentBase):
        def __init__(self):
            super().__init__(
                name="CATI Survey Agent",
                route=f"/agent/survey/{survey_id}",
            )
            self.set_params({
                "ai_model": settings.llm.anthropic_model,
                "languages": [{"name": "English", "code": "en-US", "voice": "nova"}],
            })

        async def on_call_state(self, call_state, **kwargs):
            log.info("signalwire_call_state", state=call_state)

    return SurveyCATIAgent()
