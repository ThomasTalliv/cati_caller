"""Unit tests for survey renderer."""
import pytest

from cati.survey.builder import SurveyBuilder
from cati.survey.renderer import SurveyRenderer


@pytest.fixture
def renderer() -> SurveyRenderer:
    survey = (
        SurveyBuilder("Test")
        .add_question("q1", "yes_no", "Are you happy?")
        .add_question(
            "q2",
            "single_choice",
            "How often?",
            options=[
                {"value": "daily", "label": "Daily", "spoken_label": "daily"},
                {"value": "weekly", "label": "Weekly", "spoken_label": "weekly"},
            ],
        )
        .add_question("q3", "numeric", "Age?", validation={"min": 18, "max": 99})
        .add_question("q4", "rating_scale", "Score?", validation={"min": 1, "max": 5})
        .add_skip_rule("q1", "responses.q1 == 'no'", target=None, priority=0)
        .build()
    )
    return SurveyRenderer.from_survey_def(survey)


def test_first_question_key(renderer: SurveyRenderer) -> None:
    assert renderer.first_question_key == "q1"


def test_render_yes_no_text(renderer: SurveyRenderer) -> None:
    text = renderer.render_question_text("q1")
    assert "yes or no" in text.lower()


def test_render_choice_options_appended(renderer: SurveyRenderer) -> None:
    text = renderer.render_question_text("q2")
    assert "daily" in text.lower()
    assert "weekly" in text.lower()


def test_render_numeric_range(renderer: SurveyRenderer) -> None:
    text = renderer.render_question_text("q3")
    assert "18" in text
    assert "99" in text


def test_render_rating_scale(renderer: SurveyRenderer) -> None:
    text = renderer.render_question_text("q4")
    assert "1" in text
    assert "5" in text


def test_render_rephrasing(renderer: SurveyRenderer) -> None:
    survey = SurveyBuilder("Rephrase").add_question(
        "q1", "open_ended", "Original text?", rephrasing="Rephrased text?"
    ).build()
    r = SurveyRenderer.from_survey_def(survey)
    assert r.render_question_text("q1", use_rephrasing=False) == "Original text?"
    assert r.render_question_text("q1", use_rephrasing=True) == "Rephrased text?"


def test_next_question_skip(renderer: SurveyRenderer) -> None:
    # q1 answered 'no' -> skip rule -> end survey
    next_key = renderer.next_question_key("q1", {"q1": "no"})
    assert next_key is None


def test_next_question_normal_order(renderer: SurveyRenderer) -> None:
    next_key = renderer.next_question_key("q1", {"q1": "yes"})
    assert next_key == "q2"


def test_unknown_question_raises(renderer: SurveyRenderer) -> None:
    with pytest.raises(KeyError):
        renderer.render_question_text("nonexistent")
