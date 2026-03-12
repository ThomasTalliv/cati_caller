"""LangGraph node functions for the CATI interview state machine."""
from __future__ import annotations

import random
from typing import Any

import structlog

from cati.interview.prompts import (
    CLOSING_TEMPLATE,
    GREETING_TEMPLATES,
    REFUSAL_RESPONSE_TEMPLATES,
    UNCLEAR_RESPONSE_TEMPLATES,
)
from cati.interview.state import InterviewState
from cati.survey.renderer import SurveyRenderer

log = structlog.get_logger(__name__)


# ── Node functions ─────────────────────────────────────────────────────────────

async def greet(state: InterviewState) -> InterviewState:
    """Deliver the survey introduction and set the first question."""
    intro = state.intro_text or "Thank you for taking our survey."
    q_count = len(state.questions)
    greeting = random.choice(GREETING_TEMPLATES).format(
        intro_text=intro, question_count=q_count
    )
    state.add_agent_turn(greeting)
    state.last_agent_text = greeting

    # Set the first question
    if state.question_keys_in_order:
        state.current_question_key = state.question_keys_in_order[0]
        state.next_node = "ask_question"
    else:
        state.is_complete = True
        state.next_node = "close_interview"

    return state


async def ask_question(state: InterviewState) -> InterviewState:
    """Speak the current question to the respondent."""
    renderer = SurveyRenderer(
        questions=state.questions,
        skip_rules=state.skip_rules,
    )
    if state.current_question_key is None:
        state.is_complete = True
        state.next_node = "close_interview"
        return state

    use_rephrasing = state.retry_count > 0
    try:
        question_text = renderer.render_question_text(
            state.current_question_key, use_rephrasing=use_rephrasing
        )
    except KeyError:
        log.error("unknown_question_key", key=state.current_question_key)
        state.is_complete = True
        state.next_node = "close_interview"
        return state

    state.add_agent_turn(question_text)
    state.next_node = "listen_and_parse"
    return state


async def listen_and_parse(
    state: InterviewState,
    *,
    llm=None,
) -> InterviewState:
    """Parse the respondent's answer and record it."""
    from cati.interview.response_parser import ResponseParser
    from cati.llm.router import get_llm_provider

    raw_text = state.last_respondent_text or ""
    if not raw_text.strip():
        state.next_node = "handle_unclear"
        return state

    state.add_respondent_turn(raw_text)

    q_def = state.current_question_def()
    if q_def is None:
        state.next_node = "close_interview"
        return state

    parser = ResponseParser(llm or get_llm_provider())
    value, is_refused, confidence = await parser.parse(
        raw_text=raw_text,
        question_type=q_def["question_type"],
        question_text=q_def["text"],
        options=q_def.get("options"),
        validation=q_def.get("validation"),
    )

    if is_refused:
        state.refusal_count += 1
        state.next_node = "handle_refusal"
        return state

    if value is None and state.retry_count < q_def.get("max_retries", 2):
        state.retry_count += 1
        state.next_node = "handle_unclear"
        return state

    # Record the response
    state.record_response(state.current_question_key, value)
    state.retry_count = 0

    # Advance to next question
    renderer = SurveyRenderer(questions=state.questions, skip_rules=state.skip_rules)
    next_key = renderer.next_question_key(state.current_question_key, state.responses)
    state.current_question_key = next_key

    if next_key is None:
        state.next_node = "close_interview"
    else:
        state.next_node = "ask_question"

    return state


async def handle_refusal(state: InterviewState) -> InterviewState:
    """Acknowledge refusal, skip question, advance."""
    msg = random.choice(REFUSAL_RESPONSE_TEMPLATES)
    state.add_agent_turn(msg)

    q_def = state.current_question_def()
    if q_def and not q_def.get("required", True):
        # Skip to next question
        renderer = SurveyRenderer(questions=state.questions, skip_rules=state.skip_rules)
        next_key = renderer.next_question_key(state.current_question_key, state.responses)
        state.current_question_key = next_key
        state.retry_count = 0
        state.next_node = "ask_question" if next_key else "close_interview"
    else:
        # Required question refused — record null and advance
        if state.current_question_key:
            state.record_response(state.current_question_key, None)
        renderer = SurveyRenderer(questions=state.questions, skip_rules=state.skip_rules)
        next_key = renderer.next_question_key(state.current_question_key or "", state.responses)
        state.current_question_key = next_key
        state.retry_count = 0
        state.next_node = "ask_question" if next_key else "close_interview"

    return state


async def handle_unclear(state: InterviewState) -> InterviewState:
    """Ask the respondent to repeat or clarify."""
    msg = random.choice(UNCLEAR_RESPONSE_TEMPLATES)
    state.add_agent_turn(msg)
    state.next_node = "ask_question"
    return state


async def close_interview(state: InterviewState) -> InterviewState:
    """Deliver the closing message and mark the interview complete."""
    outro = state.outro_text or "Thank you for your time!"
    closing = CLOSING_TEMPLATE.format(outro_text=outro)
    state.add_agent_turn(closing)
    state.is_complete = True
    state.next_node = None
    return state
