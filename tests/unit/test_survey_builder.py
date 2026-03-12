"""Unit tests for survey builder."""
import pytest

from cati.survey.builder import SurveyBuilder, SurveyDef


def test_basic_survey_build() -> None:
    survey = (
        SurveyBuilder("Test Survey")
        .language("en")
        .intro("Welcome!")
        .outro("Thank you!")
        .add_question("q1", "yes_no", "Do you like surveys?")
        .build()
    )
    assert survey.name == "Test Survey"
    assert survey.language == "en"
    assert survey.intro_text == "Welcome!"
    assert survey.outro_text == "Thank you!"
    assert len(survey.questions) == 1
    assert survey.questions[0].question_key == "q1"
    assert survey.questions[0].position == 1


def test_question_positions_auto_increment() -> None:
    survey = (
        SurveyBuilder("Multi-Q")
        .add_question("q1", "yes_no", "Q1?")
        .add_question("q2", "numeric", "Q2?")
        .add_question("q3", "open_ended", "Q3?")
        .build()
    )
    positions = [q.position for q in survey.questions]
    assert positions == [1, 2, 3]


def test_skip_rule_added() -> None:
    survey = (
        SurveyBuilder("Skip Test")
        .add_question("q1", "yes_no", "Are you 18 or over?")
        .add_question("q2", "open_ended", "What is your occupation?")
        .add_skip_rule("q1", "responses.q1 == 'no'", target=None)
        .build()
    )
    assert len(survey.skip_rules) == 1
    rule = survey.skip_rules[0]
    assert rule.source_question_key == "q1"
    assert rule.condition_expr == "responses.q1 == 'no'"
    assert rule.target_question_key is None


def test_from_dict() -> None:
    data = {
        "name": "Dict Survey",
        "language": "fr",
        "questions": [
            {
                "question_key": "q1",
                "question_type": "single_choice",
                "text": "Preferred option?",
                "options": [{"value": "a", "label": "Option A"}, {"value": "b", "label": "Option B"}],
            }
        ],
        "skip_rules": [],
    }
    survey = SurveyBuilder.from_dict(data)
    assert isinstance(survey, SurveyDef)
    assert survey.name == "Dict Survey"
    assert survey.language == "fr"
    assert survey.questions[0].options is not None
    assert len(survey.questions[0].options) == 2


def test_metadata() -> None:
    survey = SurveyBuilder("Meta").meta(project="P1", wave=3).build()
    assert survey.metadata["project"] == "P1"
    assert survey.metadata["wave"] == 3


def test_choice_question_options() -> None:
    opts = [{"value": "yes", "label": "Yes"}, {"value": "no", "label": "No"}]
    survey = (
        SurveyBuilder("Options")
        .add_question("q1", "single_choice", "Pick one?", options=opts)
        .build()
    )
    assert survey.questions[0].options == opts
