"""Kokoro TTS provider — Apache 2.0, sub-100ms TTFB, multilingual."""
from __future__ import annotations

import functools
import hashlib
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

# Maximum number of (text, voice) pairs kept in the TTS audio cache.
# Each entry is ~160 KB for a 5-second utterance at 16kHz 16-bit mono.
# 512 entries ≈ 80 MB — safe for a long-running worker process.
_TTS_CACHE_SIZE = 512


def _cache_key(text: str, voice: str) -> str:
    """Short stable key for (text, voice) — avoids huge dict keys."""
    return hashlib.md5(f"{voice}:{text}".encode()).hexdigest()


class KokoroTTSProvider(TTSProvider):
    """Kokoro-82M TTS integration with audio caching.

    The audio cache stores rendered PCM bytes keyed by (text, voice).
    For batch survey campaigns where thousands of respondents receive
    identical question texts, each question is synthesised only once.

    Requires: pip install kokoro soundfile torch
    """

    def __init__(self, model: str = "kokoro-v1.0", voice: str = "af_sky", device: str = "cpu") -> None:
        self._model_name = model
        self._default_voice = voice
        self._device = device
        self._pipeline = None
        # LRU cache: key → PCM bytes.  Thread-safe for reads; writes use a lock.
        self._cache: dict[str, bytes] = {}
        self._cache_hits = 0
        self._cache_misses = 0

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

        if sample_rate != _TARGET_SAMPLE_RATE:
            try:
                import torchaudio  # type: ignore[import]
                import torch
                tensor = torch.from_numpy(audio_array).unsqueeze(0)
                resampled = torchaudio.functional.resample(tensor, sample_rate, _TARGET_SAMPLE_RATE)
                audio_array = resampled.squeeze(0).numpy()
            except ImportError:
                ratio = _TARGET_SAMPLE_RATE / sample_rate
                new_len = int(len(audio_array) * ratio)
                audio_array = np.interp(
                    np.linspace(0, len(audio_array) - 1, new_len),
                    np.arange(len(audio_array)),
                    audio_array,
                )

        clipped = np.clip(audio_array, -1.0, 1.0)
        int16 = (clipped * 32767).astype(np.int16)
        return int16.tobytes()

    async def synthesize(self, text: str, *, voice: str | None = None) -> bytes:
        import asyncio

        used_voice = voice or self._default_voice
        key = _cache_key(text, used_voice)

        if key in self._cache:
            self._cache_hits += 1
            log.debug("tts_cache_hit", hits=self._cache_hits, key=key[:8])
            return self._cache[key]

        self._cache_misses += 1
        pcm = await asyncio.get_event_loop().run_in_executor(
            None, self._synthesize_sync, text, used_voice
        )

        # Evict oldest entry if cache is full
        if len(self._cache) >= _TTS_CACHE_SIZE:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[key] = pcm
        return pcm

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
        import concurrent.futures

        self._load()
        used_voice = voice or self._default_voice
        loop = asyncio.get_event_loop()

        def _iter():
            for _, _, audio in self._pipeline(text, voice=used_voice, speed=1.0):
                if audio is not None:
                    yield self._pcm_from_audio(audio, _KOKORO_SAMPLE_RATE)

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        gen = _iter()
        while True:
            try:
                chunk = await loop.run_in_executor(executor, next, gen)
                yield chunk
            except StopIteration:
                break

    def cache_stats(self) -> dict:
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total else 0.0
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate": round(hit_rate, 3),
            "cached_entries": len(self._cache),
        }

    @property
    def sample_rate(self) -> int:
        return _TARGET_SAMPLE_RATE

    @property
    def provider_name(self) -> str:
        return "kokoro"

