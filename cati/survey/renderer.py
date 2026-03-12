"""Determine and format the next question to ask during a live interview."""
from __future__ import annotations

from typing import Any

from cati.survey.skip_logic import find_next_question_key


class SurveyRenderer:
    """Stateless helper that determines what to say next during an interview.

    Takes a snapshot of the current survey definition and provides methods
    for the interview engine to query the next question text.
    """

    def __init__(
        self,
        questions: list[dict[str, Any]],
        skip_rules: list[dict[str, Any]],
    ) -> None:
        # questions: list of dicts with keys matching QuestionDef fields
        self._questions = {q["question_key"]: q for q in questions}
        self._ordered_keys = [q["question_key"] for q in questions]
        self._skip_rules = skip_rules

    @property
    def first_question_key(self) -> str | None:
        return self._ordered_keys[0] if self._ordered_keys else None

    def get_question(self, question_key: str) -> dict[str, Any] | None:
        return self._questions.get(question_key)

    def next_question_key(
        self,
        current_question_key: str,
        responses: dict[str, Any],
    ) -> str | None:
        """Return the key of the next question, or None if survey is complete."""
        return find_next_question_key(
            current_question_key,
            responses,
            self._skip_rules,
            self._ordered_keys,
        )

    def render_question_text(self, question_key: str, *, use_rephrasing: bool = False) -> str:
        """Return the text to speak for a given question.

        Args:
            question_key: The question to render.
            use_rephrasing: If True and a rephrasing exists, use it instead.
        """
        q = self._questions.get(question_key)
        if q is None:
            raise KeyError(f"Unknown question key: {question_key!r}")

        text = q.get("text", "")
        if use_rephrasing and q.get("rephrasing"):
            text = q["rephrasing"]

        # Append spoken option labels for choice questions
        question_type = q.get("question_type", "")
        if question_type in ("single_choice", "multiple_choice") and q.get("options"):
            labels = [
                opt.get("spoken_label") or opt.get("label") or str(opt.get("value", ""))
                for opt in q["options"]
            ]
            options_text = ", ".join(labels[:-1])
            if len(labels) > 1:
                options_text += f", or {labels[-1]}"
            else:
                options_text = labels[0] if labels else ""
            text = f"{text} Your options are: {options_text}."
        elif question_type == "yes_no":
            text = f"{text} Please say yes or no."
        elif question_type in ("rating_scale", "numeric") and q.get("validation"):
            min_val = q["validation"].get("min", 1 if question_type == "rating_scale" else None)
            max_val = q["validation"].get("max", 10 if question_type == "rating_scale" else None)
            if min_val is not None and max_val is not None:
                text = f"{text} Please give a number between {min_val} and {max_val}."

        return text

    @classmethod
    def from_survey_def(cls, survey_def: Any) -> "SurveyRenderer":
        """Construct from a SurveyDef dataclass."""
        questions = [
            {
                "question_key": q.question_key,
                "question_type": q.question_type,
                "text": q.text,
                "rephrasing": q.rephrasing,
                "options": q.options,
                "validation": q.validation,
                "required": q.required,
                "max_retries": q.max_retries,
                "position": q.position,
            }
            for q in survey_def.questions
        ]
        skip_rules = [
            {
                "source_question_key": r.source_question_key,
                "condition_expr": r.condition_expr,
                "target_question_key": r.target_question_key,
                "priority": r.priority,
            }
            for r in survey_def.skip_rules
        ]
        return cls(questions=questions, skip_rules=skip_rules)
