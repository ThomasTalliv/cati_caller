"""STT provider factory."""
from __future__ import annotations

from cati.voice.stt.base import STTProvider


def get_stt_provider() -> STTProvider:
    """Return the configured STT provider."""
    from config.settings import get_settings
    settings = get_settings()

    from cati.voice.stt.faster_whisper_provider import FasterWhisperProvider
    return FasterWhisperProvider(
        model_size=settings.stt.model_size,
        device=settings.stt.device,
        compute_type=settings.stt.compute_type,
        language=settings.stt.language,
    )
