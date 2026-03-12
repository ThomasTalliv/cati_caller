"""TTS provider factory."""
from __future__ import annotations

from cati.voice.tts.base import TTSProvider


def get_tts_provider() -> TTSProvider:
    """Return the configured TTS provider."""
    from config.settings import get_settings
    settings = get_settings()
    provider = settings.tts.provider

    if provider == "kokoro":
        from cati.voice.tts.kokoro_provider import KokoroTTSProvider
        return KokoroTTSProvider(
            model=settings.tts.kokoro_model,
            voice=settings.tts.kokoro_voice,
            device=settings.tts.kokoro_device,
        )
    elif provider == "xtts":
        from cati.voice.tts.xtts_provider import XTTSProvider
        return XTTSProvider(
            model_path=settings.tts.xtts_model_path,
            voice_sample_path=settings.tts.voice_sample_path,
            device=settings.tts.kokoro_device,
        )
    else:
        raise ValueError(f"Unknown TTS provider: {provider!r}")
