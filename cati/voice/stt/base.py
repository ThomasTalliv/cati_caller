"""Abstract STT provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    text: str
    confidence: float | None = None
    language: str | None = None
    duration_s: float | None = None


class STTProvider(ABC):
    """Transcribe PCM audio to text.

    All providers accept 16-bit signed PCM at 16 kHz (mono).
    """

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> TranscriptionResult:
        """Transcribe a complete audio buffer.

        Args:
            audio_bytes: 16-bit signed PCM at 16 kHz mono.

        Returns:
            TranscriptionResult with text and optional metadata.
        """

    @abstractmethod
    async def transcribe_stream(self, audio_bytes: bytes) -> TranscriptionResult:
        """Transcribe a streaming audio chunk.

        Implementations accumulate context across calls within the same session.
        """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""
