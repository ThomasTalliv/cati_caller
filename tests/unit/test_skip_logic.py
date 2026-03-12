"""Unit tests for skip logic evaluator."""
import pytest

from cati.survey.skip_logic import (
    SkipLogicError,
    evaluate_condition,
    find_next_question_key,
)


def test_simple_equality() -> None:
    assert evaluate_condition("responses.q1 == 'yes'", {"q1": "yes"}) is True
    assert evaluate_condition("responses.q1 == 'yes'", {"q1": "no"}) is False


def test_numeric_comparison() -> None:
    assert evaluate_condition("responses.q1 >= 18", {"q1": 18}) is True
    assert evaluate_condition("responses.q1 >= 18", {"q1": 17}) is False


def test_logical_and() -> None:
    cond = "responses.q1 == 'a' and responses.q2 == 'b'"
    assert evaluate_condition(cond, {"q1": "a", "q2": "b"}) is True
    assert evaluate_condition(cond, {"q1": "a", "q2": "x"}) is False


def test_in_operator() -> None:
    assert evaluate_condition("responses.q1 in ['a', 'b', 'c']", {"q1": "b"}) is True
    assert evaluate_condition("responses.q1 in ['a', 'b', 'c']", {"q1": "z"}) is False


def test_missing_key_returns_false() -> None:
    # A question that hasn't been answered yet should not crash
    result = evaluate_condition("responses.q1 == 'yes'", {})
    assert result is False


def test_forbidden_token_raises() -> None:
    with pytest.raises(SkipLogicError, match="forbidden"):
        evaluate_condition("import os", {})

    with pytest.raises(SkipLogicError, match="forbidden"):
        evaluate_condition("__import__('os')", {})


def test_find_next_default_order() -> None:
    keys = ["q1", "q2", "q3"]
    rules: list = []
    assert find_next_question_key("q1", {}, rules, keys) == "q2"
    assert find_next_question_key("q2", {}, rules, keys) == "q3"
    assert find_next_question_key("q3", {}, rules, keys) is None


def test_find_next_skip_rule_matches() -> None:
    keys = ["q1", "q2", "q3"]
    rules = [
        {
            "source_question_key": "q1",
            "condition_expr": "responses.q1 == 'skip'",
            "target_question_key": "q3",
            "priority": 0,
        }
    ]
    result = find_next_question_key("q1", {"q1": "skip"}, rules, keys)
    assert result == "q3"


def test_find_next_skip_rule_end_survey() -> None:
    keys = ["q1", "q2"]
    rules = [
        {
            "source_question_key": "q1",
            "condition_expr": "responses.q1 == 'no'",
            "target_question_key": None,
            "priority": 0,
        }
    ]
    result = find_next_question_key("q1", {"q1": "no"}, rules, keys)
    assert result is None


def test_find_next_rule_priority_order() -> None:
    keys = ["q1", "q2", "q3", "q4"]
    rules = [
        {
            "source_question_key": "q1",
            "condition_expr": "responses.q1 == 'a'",
            "target_question_key": "q4",
            "priority": 1,  # lower priority
        },
        {
            "source_question_key": "q1",
            "condition_expr": "responses.q1 == 'a'",
            "target_question_key": "q3",
            "priority": 0,  # higher priority (evaluated first)
        },
    ]
    result = find_next_question_key("q1", {"q1": "a"}, rules, keys)
    assert result == "q3"
