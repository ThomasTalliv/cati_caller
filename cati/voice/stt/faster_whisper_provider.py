"""faster-whisper STT provider — 4× faster than Whisper, local inference."""
from __future__ import annotations

import io
import struct
import wave

import numpy as np
import structlog

from cati.voice.stt.base import STTProvider, TranscriptionResult

log = structlog.get_logger(__name__)

_SAMPLE_RATE = 16000
_SAMPLE_WIDTH = 2  # 16-bit


class FasterWhisperProvider(STTProvider):
    """faster-whisper integration for real-time CATI call transcription.

    Requires: pip install faster-whisper
    Loads the model lazily on first use.
    """

    def __init__(
        self,
        model_size: str = "large-v3-turbo",
        device: str = "cpu",
        compute_type: str = "float32",
        language: str = "en",
    ) -> None:
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._language = language
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel  # type: ignore[import]
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )
            log.info(
                "faster_whisper_loaded",
                model=self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed. Run: pip install faster-whisper"
            ) from exc

    def _pcm_to_float32(self, pcm_bytes: bytes) -> np.ndarray:
        """Convert 16-bit PCM bytes to float32 numpy array [-1, 1]."""
        n = len(pcm_bytes) // _SAMPLE_WIDTH
        samples = struct.unpack(f"<{n}h", pcm_bytes[:n * _SAMPLE_WIDTH])
        return np.array(samples, dtype=np.float32) / 32768.0

    async def transcribe(self, audio_bytes: bytes) -> TranscriptionResult:
        import asyncio

        return await asyncio.get_event_loop().run_in_executor(
            None, self._transcribe_sync, audio_bytes
        )

    def _transcribe_sync(self, audio_bytes: bytes) -> TranscriptionResult:
        self._load()
        audio = self._pcm_to_float32(audio_bytes)
        if len(audio) == 0:
            return TranscriptionResult(text="")

        segments, info = self._model.transcribe(
            audio,
            language=self._language,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return TranscriptionResult(
            text=text,
            language=info.language,
            confidence=getattr(info, "language_probability", None),
            duration_s=len(audio) / _SAMPLE_RATE,
        )

    async def transcribe_stream(self, audio_bytes: bytes) -> TranscriptionResult:
        # faster-whisper processes entire buffers; stream == batch for now
        return await self.transcribe(audio_bytes)

    @property
    def provider_name(self) -> str:
        return "faster_whisper"
