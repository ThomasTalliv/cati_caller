"""FastAPI application factory."""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from cati.api.routers import health, surveys
from cati.api.routers import calls, contacts, responses, analysis, exports
from cati.telephony.call_events import router as webhooks_router
from cati.db.engine import dispose_engine
from config.logging import configure_logging
from config.settings import get_settings

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    configure_logging(debug=settings.debug)
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="CATI Caller API",
        description="AI-driven CATI survey caller",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(surveys.router)
    app.include_router(calls.router)
    app.include_router(contacts.router)
    app.include_router(responses.router)
    app.include_router(analysis.router)
    app.include_router(exports.router)
    app.include_router(webhooks_router)

    # Serve compiled frontend (Vite build output) at /
    # Falls back gracefully if the dist directory doesn't exist yet (dev mode).
    dist_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if dist_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

    return app
