"""Health and readiness probes."""
from fastapi import APIRouter
from sqlalchemy import text

from cati.db.session import get_session_factory

router = APIRouter(tags=["system"])


@router.get("/health")
async def liveness() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def readiness() -> dict:
    errors: list[str] = []

    # Check DB
    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        errors.append(f"db: {exc}")

    if errors:
        return {"status": "degraded", "errors": errors}
    return {"status": "ready"}
