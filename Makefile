.PHONY: dev test migrate lint fmt install

install:
	pip install -e ".[dev]"

dev:
	docker compose up --build

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(msg)"

test:
	pytest -v --tb=short

lint:
	ruff check .

fmt:
	ruff check --fix . && ruff format .

shell:
	python -c "import asyncio; from cati.db.session import get_session; print('DB session ready')"

seed:
	python scripts/seed_demo_survey.py
