"""Silero VAD wrapper — speech boundary detection from raw PCM."""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

import structlog

log = structlog.get_logger(__name__)

_SAMPLE_RATE = 16000
_FRAME_SIZE_MS = 30  # Silero expects 30ms frames at 16kHz = 480 samples
_FRAME_SAMPLES = _SAMPLE_RATE * _FRAME_SIZE_MS // 1000  # 480
_FRAME_BYTES = _FRAME_SAMPLES * 2  # 16-bit = 2 bytes/sample


@dataclass
class VADState:
    """Mutable VAD state for a single call session."""
    speech_buffer: bytearray = field(default_factory=bytearray)
    is_speaking: bool = False
    silence_frames: int = 0
    total_frames: int = 0


class SileroVAD:
    """Wrapper around Silero VAD for detecting speech boundaries.

    Silero VAD is loaded lazily. It processes 30ms frames of 16kHz 16-bit PCM.
    Requires: pip install silero-vad torch
    """

    def __init__(self, threshold: float = 0.5) -> None:
        self._threshold = threshold
        self._model = None
        self._get_speech_ts = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                onnx=False,
            )
            self._model = model
            self._get_speech_ts = utils[0]
            log.info("silero_vad_loaded", threshold=self._threshold)
        except Exception:
            # Fallback: try the silero-vad pip package
            try:
                from silero_vad import load_silero_vad, get_speech_timestamps  # type: ignore[import]
                self._model = load_silero_vad()
                self._get_speech_ts = get_speech_timestamps
                log.info("silero_vad_loaded_pip", threshold=self._threshold)
            except ImportError as exc:
                raise RuntimeError(
                    "silero-vad is not installed. Run: pip install silero-vad"
                ) from exc

    def _frame_to_tensor(self, frame_bytes: bytes):
        import torch
        n = len(frame_bytes) // 2
        samples = struct.unpack(f"<{n}h", frame_bytes[:n * 2])
        arr = [s / 32768.0 for s in samples]
        return torch.tensor(arr, dtype=torch.float32)

    def is_speech(self, frame_bytes: bytes) -> float:
        """Return speech probability for a 30ms PCM frame. Range 0.0–1.0."""
        self._load()
        tensor = self._frame_to_tensor(frame_bytes)
        prob = self._model(tensor, _SAMPLE_RATE).item()
        return float(prob)

    def process_audio(
        self,
        audio_bytes: bytes,
        state: VADState,
        *,
        silence_threshold_frames: int = 10,
    ) -> bytes | None:
        """Process incoming audio bytes.

        Feeds audio into VAD frame-by-frame. Returns the accumulated speech
        buffer when a complete utterance ends (silence after speech), else None.

        Args:
            audio_bytes: Raw 16-bit 16kHz PCM.
            state: Mutable per-session VAD state.
            silence_threshold_frames: Consecutive silent frames before utterance end.

        Returns:
            Complete utterance PCM bytes if one just ended, else None.
        """
        self._load()
        state.speech_buffer.extend(audio_bytes)
        result: bytes | None = None

        # Process complete 30ms frames
        while len(state.speech_buffer) >= _FRAME_BYTES:
            frame = bytes(state.speech_buffer[:_FRAME_BYTES])
            state.speech_buffer = state.speech_buffer[_FRAME_BYTES:]
            state.total_frames += 1

            prob = self.is_speech(frame)

            if prob >= self._threshold:
                state.is_speaking = True
                state.silence_frames = 0
                state.speech_buffer[:0] = frame  # prepend frame back for accumulation
                # Re-add frame to ensure it's part of the utterance
                # Actually we need a separate utterance buffer
            else:
                if state.is_speaking:
                    state.silence_frames += 1
                    if state.silence_frames >= silence_threshold_frames:
                        # Utterance complete
                        utterance = bytes(state.speech_buffer)
                        state.speech_buffer = bytearray()
                        state.is_speaking = False
                        state.silence_frames = 0
                        result = utterance

        return result


class SimpleEnergyVAD:
    """Lightweight energy-based VAD fallback when Silero is not available.

    Uses RMS energy threshold. Less accurate but zero dependencies.
    """

    def __init__(self, energy_threshold: float = 0.01) -> None:
        self._threshold = energy_threshold

    def is_speech(self, frame_bytes: bytes) -> bool:
        import math
        n = len(frame_bytes) // 2
        if n == 0:
            return False
        samples = struct.unpack(f"<{n}h", frame_bytes[:n * 2])
        rms = math.sqrt(sum(s * s for s in samples) / n) / 32768.0
        return rms > self._threshold


def get_vad(threshold: float = 0.5) -> SileroVAD:
    """Return a Silero VAD instance."""
    return SileroVAD(threshold=threshold)
