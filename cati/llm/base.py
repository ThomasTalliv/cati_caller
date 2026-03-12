"""Abstract LLM provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMProvider(ABC):
    """Generate text completions from a language model."""

    @abstractmethod
    async def complete(self, messages: list[Message], *, max_tokens: int = 1024) -> str:
        """Return a single completion string."""

    @abstractmethod
    async def stream(
        self, messages: list[Message], *, max_tokens: int = 1024
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        yield ""  # pragma: no cover

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier string."""
