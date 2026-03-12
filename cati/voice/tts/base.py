"""Abstract TTS provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class TTSProvider(ABC):
    """Synthesize text to raw PCM audio bytes.

    All providers must produce 16-bit signed PCM at 8 kHz (telephone quality)
    or 16 kHz (wideband). The telephony layer resamples as needed.
    """

    @abstractmethod
    async def synthesize(self, text: str, *, voice: str | None = None) -> bytes:
        """Synthesize text and return complete PCM audio bytes."""

    @abstractmethod
    async def synthesize_stream(
        self, text: str, *, voice: str | None = None
    ) -> AsyncIterator[bytes]:
        """Synthesize text and yield PCM chunks as they are generated.

        Must yield at least one chunk. Implementations should aim to yield
        the first chunk within 200ms for acceptable call latency.
        """
        # Make this an async generator by design
        raise NotImplementedError
        yield b""  # pragma: no cover

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """Output sample rate in Hz (e.g. 8000 or 16000)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""
