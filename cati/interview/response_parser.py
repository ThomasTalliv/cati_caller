"""Extract structured answers from raw respondent transcripts using LLM."""
from __future__ import annotations

import json
import re
from typing import Any

import structlog

from cati.llm.base import LLMProvider, Message
from cati.interview.prompts import RESPONSE_PARSER_PROMPT

log = structlog.get_logger(__name__)


class ResponseParser:
    """Parse free-form respondent speech into structured survey answer values."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def parse(
        self,
        raw_text: str,
        question_type: str,
        question_text: str,
        options: list[dict[str, Any]] | None = None,
        validation: dict[str, Any] | None = None,
    ) -> tuple[Any, bool, float]:
        """Parse respondent text into a structured value.

        Returns:
            Tuple of (parsed_value, is_refused, confidence).
            parsed_value is None if refused or unparseable.
            confidence is 0.0–1.0.
        """
        # Fast-path rules for clear refusals
        lower = raw_text.strip().lower()
        if _is_clear_refusal(lower):
            return None, True, 0.9

        # Fast-path for simple yes/no without LLM
        if question_type == "yes_no":
            result = _parse_yes_no_fast(lower)
            if result is not None:
                return result, False, 0.95

        # Use LLM for ambiguous or complex responses
        options_hint = ""
        if options:
            opts_str = ", ".join(
                f"{o.get('value')!r} ({o.get('label', '')})" for o in options
            )
            options_hint = f"Valid options: {opts_str}"
        if validation:
            options_hint += f"\nValidation constraints: {json.dumps(validation)}"

        prompt = RESPONSE_PARSER_PROMPT.format(
            question_text=question_text,
            question_type=question_type,
            options_hint=options_hint,
            raw_text=raw_text,
        )

        try:
            response_text = await self._llm.complete(
                [Message(role="user", content=prompt)],
                max_tokens=256,
            )
            return _parse_llm_response(response_text, question_type, validation)
        except Exception as exc:
            log.warning("response_parser_llm_failed", error=str(exc))
            return _fallback_parse(raw_text, question_type), False, 0.3


def _is_clear_refusal(text: str) -> bool:
    refusal_phrases = [
        "don't want to answer", "do not want to answer",
        "prefer not to", "no comment", "decline",
        "private", "personal", "none of your business",
        "i refuse", "skip", "pass",
    ]
    return any(phrase in text for phrase in refusal_phrases)


def _parse_yes_no_fast(text: str) -> str | None:
    yes_words = {"yes", "yeah", "yep", "yup", "sure", "correct", "affirmative", "definitely", "absolutely", "of course", "true"}
    no_words = {"no", "nope", "nah", "negative", "not", "false", "disagree"}
    words = set(re.findall(r"\b\w+\b", text))
    if words & yes_words:
        return "yes"
    if words & no_words:
        return "no"
    return None


def _parse_llm_response(
    response_text: str, question_type: str, validation: dict | None
) -> tuple[Any, bool, float]:
    # Extract JSON from response
    match = re.search(r"\{.*?\}", response_text, re.DOTALL)
    if not match:
        return None, False, 0.2

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return None, False, 0.1

    if data.get("refused"):
        return None, True, 0.85

    value = data.get("value")
    if value is None:
        return None, False, 0.5

    # Validate numeric ranges
    if question_type in ("numeric", "rating_scale") and validation and value is not None:
        try:
            num = float(value)
            min_val = validation.get("min")
            max_val = validation.get("max")
            if min_val is not None and num < min_val:
                return None, False, 0.4
            if max_val is not None and num > max_val:
                return None, False, 0.4
            value = int(num) if question_type == "rating_scale" else num
        except (TypeError, ValueError):
            return None, False, 0.3

    return value, False, 0.85


def _fallback_parse(text: str, question_type: str) -> Any:
    """Last-resort parser when LLM is unavailable."""
    if question_type == "open_ended":
        return text.strip()
    if question_type == "yes_no":
        result = _parse_yes_no_fast(text.lower())
        return result
    if question_type in ("numeric", "rating_scale"):
        numbers = re.findall(r"\b\d+(?:\.\d+)?\b", text)
        if numbers:
            return float(numbers[0]) if "." in numbers[0] else int(numbers[0])
    return None
