"""OpenAI GPT LLM provider."""
from __future__ import annotations

from collections.abc import AsyncIterator

from cati.llm.base import LLMProvider, Message


class OpenAIProvider(LLMProvider):
    """OpenAI GPT via the official openai SDK."""

    def __init__(self, api_key: str, model: str = "gpt-4o", max_tokens: int = 4096, temperature: float = 0.3) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self._api_key)
        return self._client

    async def complete(self, messages: list[Message], *, max_tokens: int = 1024) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            max_tokens=max_tokens,
            temperature=self._temperature,
        )
        return response.choices[0].message.content or ""

    async def stream(
        self, messages: list[Message], *, max_tokens: int = 1024
    ) -> AsyncIterator[str]:
        client = self._get_client()
        async with client.chat.completions.stream(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            max_tokens=max_tokens,
            temperature=self._temperature,
        ) as stream_ctx:
            async for chunk in stream_ctx:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model
