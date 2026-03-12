# CATI Caller — System Architecture

## Overview

CATI Caller is a self-hosted, AI-driven Computer-Assisted Telephone Interviewing system. It replaces human call-centre interviewers with a real-time voice AI agent that dials respondents, conducts structured survey interviews, parses spoken answers, and stores results for analysis and export.

---

## Component Map

```
┌─────────────────────────────────────────────────────────────────────┐
│  External                                                           │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────┐               │
│  │ REST API │   │  SignalWire  │   │ LLM (Claude/ │               │
│  │ Clients  │   │  (Telephony) │   │  OpenAI)     │               │
│  └────┬─────┘   └──────┬───────┘   └──────┬───────┘               │
└───────┼─────────────────┼──────────────────┼───────────────────────┘
        │                 │                  │
┌───────▼─────────────────▼──────────────────▼───────────────────────┐
│  FastAPI Application (cati/api/)                                    │
│                                                                     │
│  Routers: surveys · calls · contacts · responses · analysis ·       │
│           exports · health · webhooks                               │
│                                                                     │
│  Middleware: API-key auth · Rate limiting (200 req/min) · CORS      │
└────────┬────────────────────────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────────────────────┐
│  Interview Engine (cati/interview/)                                 │
│                                                                     │
│  LangGraph StateGraph                                               │
│  ┌────────┐   ┌─────────────┐   ┌────────────────┐                │
│  │ greet  │──▶│ ask_question│──▶│listen_and_parse│                │
│  └────────┘   └─────────────┘   └───────┬────────┘                │
│                    ▲                     │                          │
│                    │          ┌──────────▼──────────┐              │
│                    └──────────│   handle_refusal /  │              │
│                               │   handle_unclear /  │              │
│                               │   close_interview   │              │
│                               └─────────────────────┘              │
│                                                                     │
│  State: InterviewState (Pydantic) ←→ Redis (session TTL: 2h)       │
└────────┬──────────────────────────────────────────────────────────-┘
         │
   ┌─────┴──────────────────────────────────────────────────────────┐
   │  Voice Pipeline                                                 │
   │                                                                 │
   │  SignalWire PCM stream                                          │
   │      → Silero VAD (speech boundary detection)                   │
   │      → faster-whisper (streaming STT, large-v3-turbo)          │
   │      → LLM response parser (Claude/GPT-4o)                     │
   │      → Survey renderer (next question text)                     │
   │      → Kokoro-82M TTS (PCM output, resampled to 16 kHz)        │
   │      → XTTS-v2 (voice cloning / multilingual fallback)         │
   └─────┬──────────────────────────────────────────────────────────┘
         │
   ┌─────▼──────────────────────────────────────────────────────────┐
   │  Persistence                                                    │
   │                                                                 │
   │  PostgreSQL (SQLAlchemy async / asyncpg)                        │
   │    surveys · questions · skip_rules · contacts                  │
   │    call_batches · calls · responses · transcript_turns          │
   │    analysis_reports · exports                                   │
   │                                                                 │
   │  Redis                                                          │
   │    Interview sessions (interview:session:{call_id})             │
   │    Celery broker + result backend                               │
   └─────┬──────────────────────────────────────────────────────────┘
         │
   ┌─────▼──────────────────────────────────────────────────────────┐
   │  Background Workers (Celery)                                    │
   │                                                                 │
   │  call_tasks     — batch call dispatch with concurrency control  │
   │  analysis_tasks — post-call AI analysis (summarize, sentiment)  │
   │  export_tasks   — Word / Excel / TXT / Google Sheets export     │
   └────────────────────────────────────────────────────────────────┘
```

---

## Call Data Flow

### Outbound Call Initiation

```
POST /api/v1/calls/initiate
  → DNC check (contacts table)
  → Create Call record (status: pending)
  → SignalWire REST API: dial respondent
  → Call record updated (status: dialing + sw_call_id)
  → SignalWire webhook fires → CATIAgent.on_call_answered()
```

### Live Interview Loop (per audio turn)

```
SignalWire PCM stream (μ-law → PCM decode)
  → SileroVAD: detect speech end
  → faster-whisper: transcribe to text
  → Redis: load InterviewState
  → LangGraph: execute listen_and_parse node
      → ResponseParser: structured answer extraction
      → SkipLogic: CEL-like expression evaluator for branching
      → SurveyRenderer: compute next question text
  → Kokoro TTS: synthesize response audio
  → PCM returned to SignalWire → respondent's phone speaker
  (repeat until survey is_complete or respondent hangs up)
```

### Post-Call Pipeline

```
SignalWire webhook: call-status = completed
  → CallEvents: update Call status in DB
  → Trigger Celery: analysis_tasks.run_call_analysis
      → CallAnalyzer:
          → LLM: summarize transcript
          → LLM: sentiment analysis
          → LLM: thematic categorisation (open-ended)
          → Persist AnalysisReport to DB
```

### Export Pipeline

```
POST /api/v1/exports  { survey_id, format }
  → Create Export record (status: pending)
  → Celery: export_tasks.generate_export
      → get_exporter(format): txt | excel | word | gsheets
      → Write file to /data/exports/ or Google Sheets
      → Update Export record (status: completed, file_path/external_url)
GET /api/v1/exports/{id}/download
  → FileResponse or redirect to Sheets URL
```

---

## Key Design Decisions

### LangGraph for Interview State

The interview is modelled as a directed graph where each node is a Python async function that reads and returns an `InterviewState`. Routing between nodes is driven by `state.next_node`, making the transition logic explicit and testable without branching inside nodes.

### CEL-like Skip Logic

Survey branching rules (`skip_rules`) use a constrained expression evaluator that sandboxes `eval()` with a denylist of dangerous identifiers and a `_Namespace` wrapper that enables dot-notation attribute access on the responses dictionary (e.g., `responses.q1 >= 4`).

### Voice Provider Abstraction

Both TTS and STT are accessed through abstract base classes (`TTSProvider`, `STTProvider`), making it straightforward to swap Kokoro for XTTS-v2 or faster-whisper for a cloud STT provider without touching interview logic.

### DNC Enforcement

Do-Not-Call enforcement runs synchronously before any call is created or dialled. It checks both by `contact_id` (if provided) and by normalized E.164 phone number against the contacts table.

---

## Supported Languages

| Language | TTS (Kokoro) | TTS (XTTS-v2) | STT (faster-whisper) |
|----------|-------------|----------------|----------------------|
| English  | ✓           | ✓              | ✓                    |
| French   | ✓           | ✓              | ✓                    |
| German   | ✓           | ✓              | ✓                    |
| Spanish  | ✓           | ✓              | ✓                    |
| Portuguese | ✓         | ✓              | ✓                    |
| Italian  | ✓           | ✓              | ✓                    |

Configure via `TTS__KOKORO_VOICE` (e.g., `ff_siwis` for French) and `STT__LANGUAGE`.
