# CATI Caller — Survey Schema Reference

## Overview

A survey is a tree-structured questionnaire. The interview engine walks through questions in order, applying skip rules to branch the flow based on prior responses.

---

## Survey Object

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Survey display name (required) |
| `language` | `string` | ISO 639-1 language code: `en`, `fr`, `de`, `es`, `pt`, `it` |
| `intro_text` | `string \| null` | Spoken before the first question |
| `outro_text` | `string \| null` | Spoken after the last question or early exit |
| `description` | `string \| null` | Internal description |
| `max_duration_s` | `int` | Maximum call duration in seconds (default: `900`) |
| `metadata` | `object` | Arbitrary key-value pairs for project tracking |
| `status` | `enum` | `draft` → `active` → `archived` |

---

## Question Object

| Field | Type | Description |
|-------|------|-------------|
| `question_key` | `string` | Unique identifier within the survey (e.g. `q1_overall`) |
| `question_type` | `enum` | See question types below |
| `text` | `string` | Primary spoken text for this question |
| `rephrasing` | `string \| null` | Alternative phrasing used on the first retry |
| `options` | `array \| null` | For `single_choice` questions (see below) |
| `validation` | `object \| null` | For numeric/rating questions (see below) |
| `required` | `bool` | If `false`, respondent may skip. Default: `true` |
| `max_retries` | `int` | Times to re-ask before marking as unclear. Default: `2` |
| `position` | `int` | 1-based display order |

### Question Types

| Type | Expected Answer | DTMF Fallback |
|------|-----------------|---------------|
| `yes_no` | "yes" or "no" | 1=yes, 2=no |
| `rating_scale` | Integer within `validation.min`..`validation.max` | Enter number + `#` |
| `numeric` | Any integer within optional min/max | Enter number + `#` |
| `single_choice` | One of the defined option values | Enter option number + `#` |
| `open_ended` | Free-form text | Not supported via DTMF |

### Validation Object (numeric / rating_scale)

```json
{
  "min": 1,
  "max": 5
}
```

Both `min` and `max` are optional.

### Option Object (single_choice)

```json
{
  "value": "very_satisfied",
  "label": "Very satisfied",
  "spoken_label": "very satisfied"
}
```

`spoken_label` is used in the DTMF prompt if provided; otherwise `label` is used.

---

## Skip Rule Object

Skip rules define conditional branching. Rules are evaluated after each answer.

| Field | Type | Description |
|-------|------|-------------|
| `source_question_key` | `string` | Key of the question that triggers evaluation |
| `condition_expr` | `string` | Expression that must evaluate to `True` to apply the rule |
| `target_question_key` | `string \| null` | Jump to this question; `null` = end the survey |
| `priority` | `int` | Lower = higher priority. Default: `0` |

### Condition Expression Syntax

Expressions are evaluated with `responses` as the context namespace. You can access any previous answer by question key:

```
responses.q1_overall >= 4
responses.q2_recommend == 'yes'
responses.q3_age < 18
responses.q4_choice in ('a', 'b')
```

**Allowed operators:** `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`, `and`, `or`, `not`

**Security:** Expressions are evaluated in a constrained sandbox. Builtins, imports, attribute chains deeper than one level, and `__` names are all blocked.

---

## Python Builder API

```python
from cati.survey.builder import SurveyBuilder
from cati.survey.validator import validate_survey

survey = (
    SurveyBuilder("Customer Satisfaction Survey")
    .language("en")
    .intro("Hello! I'd like to ask you a few quick questions.")
    .outro("Thank you so much for your time!")
    .add_question(
        "q1_overall",
        "rating_scale",
        "Overall, how satisfied were you with your recent experience?",
        rephrasing="On a scale of 1 to 5, how satisfied were you?",
        validation={"min": 1, "max": 5},
    )
    .add_question(
        "q2_recommend",
        "yes_no",
        "Would you recommend our service to a friend?",
    )
    .add_question(
        "q3_reason",
        "open_ended",
        "What was the main reason for your rating?",
        required=False,
    )
    # Skip the open-ended question for satisfied customers (4 or 5)
    .add_skip_rule(
        "q1_overall",
        "responses.q1_overall >= 4",
        target="q2_recommend",
        priority=0,
    )
    .meta(project="Wave1", client="Acme")
    .build()
)

validate_survey(survey)  # Raises ValueError if invalid
```

---

## JSON Import

```python
survey = SurveyBuilder.from_dict({
    "name": "NPS Survey",
    "language": "fr",
    "intro_text": "Bonjour!",
    "outro_text": "Merci!",
    "questions": [
        {
            "question_key": "nps",
            "question_type": "rating_scale",
            "text": "Sur une échelle de 0 à 10, recommanderiez-vous notre service?",
            "validation": {"min": 0, "max": 10}
        }
    ],
    "skip_rules": []
})
```

---

## Survey Lifecycle

```
draft → active → archived
```

- **draft**: Can be edited. Cannot initiate calls.
- **active**: Locked for editing. Calls can be initiated.
- **archived**: Soft-deleted. No new calls. Historical data preserved.

Activate via `POST /api/v1/surveys/{id}/activate`.

Validation checks performed on activation:
- At least one question
- All question keys are unique
- All skip rule source/target keys exist in the survey
- No self-referencing skip rules
- No unreachable questions (questions that can never be reached)
- Single-choice questions have at least 2 options
- Numeric/rating validation min ≤ max

---

## Multi-language Configuration

Set the survey `language` field to the respondent's language. Configure the corresponding TTS voice:

| Language | Kokoro Voice | XTTS Speaker |
|----------|-------------|--------------|
| English  | `af_sky`, `am_adam` | English speaker |
| French   | `ff_siwis` | French speaker |
| German   | `de_*` | German speaker |
| Spanish  | `es_*` | Spanish speaker |
| Portuguese | `pt_*` | Portuguese speaker |
| Italian  | `it_*` | Italian speaker |

Set `TTS__KOKORO_VOICE` in your `.env` or switch providers via `TTS__PROVIDER=xtts` for broader language support.
