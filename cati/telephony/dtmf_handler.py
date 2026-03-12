"""DTMF touch-tone fallback for numeric and choice questions."""
from __future__ import annotations

from typing import Any


def dtmf_to_value(
    digits: str,
    question_type: str,
    options: list[dict[str, Any]] | None = None,
    validation: dict[str, Any] | None = None,
) -> tuple[Any, bool]:
    """Convert DTMF digit string to a structured answer value.

    Returns:
        (value, is_valid) — value is None if invalid.
    """
    digits = digits.strip()
    if not digits:
        return None, False

    if question_type == "yes_no":
        if digits == "1":
            return "yes", True
        if digits == "2":
            return "no", True
        return None, False

    if question_type in ("numeric", "rating_scale"):
        try:
            num = int(digits)
        except ValueError:
            return None, False
        if validation:
            min_val = validation.get("min")
            max_val = validation.get("max")
            if min_val is not None and num < min_val:
                return None, False
            if max_val is not None and num > max_val:
                return None, False
        return num, True

    if question_type == "single_choice" and options:
        idx = int(digits) - 1 if digits.isdigit() else -1
        if 0 <= idx < len(options):
            return options[idx].get("value"), True
        return None, False

    return None, False


def build_dtmf_prompt(question_type: str, options: list[dict[str, Any]] | None) -> str:
    """Build a spoken prompt explaining DTMF input options."""
    if question_type == "yes_no":
        return "Press 1 for yes, or press 2 for no."

    if question_type == "single_choice" and options:
        parts = [f"Press {i+1} for {o.get('spoken_label') or o.get('label')}" for i, o in enumerate(options)]
        return ". ".join(parts) + "."

    if question_type in ("numeric", "rating_scale"):
        return "Please enter your answer using the keypad, then press pound."

    return ""
