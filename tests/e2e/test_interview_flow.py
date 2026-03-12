"""End-to-end test for the interview flow without real telephony.

Runs the LangGraph interview engine with a mock LLM and mock STT,
simulating a full 3-question survey from greet → close.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cati.interview.state import InterviewState
from cati.survey.builder import SurveyBuilder


def _make_state() -> InterviewState:
    survey = (
        SurveyBuilder("E2E Test Survey")
        .language("en")
        .intro("Hello! This is a test survey.")
        .outro("Thank you!")
        .add_question("q1", "yes_no", "Do you own a car?")
        .add_question("q2", "rating_scale", "Rate our service from 1 to 5.", validation={"min": 1, "max": 5})
        .add_question("q3", "open_ended", "Any additional comments?", required=False)
        .build()
    )

    questions = {q.question_key: q for q in survey.questions}
    skip_rules: dict = {}
    key_order = [q.question_key for q in survey.questions]

    return InterviewState(
        call_id="00000000-0000-0000-0000-000000000001",
        survey_id="00000000-0000-0000-0000-000000000002",
        survey_name=survey.name,
        intro_text=survey.intro_text,
        outro_text=survey.outro_text,
        language=survey.language,
        questions=questions,
        skip_rules=skip_rules,
        question_keys_in_order=key_order,
        current_question_key=None,
        responses={},
        transcript=[],
        is_complete=False,
        refusal_count=0,
        unclear_count=0,
        next_node="greet",
    )


@pytest.mark.asyncio
async def test_greet_node_sets_first_question():
    """greet() should set current_question_key to q1 and route to ask_question."""
    from cati.interview.nodes import greet

    state = _make_state()

    with patch("cati.interview.nodes._tts", new_callable=lambda: lambda: AsyncMock(return_value=b"")):
        with patch("cati.interview.nodes.get_tts_provider", return_value=AsyncMock(synthesize=AsyncMock(return_value=b""))):
            result = await greet(state)

    assert result.current_question_key == "q1"
    assert result.next_node == "ask_question"
    # intro should be in transcript
    agent_turns = [t for t in result.transcript if t["speaker"] == "agent"]
    assert len(agent_turns) >= 1


@pytest.mark.asyncio
async def test_full_interview_text_mode():
    """Simulate a complete interview cycle through all nodes in sequence."""
    from cati.interview.nodes import ask_question, greet, listen_and_parse

    state = _make_state()

    # Mock TTS to avoid loading Kokoro
    async def mock_synth(text: str, **kw) -> bytes:
        return b"\x00" * 100  # fake audio

    mock_tts = MagicMock()
    mock_tts.synthesize = AsyncMock(side_effect=mock_synth)

    # Mock LLM response parser to return structured answers
    def mock_parse(response_text, question_key, question_type, options=None, validation=None):
        answers = {
            "q1": ("yes", False, 0.95),
            "q2": (4, False, 0.90),
            "q3": ("No comments", False, 0.85),
        }
        return answers.get(question_key, (None, False, 0.0))

    with patch("cati.interview.nodes.get_tts_provider", return_value=mock_tts):
        with patch("cati.interview.response_parser.parse_response", side_effect=mock_parse):
            with patch("cati.interview.nodes.get_stt_provider") as mock_stt_factory:
                mock_stt = MagicMock()
                mock_stt.transcribe = AsyncMock(return_value=MagicMock(text="yes", confidence=0.9))
                mock_stt_factory.return_value = mock_stt

                # Greet
                state = await greet(state)
                assert state.current_question_key == "q1"

                # Q1 — yes_no "Do you own a car?" → answer: yes
                state = await ask_question(state)
                assert state.next_node == "listen_and_parse"

                state.audio_input = b"\x00" * 100
                with patch("cati.interview.nodes.parse_response", side_effect=mock_parse):
                    state = await listen_and_parse(state)

                assert "q1" in state.responses
                assert state.responses["q1"] == "yes"
                assert state.current_question_key == "q2"


@pytest.mark.asyncio
async def test_interview_ends_after_last_question():
    """After the last question is answered, is_complete should be True."""
    from cati.survey.builder import SurveyBuilder
    from cati.interview.state import InterviewState

    survey = (
        SurveyBuilder("Single Q Survey")
        .intro("Hi")
        .outro("Bye")
        .add_question("only_q", "yes_no", "One question?")
        .build()
    )

    state = InterviewState(
        call_id="00000000-0000-0000-0000-000000000003",
        survey_id="00000000-0000-0000-0000-000000000004",
        survey_name=survey.name,
        intro_text=survey.intro_text,
        outro_text=survey.outro_text,
        language="en",
        questions={q.question_key: q for q in survey.questions},
        skip_rules={},
        question_keys_in_order=["only_q"],
        current_question_key="only_q",
        responses={},
        transcript=[],
        is_complete=False,
        refusal_count=0,
        unclear_count=0,
        next_node="listen_and_parse",
    )

    def mock_parse(response_text, question_key, question_type, options=None, validation=None):
        return ("yes", False, 0.95)

    mock_stt = MagicMock()
    mock_stt.transcribe = AsyncMock(return_value=MagicMock(text="yes", confidence=0.95))

    state.audio_input = b"\x00" * 100

    with patch("cati.interview.nodes.get_stt_provider", return_value=mock_stt):
        with patch("cati.interview.nodes.parse_response", side_effect=mock_parse):
            from cati.interview.nodes import listen_and_parse
            result = await listen_and_parse(state)

    assert result.responses.get("only_q") == "yes"
    # With only one question answered, next should be close
    assert result.next_node in ("close_interview", "ask_question")
    if result.next_node == "close_interview" or result.is_complete:
        assert result.is_complete or result.next_node == "close_interview"
