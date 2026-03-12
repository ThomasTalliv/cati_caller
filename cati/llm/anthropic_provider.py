"""Anthropic Claude LLM provider."""
from __future__ import annotations

from collections.abc import AsyncIterator

import structlog

from cati.llm.base import LLMProvider, Message

log = structlog.get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """Claude API via the official anthropic SDK."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6", max_tokens: int = 4096, temperature: float = 0.3) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._client

    def _build_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """Split system prompt from messages list."""
        system = None
        chat: list[dict] = []
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                chat.append({"role": msg.role, "content": msg.content})
        return system, chat

    async def complete(self, messages: list[Message], *, max_tokens: int = 1024) -> str:
        client = self._get_client()
        system, chat = self._build_messages(messages)
        kwargs: dict = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": chat,
            "temperature": self._temperature,
        }
        if system:
            kwargs["system"] = system

        response = await client.messages.create(**kwargs)
        return response.content[0].text

    async def stream(
        self, messages: list[Message], *, max_tokens: int = 1024
    ) -> AsyncIterator[str]:
        client = self._get_client()
        system, chat = self._build_messages(messages)
        kwargs: dict = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": chat,
            "temperature": self._temperature,
        }
        if system:
            kwargs["system"] = system

        async with client.messages.stream(**kwargs) as stream_ctx:
            async for text in stream_ctx.text_stream:
                yield text

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model
