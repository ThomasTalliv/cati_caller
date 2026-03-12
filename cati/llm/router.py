"""LLM provider router — selection and fallback logic."""
from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

import structlog

from cati.llm.base import LLMProvider, Message

log = structlog.get_logger(__name__)


class RouterLLMProvider(LLMProvider):
    """Routes to primary LLM provider with fallback to secondary."""

    def __init__(self, primary: LLMProvider, fallback: LLMProvider | None = None) -> None:
        self._primary = primary
        self._fallback = fallback

    async def complete(self, messages: list[Message], *, max_tokens: int = 1024) -> str:
        try:
            return await self._primary.complete(messages, max_tokens=max_tokens)
        except Exception as exc:
            if self._fallback:
                log.warning("llm_primary_failed_falling_back", error=str(exc), provider=self._primary.provider_name)
                return await self._fallback.complete(messages, max_tokens=max_tokens)
            raise

    async def stream(
        self, messages: list[Message], *, max_tokens: int = 1024
    ) -> AsyncIterator[str]:
        try:
            async for token in self._primary.stream(messages, max_tokens=max_tokens):
                yield token
        except Exception as exc:
            if self._fallback:
                log.warning("llm_stream_primary_failed", error=str(exc))
                async for token in self._fallback.stream(messages, max_tokens=max_tokens):
                    yield token
            else:
                raise

    @property
    def provider_name(self) -> str:
        return f"router({self._primary.provider_name})"

    @property
    def model_name(self) -> str:
        return self._primary.model_name


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """Build and cache the configured LLM provider."""
    from config.settings import get_settings
    settings = get_settings()
    llm = settings.llm

    primary: LLMProvider
    fallback: LLMProvider | None = None

    if llm.primary_provider == "anthropic":
        from cati.llm.anthropic_provider import AnthropicProvider
        primary = AnthropicProvider(
            api_key=llm.anthropic_api_key,
            model=llm.anthropic_model,
            max_tokens=llm.max_tokens,
            temperature=llm.temperature,
        )
        if llm.openai_api_key:
            from cati.llm.openai_provider import OpenAIProvider
            fallback = OpenAIProvider(
                api_key=llm.openai_api_key,
                model=llm.openai_model,
                temperature=llm.temperature,
            )
    else:
        from cati.llm.openai_provider import OpenAIProvider
        primary = OpenAIProvider(
            api_key=llm.openai_api_key,
            model=llm.openai_model,
            temperature=llm.temperature,
        )
        if llm.anthropic_api_key:
            from cati.llm.anthropic_provider import AnthropicProvider
            fallback = AnthropicProvider(
                api_key=llm.anthropic_api_key,
                model=llm.anthropic_model,
                temperature=llm.temperature,
            )

    return RouterLLMProvider(primary=primary, fallback=fallback)
