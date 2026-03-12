# CATI Caller — Deployment Guide

## Prerequisites

- Docker ≥ 24 and Docker Compose ≥ 2.20
- A SignalWire account (project ID, API token, space URL, outbound number)
- Anthropic API key and/or OpenAI API key
- (Optional) Google Cloud service account JSON for Google Sheets export

---

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your credentials

# 2. Start all services
docker compose up -d

# 3. Run database migrations
docker compose exec app alembic upgrade head

# 4. Seed a demo survey (optional)
docker compose exec app python scripts/seed_demo_survey.py

# 5. Access the API
curl -H "x-api-key: $API_KEY" http://localhost:8000/health
# → {"status": "ok", "version": "0.1.0"}

# 6. Open interactive API docs
open http://localhost:8000/docs
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in all values.

### Core

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | Master API key for all REST endpoints | `change-me` |
| `DEBUG` | Enable debug logging and SQL echo | `false` |

### Database

| Variable | Description | Default |
|----------|-------------|---------|
| `DB__POSTGRES_URL` | SQLAlchemy async DSN | `postgresql+asyncpg://cati:cati@postgres:5432/cati` |
| `DB__REDIS_URL` | Redis DSN for session state | `redis://redis:6379/0` |
| `DB__POOL_SIZE` | SQLAlchemy connection pool size | `10` |

### SignalWire

| Variable | Description |
|----------|-------------|
| `SIGNALWIRE__PROJECT_ID` | SignalWire project UUID |
| `SIGNALWIRE__API_TOKEN` | SignalWire API token |
| `SIGNALWIRE__SPACE_URL` | e.g. `your-company.signalwire.com` |
| `SIGNALWIRE__OUTBOUND_NUMBER` | E.164 caller ID, e.g. `+15551234567` |
| `SIGNALWIRE__WEBHOOK_BASE_URL` | Publicly reachable URL for webhooks |

> **Note:** `WEBHOOK_BASE_URL` must be publicly reachable by SignalWire. Use [ngrok](https://ngrok.com) or a public IP/domain in development.

### TTS

| Variable | Description | Default |
|----------|-------------|---------|
| `TTS__PROVIDER` | `kokoro` or `xtts` | `kokoro` |
| `TTS__KOKORO_VOICE` | Voice ID, e.g. `af_sky` (EN), `ff_siwis` (FR) | `af_sky` |
| `TTS__KOKORO_DEVICE` | `cpu` or `cuda` | `cpu` |

### STT

| Variable | Description | Default |
|----------|-------------|---------|
| `STT__MODEL_SIZE` | Whisper model: `tiny`, `base`, `large-v3-turbo` | `large-v3-turbo` |
| `STT__DEVICE` | `cpu` or `cuda` | `cpu` |
| `STT__LANGUAGE` | ISO 639-1 code, e.g. `en`, `fr`, `de` | `en` |

### LLM

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM__PRIMARY_PROVIDER` | `anthropic` or `openai` | `anthropic` |
| `LLM__ANTHROPIC_API_KEY` | Anthropic API key | — |
| `LLM__ANTHROPIC_MODEL` | Model ID | `claude-sonnet-4-6` |
| `LLM__OPENAI_API_KEY` | OpenAI API key (fallback) | — |
| `LLM__OPENAI_MODEL` | Model ID | `gpt-4o` |

### Export

| Variable | Description | Default |
|----------|-------------|---------|
| `EXPORT__EXPORT_DIR` | Local directory for file exports | `/data/exports` |
| `EXPORT__GOOGLE_SERVICE_ACCOUNT_JSON` | JSON string of service account credentials | — |
| `EXPORT__GOOGLE_SHEETS_FOLDER_ID` | Google Drive folder ID to move sheets into | — |

### Celery

| Variable | Description | Default |
|----------|-------------|---------|
| `CELERY__BROKER_URL` | Celery broker | `redis://redis:6379/1` |
| `CELERY__RESULT_BACKEND` | Celery backend | `redis://redis:6379/2` |
| `CELERY__CALL_CONCURRENCY` | Max simultaneous outbound calls | `5` |
| `CELERY__WORKER_CONCURRENCY` | Celery worker processes | `4` |

---

## Services (Docker Compose)

| Service | Port | Description |
|---------|------|-------------|
| `app` | `8000` | FastAPI + Uvicorn |
| `worker` | — | Celery worker (call, analysis, export tasks) |
| `postgres` | `5432` | PostgreSQL 16 |
| `redis` | `6379` | Redis 7 |

---

## Database Migrations

```bash
# Apply all migrations
docker compose exec app alembic upgrade head

# Create a new migration
docker compose exec app alembic revision --autogenerate -m "add_new_column"

# Roll back one step
docker compose exec app alembic downgrade -1
```

---

## Scaling

### Horizontal API Scaling

Run multiple `app` replicas behind a load balancer. All state is in PostgreSQL and Redis.

```bash
docker compose up -d --scale app=3
```

### Celery Workers

Scale workers independently from the API:

```bash
docker compose up -d --scale worker=4
```

Adjust `CELERY__CALL_CONCURRENCY` to control max simultaneous outbound calls per worker.

### GPU Acceleration

For production with high call volume, add a GPU node:

1. Set `TTS__KOKORO_DEVICE=cuda` and `STT__DEVICE=cuda`
2. Run the worker container with `--gpus all`
3. Enable CUDA in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```

---

## SignalWire Setup

1. Log in to [SignalWire Dashboard](https://signalwire.com)
2. Create a project → note **Project ID** and **API Token**
3. Buy a phone number → note the **E.164** number
4. Set webhook URL: `{WEBHOOK_BASE_URL}/webhooks/signalwire/call-status`

### Provisioning via Script

```bash
python scripts/provision_phone_number.py --area-code 555
```

---

## Monitoring

### Logs

Structured JSON logs to stdout. In production, pipe to your log aggregator:

```bash
docker compose logs -f app | jq .
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# With coverage
pytest --cov=cati --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run integration tests (uses SQLite in-memory, no Postgres required)
pytest tests/integration/
```
