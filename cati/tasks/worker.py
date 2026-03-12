"""Celery application."""
from celery import Celery

from config.settings import get_settings


def create_celery() -> Celery:
    settings = get_settings()
    app = Celery("cati_caller")
    app.conf.update(
        broker_url=settings.celery.broker_url,
        result_backend=settings.celery.result_backend,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        worker_concurrency=settings.celery.worker_concurrency,
        # Auto-discover tasks
        include=[
            "cati.tasks.call_tasks",
            "cati.tasks.analysis_tasks",
            "cati.tasks.export_tasks",
        ],
    )
    return app


celery_app = create_celery()
