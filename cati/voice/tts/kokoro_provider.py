"""Kokoro TTS provider — Apache 2.0, sub-100ms TTFB, multilingual."""
from __future__ import annotations

import io
import struct
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import structlog

from cati.voice.tts.base import TTSProvider

if TYPE_CHECKING:
    pass

log = structlog.get_logger(__name__)

# Kokoro sample rate
_KOKORO_SAMPLE_RATE = 24000  # kokoro outputs 24kHz
_TARGET_SAMPLE_RATE = 16000  # target for telephony


class KokoroTTSProvider(TTSProvider):
    """Kokoro-82M TTS integration.

    Kokoro is loaded lazily on first use to avoid GPU initialisation at import.
    Requires: pip install kokoro soundfile torch
    """

    def __init__(self, model: str = "kokoro-v1.0", voice: str = "af_sky", device: str = "cpu") -> None:
        self._model_name = model
        self._default_voice = voice
        self._device = device
        self._pipeline = None

    def _load(self) -> None:
        if self._pipeline is not None:
            return
        try:
            from kokoro import KPipeline  # type: ignore[import]
            lang_code = "a"  # American English default; overridden per-voice
            self._pipeline = KPipeline(lang_code=lang_code, device=self._device)
            log.info("kokoro_loaded", model=self._model_name, device=self._device)
        except ImportError as exc:
            raise RuntimeError(
                "Kokoro is not installed. Run: pip install kokoro torch"
            ) from exc

    def _pcm_from_audio(self, audio_array, sample_rate: int) -> bytes:
        """Convert numpy float32 array to 16-bit PCM bytes, resampled to 16 kHz."""
        import numpy as np

        # Resample if needed
        if sample_rate != _TARGET_SAMPLE_RATE:
            try:
                import torchaudio  # type: ignore[import]
                import torch
                tensor = torch.from_numpy(audio_array).unsqueeze(0)
                resampled = torchaudio.functional.resample(tensor, sample_rate, _TARGET_SAMPLE_RATE)
                audio_array = resampled.squeeze(0).numpy()
            except ImportError:
                # Fallback: simple linear interpolation resample
                ratio = _TARGET_SAMPLE_RATE / sample_rate
                new_len = int(len(audio_array) * ratio)
                audio_array = np.interp(
                    np.linspace(0, len(audio_array) - 1, new_len),
                    np.arange(len(audio_array)),
                    audio_array,
                )

        # Clip and convert to int16
        clipped = np.clip(audio_array, -1.0, 1.0)
        int16 = (clipped * 32767).astype(np.int16)
        return int16.tobytes()

    async def synthesize(self, text: str, *, voice: str | None = None) -> bytes:
        import asyncio

        return await asyncio.get_event_loop().run_in_executor(
            None, self._synthesize_sync, text, voice or self._default_voice
        )

    def _synthesize_sync(self, text: str, voice: str) -> bytes:
        self._load()
        chunks: list[bytes] = []
        for _, _, audio in self._pipeline(text, voice=voice, speed=1.0):
            if audio is not None:
                chunks.append(self._pcm_from_audio(audio, _KOKORO_SAMPLE_RATE))
        return b"".join(chunks)

    async def synthesize_stream(
        self, text: str, *, voice: str | None = None
    ) -> AsyncIterator[bytes]:
        import asyncio

        self._load()
        used_voice = voice or self._default_voice
        loop = asyncio.get_event_loop()

        # Kokoro generates sentence-by-sentence; yield each as a chunk
        def _iter():
            for _, _, audio in self._pipeline(text, voice=used_voice, speed=1.0):
                if audio is not None:
                    yield self._pcm_from_audio(audio, _KOKORO_SAMPLE_RATE)

        # Run generator in executor and yield results
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        gen = _iter()
        while True:
            try:
                chunk = await loop.run_in_executor(executor, next, gen)
                yield chunk
            except StopIteration:
                break

    @property
    def sample_rate(self) -> int:
        return _TARGET_SAMPLE_RATE

    @property
    def provider_name(self) -> str:
        return "kokoro"
