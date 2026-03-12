"""Fluent API for constructing survey definitions programmatically or from JSON."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

QuestionType = Literal[
    "open_ended", "single_choice", "multiple_choice", "numeric", "yes_no", "rating_scale", "date"
]


@dataclass
class QuestionDef:
    question_key: str
    question_type: QuestionType
    text: str
    position: int = 0
    rephrasing: str | None = None
    options: list[dict[str, Any]] | None = None
    validation: dict[str, Any] | None = None
    required: bool = True
    max_retries: int = 2
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class SkipRuleDef:
    source_question_key: str
    condition_expr: str
    target_question_key: str | None = None  # None = end survey
    priority: int = 0
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class SurveyDef:
    name: str
    language: str = "en"
    description: str | None = None
    intro_text: str | None = None
    outro_text: str | None = None
    max_duration_s: int = 900
    metadata: dict[str, Any] = field(default_factory=dict)
    questions: list[QuestionDef] = field(default_factory=list)
    skip_rules: list[SkipRuleDef] = field(default_factory=list)
    id: uuid.UUID = field(default_factory=uuid.uuid4)


class SurveyBuilder:
    """Fluent builder for survey definitions.

    Usage::

        survey = (
            SurveyBuilder("Customer Satisfaction")
            .language("en")
            .intro("Thank you for taking our survey.")
            .add_question("q1_satisfied", "yes_no", "Are you satisfied with our service?")
            .add_question("q2_score", "rating_scale", "On a scale of 1 to 10, how would you rate us?",
                          validation={"min": 1, "max": 10})
            .add_skip_rule("q1_satisfied", "responses.q1_satisfied == 'yes'", target="q2_score")
            .build()
        )
    """

    def __init__(self, name: str) -> None:
        self._survey = SurveyDef(name=name)
        self._position = 0

    # ── Metadata ──────────────────────────────────────────────────────────────

    def language(self, lang: str) -> SurveyBuilder:
        self._survey.language = lang
        return self

    def description(self, text: str) -> SurveyBuilder:
        self._survey.description = text
        return self

    def intro(self, text: str) -> SurveyBuilder:
        self._survey.intro_text = text
        return self

    def outro(self, text: str) -> SurveyBuilder:
        self._survey.outro_text = text
        return self

    def max_duration(self, seconds: int) -> SurveyBuilder:
        self._survey.max_duration_s = seconds
        return self

    def meta(self, **kwargs: Any) -> SurveyBuilder:
        self._survey.metadata.update(kwargs)
        return self

    # ── Questions ─────────────────────────────────────────────────────────────

    def add_question(
        self,
        question_key: str,
        question_type: QuestionType,
        text: str,
        *,
        rephrasing: str | None = None,
        options: list[dict[str, Any]] | None = None,
        validation: dict[str, Any] | None = None,
        required: bool = True,
        max_retries: int = 2,
    ) -> SurveyBuilder:
        self._position += 1
        q = QuestionDef(
            question_key=question_key,
            question_type=question_type,
            text=text,
            position=self._position,
            rephrasing=rephrasing,
            options=options,
            validation=validation,
            required=required,
            max_retries=max_retries,
        )
        self._survey.questions.append(q)
        return self

    # ── Skip rules ────────────────────────────────────────────────────────────

    def add_skip_rule(
        self,
        source_key: str,
        condition_expr: str,
        *,
        target: str | None = None,
        priority: int = 0,
    ) -> SurveyBuilder:
        rule = SkipRuleDef(
            source_question_key=source_key,
            condition_expr=condition_expr,
            target_question_key=target,
            priority=priority,
        )
        self._survey.skip_rules.append(rule)
        return self

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> SurveyDef:
        return self._survey

    # ── JSON import ───────────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SurveyDef:
        """Import a survey from a plain dictionary (e.g. loaded from JSON)."""
        builder = cls(data["name"])
        if "language" in data:
            builder.language(data["language"])
        if "description" in data:
            builder.description(data["description"])
        if "intro_text" in data:
            builder.intro(data["intro_text"])
        if "outro_text" in data:
            builder.outro(data["outro_text"])
        if "max_duration_s" in data:
            builder.max_duration(data["max_duration_s"])
        if "metadata" in data:
            builder.meta(**data["metadata"])

        for q in data.get("questions", []):
            builder.add_question(
                question_key=q["question_key"],
                question_type=q["question_type"],
                text=q["text"],
                rephrasing=q.get("rephrasing"),
                options=q.get("options"),
                validation=q.get("validation"),
                required=q.get("required", True),
                max_retries=q.get("max_retries", 2),
            )

        for r in data.get("skip_rules", []):
            builder.add_skip_rule(
                source_key=r["source_question_key"],
                condition_expr=r["condition_expr"],
                target=r.get("target_question_key"),
                priority=r.get("priority", 0),
            )

        return builder.build()
