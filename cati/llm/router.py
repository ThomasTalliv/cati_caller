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


def _build_provider(provider: str, llm_settings, *, model_override: str = "") -> LLMProvider:
    """Instantiate a single LLM provider, optionally with a model override."""
    if provider == "anthropic":
        from cati.llm.anthropic_provider import AnthropicProvider
        model = model_override or llm_settings.anthropic_model
        return AnthropicProvider(
            api_key=llm_settings.anthropic_api_key,
            model=model,
            max_tokens=llm_settings.max_tokens,
            temperature=llm_settings.temperature,
        )
    else:
        from cati.llm.openai_provider import OpenAIProvider
        model = model_override or llm_settings.openai_model
        return OpenAIProvider(
            api_key=llm_settings.openai_api_key,
            model=model,
            temperature=llm_settings.temperature,
        )


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """Build and cache the primary (analysis) LLM provider."""
    from config.settings import get_settings
    llm = get_settings().llm
    primary = _build_provider(llm.primary_provider, llm)
    fallback: LLMProvider | None = None
    other = "openai" if llm.primary_provider == "anthropic" else "anthropic"
    other_key = llm.openai_api_key if other == "openai" else llm.anthropic_api_key
    if other_key:
        fallback = _build_provider(other, llm)
    return RouterLLMProvider(primary=primary, fallback=fallback)


@lru_cache(maxsize=1)
def get_parsing_llm_provider() -> LLMProvider:
    """Build and cache the cheap parsing LLM provider.

    If LLM__PARSING_MODEL is set, uses that model (e.g. claude-haiku-4-5-20251001
    or gpt-4o-mini). Falls back to the primary provider when not configured.
    """
    from config.settings import get_settings
    llm = get_settings().llm
    if not llm.parsing_model:
        # No separate parsing model configured — share the primary provider
        return get_llm_provider()
    primary = _build_provider(llm.primary_provider, llm, model_override=llm.parsing_model)
    return RouterLLMProvider(primary=primary, fallback=None)
