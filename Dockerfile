FROM python:3.11-slim AS builder

WORKDIR /app
RUN pip install hatchling
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

FROM python:3.11-slim AS runtime

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

RUN mkdir -p /data/exports

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000
CMD ["uvicorn", "cati.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
