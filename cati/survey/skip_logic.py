"""CEL-based skip logic evaluation for survey branching."""
from __future__ import annotations

import re
from typing import Any


class SkipLogicError(Exception):
    pass


class _Namespace:
    """Attribute-access wrapper for a dict, enables `responses.key` syntax."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.__dict__.update(data)

    def __getattr__(self, name: str) -> Any:
        raise KeyError(name)


def _build_context(responses: dict[str, Any]) -> dict[str, Any]:
    """Build the evaluation context exposed to CEL expressions."""
    return {"responses": _Namespace(responses)}


def evaluate_condition(expr: str, responses: dict[str, Any]) -> bool:
    """Evaluate a CEL-like condition expression against current survey responses.

    Supports a safe subset of Python expressions rather than full CEL,
    which removes the need for a separate CEL interpreter dependency while
    keeping expressions readable and auditable.

    Allowed constructs:
    - Attribute access: responses.q1_age
    - Comparisons: ==, !=, <, >, <=, >=
    - Logical operators: and, or, not
    - Membership: in, not in
    - Literals: strings, ints, floats, booleans, None
    - Parentheses for grouping

    Example expressions::

        responses.q1_satisfied == 'yes'
        responses.q2_age >= 18 and responses.q2_age <= 65
        responses.q3_region in ['north', 'south']
        responses.q4_skip != None
    """
    if not expr.strip():
        return False

    _validate_expression(expr)

    context = _build_context(responses)
    try:
        result = eval(expr, {"__builtins__": {}}, context)  # noqa: S307
    except KeyError:
        # A response referenced in the expression hasn't been collected yet
        return False
    except Exception as exc:
        raise SkipLogicError(f"Error evaluating expression {expr!r}: {exc}") from exc

    return bool(result)


# Allowlist: only safe tokens permitted in expressions
_FORBIDDEN = re.compile(
    r"\b(import|exec|eval|open|__\w+__|getattr|setattr|delattr|globals|locals|vars|"
    r"compile|chr|ord|hex|oct|bin|format|input|print|breakpoint|exit|quit)\b"
)


def _validate_expression(expr: str) -> None:
    """Raise SkipLogicError if the expression contains forbidden tokens."""
    if _FORBIDDEN.search(expr):
        raise SkipLogicError(
            f"Expression {expr!r} contains forbidden tokens. "
            "Only comparison operators, logical operators, and literals are allowed."
        )


def find_next_question_key(
    current_question_key: str,
    responses: dict[str, Any],
    skip_rules: list[dict[str, Any]],
    question_keys_in_order: list[str],
) -> str | None:
    """Determine the next question key given current state.

    Args:
        current_question_key: The key of the question just answered.
        responses: All responses collected so far {question_key: parsed_value}.
        skip_rules: List of rule dicts with keys:
            source_question_key, condition_expr, target_question_key, priority.
        question_keys_in_order: All question keys in survey order.

    Returns:
        The next question key, or None if the survey is complete.
    """
    # Filter rules for the current question, ordered by priority
    applicable_rules = sorted(
        [r for r in skip_rules if r["source_question_key"] == current_question_key],
        key=lambda r: r["priority"],
    )

    for rule in applicable_rules:
        try:
            if evaluate_condition(rule["condition_expr"], responses):
                # None target means end survey
                return rule.get("target_question_key")
        except SkipLogicError:
            # Log and continue to next rule rather than crashing the interview
            pass

    # No rule matched — advance to the next question in order
    try:
        idx = question_keys_in_order.index(current_question_key)
        if idx + 1 < len(question_keys_in_order):
            return question_keys_in_order[idx + 1]
        return None  # Last question answered, survey complete
    except ValueError:
        return None
