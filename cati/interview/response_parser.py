"""Extract structured answers from raw respondent transcripts.

Fast-path rules handle the majority of responses without any LLM call:
  - Clear refusals          → always fast-path
  - open_ended questions    → always fast-path (record transcript as-is)
  - yes/no questions        → fast-path for unambiguous yes/no words
  - numeric/rating_scale    → fast-path when response contains a single clear number
  - single_choice           → fast-path when response matches exactly one option

Only genuinely ambiguous responses fall through to the LLM, keeping
LLM usage below ~10% of answers for typical survey question mixes.
"""
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
        lower = raw_text.strip().lower()

        # 1. Fast-path: clear refusals (all question types)
        if _is_clear_refusal(lower):
            return None, True, 0.9

        # 2. Fast-path: open-ended — store transcript verbatim; no LLM needed
        if question_type == "open_ended":
            return raw_text.strip(), False, 1.0

        # 3. Fast-path: yes/no
        if question_type == "yes_no":
            result = _parse_yes_no_fast(lower)
            if result is not None:
                return result, False, 0.95

        # 4. Fast-path: numeric / rating_scale — extract first unambiguous number
        if question_type in ("numeric", "rating_scale"):
            result = _parse_numeric_fast(lower, validation)
            if result is not None:
                return result, False, 0.92

        # 5. Fast-path: single_choice — match against option labels/values
        if question_type == "single_choice" and options:
            result = _parse_single_choice_fast(lower, options)
            if result is not None:
                return result, False, 0.92

        # 6. LLM fallback for ambiguous responses
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
            log.debug("response_parser_llm_used", question_type=question_type)
            return _parse_llm_response(response_text, question_type, validation)
        except Exception as exc:
            log.warning("response_parser_llm_failed", error=str(exc))
            return _fallback_parse(raw_text, question_type), False, 0.3


# ── Fast-path helpers ──────────────────────────────────────────────────────────

def _is_clear_refusal(text: str) -> bool:
    refusal_phrases = [
        "don't want to answer", "do not want to answer",
        "prefer not to", "no comment", "decline",
        "private", "personal", "none of your business",
        "i refuse", "skip", "pass",
        "vil ikke svare", "ønsker ikke", "ingen kommentar",  # Danish/Norwegian
        "ne veux pas répondre", "je refuse",                  # French
        "möchte nicht antworten",                             # German
        "no quiero responder",                                # Spanish
    ]
    return any(phrase in text for phrase in refusal_phrases)


def _parse_yes_no_fast(text: str) -> str | None:
    yes_words = {
        "yes", "yeah", "yep", "yup", "sure", "correct",
        "affirmative", "definitely", "absolutely", "of course", "true",
        # European
        "ja", "oui", "sí", "si", "sim", "sì",
    }
    no_words = {
        "no", "nope", "nah", "negative", "not", "false", "disagree",
        # European
        "nein", "non", "não", "nee",
    }
    words = set(re.findall(r"\b\w+\b", text))
    if words & yes_words and not words & no_words:
        return "yes"
    if words & no_words and not words & yes_words:
        return "no"
    return None


def _parse_numeric_fast(
    text: str, validation: dict[str, Any] | None
) -> int | float | None:
    """Extract the first number from text; validate against min/max if set.

    Returns None when the text contains more than one distinct number
    (ambiguous) or the number is out of range.
    """
    numbers = re.findall(r"\b\d+(?:[.,]\d+)?\b", text)
    if len(numbers) != 1:
        # Zero or multiple numbers → ambiguous, let LLM decide
        return None

    raw = numbers[0].replace(",", ".")
    try:
        num = float(raw)
    except ValueError:
        return None

    if validation:
        min_val = validation.get("min")
        max_val = validation.get("max")
        if min_val is not None and num < min_val:
            return None
        if max_val is not None and num > max_val:
            return None

    # Return int when the number has no fractional part
    return int(num) if num == int(num) else num


def _parse_single_choice_fast(
    text: str, options: list[dict[str, Any]]
) -> Any | None:
    """Match respondent text against option labels and values.

    Returns the option *value* when exactly one option matches.
    """
    matched: list[Any] = []
    for opt in options:
        label = str(opt.get("label") or "").lower()
        spoken = str(opt.get("spoken_label") or "").lower()
        value = str(opt.get("value") or "").lower()
        for candidate in (label, spoken, value):
            if candidate and candidate in text and opt.get("value") not in matched:
                matched.append(opt.get("value"))
                break

    if len(matched) == 1:
        return matched[0]
    return None  # 0 or >1 matches → let LLM decide


# ── LLM response decoder ───────────────────────────────────────────────────────

def _parse_llm_response(
    response_text: str, question_type: str, validation: dict | None
) -> tuple[Any, bool, float]:
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
        return _parse_yes_no_fast(text.lower())
    if question_type in ("numeric", "rating_scale"):
        return _parse_numeric_fast(text.lower(), None)
    return None
