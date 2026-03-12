"""Unit tests for survey validator."""
import pytest

from cati.survey.builder import SurveyBuilder
from cati.survey.validator import SurveyValidationError, validate_survey


def test_valid_survey_passes() -> None:
    survey = (
        SurveyBuilder("Valid Survey")
        .add_question("q1", "yes_no", "Are you happy?")
        .build()
    )
    validate_survey(survey)  # should not raise


def test_empty_name_fails() -> None:
    survey = SurveyBuilder("  ").add_question("q1", "yes_no", "Q?").build()
    with pytest.raises(SurveyValidationError) as exc_info:
        validate_survey(survey)
    assert any("name" in str(e) for e in exc_info.value.errors)


def test_no_questions_fails() -> None:
    survey = SurveyBuilder("Empty").build()
    with pytest.raises(SurveyValidationError) as exc_info:
        validate_survey(survey)
    assert any("questions" in str(e) for e in exc_info.value.errors)


def test_duplicate_question_key_fails() -> None:
    survey = (
        SurveyBuilder("Dup")
        .add_question("q1", "yes_no", "Q1?")
        .add_question("q1", "open_ended", "Q1 again?")
        .build()
    )
    with pytest.raises(SurveyValidationError) as exc_info:
        validate_survey(survey)
    assert any("Duplicate" in str(e) for e in exc_info.value.errors)


def test_invalid_question_type_fails() -> None:
    from cati.survey.builder import QuestionDef, SurveyDef
    survey = SurveyDef(name="Bad Type")
    survey.questions.append(
        QuestionDef(question_key="q1", question_type="invalid_type", text="Q?", position=1)
    )
    with pytest.raises(SurveyValidationError) as exc_info:
        validate_survey(survey)
    assert any("question_type" in str(e) for e in exc_info.value.errors)


def test_choice_without_options_fails() -> None:
    survey = (
        SurveyBuilder("No Options")
        .add_question("q1", "single_choice", "Pick one?")
        .build()
    )
    with pytest.raises(SurveyValidationError) as exc_info:
        validate_survey(survey)
    assert any("option" in str(e).lower() for e in exc_info.value.errors)


def test_skip_rule_invalid_source_key_fails() -> None:
    survey = (
        SurveyBuilder("Bad Rule")
        .add_question("q1", "yes_no", "Q?")
        .add_skip_rule("nonexistent_key", "responses.nonexistent_key == 'x'")
        .build()
    )
    with pytest.raises(SurveyValidationError) as exc_info:
        validate_survey(survey)
    assert any("source_question_key" in str(e) for e in exc_info.value.errors)


def test_skip_rule_self_cycle_fails() -> None:
    survey = (
        SurveyBuilder("Cycle")
        .add_question("q1", "yes_no", "Q?")
        .add_skip_rule("q1", "responses.q1 == 'yes'", target="q1")
        .build()
    )
    with pytest.raises(SurveyValidationError) as exc_info:
        validate_survey(survey)
    assert any("cycle" in str(e).lower() for e in exc_info.value.errors)


def test_numeric_validation_range_fails() -> None:
    survey = (
        SurveyBuilder("Bad Range")
        .add_question("q1", "numeric", "Age?", validation={"min": 100, "max": 10})
        .build()
    )
    with pytest.raises(SurveyValidationError) as exc_info:
        validate_survey(survey)
    assert any("min" in str(e) for e in exc_info.value.errors)
