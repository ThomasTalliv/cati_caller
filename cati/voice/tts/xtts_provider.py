"""XTTS-v2 TTS provider — voice cloning, 17 languages."""
from __future__ import annotations

from collections.abc import AsyncIterator

import structlog

from cati.voice.tts.base import TTSProvider

log = structlog.get_logger(__name__)

_XTTS_SAMPLE_RATE = 24000
_TARGET_SAMPLE_RATE = 16000


class XTTSProvider(TTSProvider):
    """Coqui XTTS-v2 provider for voice cloning and multilingual TTS.

    Requires: pip install TTS torch
    Set VOICE_SAMPLE_PATH to a 6+ second WAV file of the target voice.
    """

    def __init__(self, model_path: str, voice_sample_path: str = "", device: str = "cpu") -> None:
        self._model_path = model_path
        self._voice_sample = voice_sample_path
        self._device = device
        self._tts = None

    def _load(self) -> None:
        if self._tts is not None:
            return
        try:
            from TTS.api import TTS  # type: ignore[import]
            self._tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2").to(self._device)
            log.info("xtts_loaded", device=self._device)
        except ImportError as exc:
            raise RuntimeError(
                "TTS package is not installed. Run: pip install TTS torch"
            ) from exc

    def _to_pcm16(self, audio, sample_rate: int) -> bytes:
        import numpy as np

        arr = np.array(audio, dtype=np.float32)
        if sample_rate != _TARGET_SAMPLE_RATE:
            ratio = _TARGET_SAMPLE_RATE / sample_rate
            new_len = int(len(arr) * ratio)
            arr = np.interp(
                np.linspace(0, len(arr) - 1, new_len), np.arange(len(arr)), arr
            )
        clipped = np.clip(arr, -1.0, 1.0)
        return (clipped * 32767).astype(np.int16).tobytes()

    async def synthesize(self, text: str, *, voice: str | None = None) -> bytes:
        import asyncio

        return await asyncio.get_event_loop().run_in_executor(
            None, self._synthesize_sync, text, voice
        )

    def _synthesize_sync(self, text: str, voice: str | None) -> bytes:
        self._load()
        wav = self._tts.tts(
            text=text,
            speaker_wav=voice or self._voice_sample or None,
            language="en",
        )
        return self._to_pcm16(wav, _XTTS_SAMPLE_RATE)

    async def synthesize_stream(
        self, text: str, *, voice: str | None = None
    ) -> AsyncIterator[bytes]:
        # XTTS doesn't support streaming natively; fall back to full synthesis
        data = await self.synthesize(text, voice=voice)
        chunk_size = 4096
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    @property
    def sample_rate(self) -> int:
        return _TARGET_SAMPLE_RATE

    @property
    def provider_name(self) -> str:
        return "xtts"
