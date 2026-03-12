# CATI Caller — API Reference

All endpoints require an `x-api-key` header matching the `API_KEY` environment variable.

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## Surveys

### `POST /api/v1/surveys`

Create a survey.

**Request body:**
```json
{
  "name": "Customer Satisfaction Survey",
  "language": "en",
  "intro_text": "Hello! I'm calling to ask a few quick questions.",
  "outro_text": "Thank you for your time!",
  "description": "Optional description",
  "max_duration_s": 600,
  "metadata": {}
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "Customer Satisfaction Survey",
  "status": "draft",
  "language": "en",
  ...
}
```

---

### `GET /api/v1/surveys`

List all surveys. Supports `?status=active` filter.

### `GET /api/v1/surveys/{id}`

Get a single survey with all questions and skip rules.

### `PUT /api/v1/surveys/{id}`

Update survey fields (partial update supported).

### `DELETE /api/v1/surveys/{id}`

Archive a survey (sets status to `archived`).

### `POST /api/v1/surveys/{id}/activate`

Activate a draft survey. Runs validation — survey must have at least one question with no unreachable questions or cycles.

---

### `POST /api/v1/surveys/{id}/questions`

Add a question to a survey.

**Request body:**
```json
{
  "question_key": "q1_overall",
  "question_type": "rating_scale",
  "text": "How would you rate your experience from 1 to 5?",
  "rephrasing": "Could you rate from 1 to 5?",
  "validation": {"min": 1, "max": 5},
  "options": null,
  "required": true,
  "max_retries": 2
}
```

**Question types:** `yes_no`, `rating_scale`, `numeric`, `single_choice`, `open_ended`

### `PUT /api/v1/surveys/{id}/questions/{qid}`

Update a question.

### `DELETE /api/v1/surveys/{id}/questions/{qid}`

Delete a question.

---

### `POST /api/v1/surveys/{id}/skip-rules`

Add a branching rule.

**Request body:**
```json
{
  "source_question_key": "q1_overall",
  "condition_expr": "responses.q1_overall >= 4",
  "target_question_key": "q3_contact",
  "priority": 0
}
```

`target_question_key: null` means end the survey early.

---

## Contacts

### `POST /api/v1/contacts`

Create a contact.

```json
{
  "phone_number": "+15551234567",
  "name": "Jane Smith",
  "do_not_call": false,
  "metadata": {}
}
```

### `GET /api/v1/contacts`

List contacts. `?dnc_only=true` filters to DNC contacts only.

### `GET /api/v1/contacts/{id}`

Get a contact.

### `PATCH /api/v1/contacts/{id}`

Update contact name, DNC status, or metadata.

### `POST /api/v1/contacts/{id}/do-not-call`

Add a contact to the Do-Not-Call list (`204 No Content`).

### `DELETE /api/v1/contacts/{id}/do-not-call`

Remove from the DNC list (`204 No Content`).

### `POST /api/v1/contacts/check-dnc`

Check if a phone number is on the DNC list.

```json
{ "phone_number": "+15551234567" }
```

Response:
```json
{ "phone_number": "+15551234567", "do_not_call": false }
```

---

## Calls

### `POST /api/v1/calls/initiate`

Initiate a single outbound call. Enforces DNC check first.

```json
{
  "survey_id": "uuid",
  "phone_number": "+15551234567",
  "contact_id": "uuid (optional)"
}
```

**Response:** `202 Accepted`
```json
{ "call_id": "uuid", "status": "dialing" }
```

### `POST /api/v1/calls/batch`

Schedule a batch of calls.

```json
{
  "survey_id": "uuid",
  "contacts": [
    {"phone_number": "+15551111111", "contact_id": "uuid"},
    {"phone_number": "+15552222222"}
  ],
  "name": "Wave 1",
  "concurrency": 5
}
```

### `GET /api/v1/calls`

List calls. Supports `?survey_id=`, `?call_status=`, `?limit=`, `?offset=`.

### `GET /api/v1/calls/{id}`

Get call details.

### `DELETE /api/v1/calls/{id}`

Cancel a pending or dialing call.

### `GET /api/v1/batches`

List all call batches.

### `POST /api/v1/batches/{id}/pause`

Pause a running batch.

### `POST /api/v1/batches/{id}/resume`

Resume a paused batch.

---

## Responses & Transcripts

### `GET /api/v1/calls/{call_id}/responses`

Get all structured responses for a call.

### `GET /api/v1/calls/{call_id}/transcript`

Get the full conversation transcript for a call.

### `GET /api/v1/surveys/{survey_id}/responses`

Get all responses across all calls for a survey.

### `GET /api/v1/surveys/{survey_id}/stats`

Get aggregated statistics.

```json
{
  "survey_id": "uuid",
  "total_calls": 150,
  "completed_calls": 132,
  "completion_rate": 0.880
}
```

---

## Analysis

### `POST /api/v1/analysis/calls/{call_id}`

Trigger AI analysis for a single call (summarize, sentiment).

### `GET /api/v1/analysis/calls/{call_id}`

Get analysis report for a call.

### `POST /api/v1/analysis/surveys/{survey_id}`

Trigger aggregate survey analysis (cross-call summary, thematic clustering).

### `GET /api/v1/analysis/surveys/{survey_id}`

Get the latest survey analysis report.

---

## Exports

### `POST /api/v1/exports`

Request an export.

```json
{
  "survey_id": "uuid",
  "format": "excel",
  "call_ids": ["uuid1", "uuid2"]
}
```

**Formats:** `txt`, `excel`, `word`, `gsheets`

`call_ids` is optional — omit to export all calls for the survey.

**Response:** `202 Accepted`
```json
{
  "id": "uuid",
  "status": "pending",
  ...
}
```

### `GET /api/v1/exports`

List all export requests.

### `GET /api/v1/exports/{id}`

Get export status. Poll until `status == "completed"`.

### `GET /api/v1/exports/{id}/download`

Download the export file. Returns `FileResponse` for file formats or `302 redirect` for Google Sheets.

---

## Webhooks (SignalWire → Internal)

These endpoints are called by SignalWire and do not require the API key.

### `POST /webhooks/signalwire/call-status`

Called by SignalWire when call status changes. Updates call record and triggers post-call analysis.

### `POST /webhooks/signalwire/agent`

SWAIG entry point — initialises `CATIAgent` and processes audio turns.

---

## Health

### `GET /health`

```json
{ "status": "ok", "version": "0.1.0" }
```

---

## Error Responses

| Status | Meaning |
|--------|---------|
| 400 | Bad request |
| 401 | Invalid or missing API key |
| 404 | Resource not found |
| 409 | Conflict (e.g. export not ready, call already active) |
| 422 | Validation error |
| 429 | Rate limit exceeded (200 req/min per IP) |
| 500 | Internal server error |
