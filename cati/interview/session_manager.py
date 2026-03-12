"""Serialize/deserialize InterviewState to/from Redis keyed by call_id."""
from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    pass

log = structlog.get_logger(__name__)

_KEY_PREFIX = "interview:session:"
_TTL_SECONDS = 3600 * 2  # 2 hours — longer than any realistic survey


class SessionManager:
    """Redis-backed interview session store."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            import redis.asyncio as aioredis
            self._redis = await aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    def _key(self, call_id: uuid.UUID) -> str:
        return f"{_KEY_PREFIX}{call_id}"

    async def save(self, state: "InterviewState") -> None:  # noqa: F821
        from cati.interview.state import InterviewState
        r = await self._get_redis()
        data = state.model_dump_json()
        await r.set(self._key(state.call_id), data, ex=_TTL_SECONDS)
        log.debug("session_saved", call_id=str(state.call_id))

    async def load(self, call_id: uuid.UUID) -> "InterviewState | None":  # noqa: F821
        from cati.interview.state import InterviewState
        r = await self._get_redis()
        data = await r.get(self._key(call_id))
        if data is None:
            return None
        state = InterviewState.model_validate_json(data)
        log.debug("session_loaded", call_id=str(call_id))
        return state

    async def delete(self, call_id: uuid.UUID) -> None:
        r = await self._get_redis()
        await r.delete(self._key(call_id))

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()
            self._redis = None


def get_session_manager() -> SessionManager:
    from config.settings import get_settings
    return SessionManager(redis_url=get_settings().db.redis_url)
