"""Unit tests for DTMF handler."""
import pytest

from cati.telephony.dtmf_handler import build_dtmf_prompt, dtmf_to_value


class TestDtmfToValue:
    def test_yes_no_press_1(self):
        value, valid = dtmf_to_value("1", "yes_no")
        assert value == "yes"
        assert valid is True

    def test_yes_no_press_2(self):
        value, valid = dtmf_to_value("2", "yes_no")
        assert value == "no"
        assert valid is True

    def test_yes_no_invalid(self):
        value, valid = dtmf_to_value("3", "yes_no")
        assert value is None
        assert valid is False

    def test_numeric_in_range(self):
        value, valid = dtmf_to_value("42", "numeric", validation={"min": 0, "max": 100})
        assert value == 42
        assert valid is True

    def test_numeric_below_min(self):
        value, valid = dtmf_to_value("0", "numeric", validation={"min": 1, "max": 5})
        assert value is None
        assert valid is False

    def test_numeric_above_max(self):
        value, valid = dtmf_to_value("6", "numeric", validation={"min": 1, "max": 5})
        assert value is None
        assert valid is False

    def test_rating_scale_valid(self):
        value, valid = dtmf_to_value("3", "rating_scale", validation={"min": 1, "max": 5})
        assert value == 3
        assert valid is True

    def test_single_choice_first_option(self):
        options = [{"value": "red"}, {"value": "blue"}, {"value": "green"}]
        value, valid = dtmf_to_value("1", "single_choice", options=options)
        assert value == "red"
        assert valid is True

    def test_single_choice_out_of_range(self):
        options = [{"value": "red"}, {"value": "blue"}]
        value, valid = dtmf_to_value("5", "single_choice", options=options)
        assert value is None
        assert valid is False

    def test_empty_digits(self):
        value, valid = dtmf_to_value("", "yes_no")
        assert value is None
        assert valid is False

    def test_non_numeric_for_numeric_type(self):
        value, valid = dtmf_to_value("abc", "numeric")
        assert value is None
        assert valid is False

    def test_open_ended_unsupported(self):
        value, valid = dtmf_to_value("42", "open_ended")
        assert value is None
        assert valid is False


class TestBuildDtmfPrompt:
    def test_yes_no_prompt(self):
        prompt = build_dtmf_prompt("yes_no", None)
        assert "1" in prompt
        assert "2" in prompt

    def test_single_choice_prompt(self):
        options = [
            {"value": "a", "label": "Option A"},
            {"value": "b", "label": "Option B"},
        ]
        prompt = build_dtmf_prompt("single_choice", options)
        assert "1" in prompt
        assert "2" in prompt
        assert "Option A" in prompt or "Option B" in prompt

    def test_numeric_prompt(self):
        prompt = build_dtmf_prompt("numeric", None)
        assert "keypad" in prompt.lower() or "enter" in prompt.lower()

    def test_open_ended_returns_empty(self):
        prompt = build_dtmf_prompt("open_ended", None)
        assert prompt == ""
