"""Survey integrity validation before activation."""
from __future__ import annotations

from dataclasses import dataclass

from cati.survey.builder import SurveyDef

VALID_QUESTION_TYPES = {
    "open_ended",
    "single_choice",
    "multiple_choice",
    "numeric",
    "yes_no",
    "rating_scale",
    "date",
}

CHOICE_TYPES = {"single_choice", "multiple_choice"}


@dataclass
class ValidationError:
    field: str
    message: str

    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


class SurveyValidationError(Exception):
    def __init__(self, errors: list[ValidationError]) -> None:
        self.errors = errors
        super().__init__("; ".join(str(e) for e in errors))


def validate_survey(survey: SurveyDef) -> None:
    """Validate survey definition. Raises SurveyValidationError on failure."""
    errors: list[ValidationError] = []

    if not survey.name.strip():
        errors.append(ValidationError("name", "Survey name must not be empty"))

    if not survey.questions:
        errors.append(ValidationError("questions", "Survey must have at least one question"))
        raise SurveyValidationError(errors)

    keys: set[str] = set()
    for q in survey.questions:
        # Duplicate keys
        if q.question_key in keys:
            errors.append(
                ValidationError("questions", f"Duplicate question_key: {q.question_key!r}")
            )
        keys.add(q.question_key)

        # Question type
        if q.question_type not in VALID_QUESTION_TYPES:
            errors.append(
                ValidationError(
                    f"questions.{q.question_key}",
                    f"Invalid question_type {q.question_type!r}. "
                    f"Must be one of: {sorted(VALID_QUESTION_TYPES)}",
                )
            )

        # Choice questions must have options
        if q.question_type in CHOICE_TYPES:
            if not q.options:
                errors.append(
                    ValidationError(
                        f"questions.{q.question_key}",
                        "Choice questions must define at least one option",
                    )
                )
            else:
                option_values = [o.get("value") for o in q.options]
                if len(option_values) != len(set(option_values)):
                    errors.append(
                        ValidationError(
                            f"questions.{q.question_key}",
                            "Option values must be unique",
                        )
                    )

        # Numeric validation range
        if q.question_type == "numeric" and q.validation:
            min_val = q.validation.get("min")
            max_val = q.validation.get("max")
            if min_val is not None and max_val is not None and min_val >= max_val:
                errors.append(
                    ValidationError(
                        f"questions.{q.question_key}",
                        f"Validation min ({min_val}) must be less than max ({max_val})",
                    )
                )

        # Rating scale validation
        if q.question_type == "rating_scale" and q.validation:
            min_val = q.validation.get("min", 1)
            max_val = q.validation.get("max", 10)
            if max_val - min_val < 1:
                errors.append(
                    ValidationError(
                        f"questions.{q.question_key}",
                        "Rating scale must have a range of at least 2",
                    )
                )

        if not q.text.strip():
            errors.append(
                ValidationError(f"questions.{q.question_key}", "Question text must not be empty")
            )

    # Skip rules: validate references
    for rule in survey.skip_rules:
        if rule.source_question_key not in keys:
            errors.append(
                ValidationError(
                    "skip_rules",
                    f"source_question_key {rule.source_question_key!r} does not reference a known question",
                )
            )
        if rule.target_question_key is not None and rule.target_question_key not in keys:
            errors.append(
                ValidationError(
                    "skip_rules",
                    f"target_question_key {rule.target_question_key!r} does not reference a known question",
                )
            )
        if not rule.condition_expr.strip():
            errors.append(
                ValidationError("skip_rules", "condition_expr must not be empty")
            )

    # Detect obvious skip cycles (source skips to itself)
    for rule in survey.skip_rules:
        if rule.target_question_key == rule.source_question_key:
            errors.append(
                ValidationError(
                    "skip_rules",
                    f"Skip rule creates a direct cycle: {rule.source_question_key!r} -> itself",
                )
            )

    if errors:
        raise SurveyValidationError(errors)
