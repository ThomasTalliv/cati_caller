"""Audio conversion utilities — PCM ↔ WAV, resampling helpers."""
from __future__ import annotations

import io
import struct
import wave


def pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 16000, channels: int = 1) -> bytes:
    """Wrap raw 16-bit PCM bytes in a WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


def wav_to_pcm(wav_bytes: bytes) -> tuple[bytes, int]:
    """Extract raw PCM bytes from a WAV file.

    Returns:
        Tuple of (pcm_bytes, sample_rate).
    """
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        sample_rate = wf.getframerate()
        pcm = wf.readframes(wf.getnframes())
    return pcm, sample_rate


def resample_pcm(pcm_bytes: bytes, src_rate: int, dst_rate: int) -> bytes:
    """Simple linear interpolation resampler for 16-bit mono PCM."""
    if src_rate == dst_rate:
        return pcm_bytes

    n = len(pcm_bytes) // 2
    samples = struct.unpack(f"<{n}h", pcm_bytes[:n * 2])

    ratio = dst_rate / src_rate
    new_n = int(n * ratio)
    out = []
    for i in range(new_n):
        src_pos = i / ratio
        src_idx = int(src_pos)
        frac = src_pos - src_idx
        s0 = samples[min(src_idx, n - 1)]
        s1 = samples[min(src_idx + 1, n - 1)]
        out.append(int(s0 + frac * (s1 - s0)))

    return struct.pack(f"<{new_n}h", *out)


def chunk_audio(pcm_bytes: bytes, chunk_ms: int = 20, sample_rate: int = 16000) -> list[bytes]:
    """Split PCM bytes into fixed-size chunks for streaming."""
    chunk_bytes = sample_rate * chunk_ms // 1000 * 2  # 16-bit = 2 bytes
    return [pcm_bytes[i : i + chunk_bytes] for i in range(0, len(pcm_bytes), chunk_bytes)]


def compute_rms(pcm_bytes: bytes) -> float:
    """Compute RMS amplitude of 16-bit PCM, normalised to 0.0–1.0."""
    import math
    n = len(pcm_bytes) // 2
    if n == 0:
        return 0.0
    samples = struct.unpack(f"<{n}h", pcm_bytes[:n * 2])
    return math.sqrt(sum(s * s for s in samples) / n) / 32768.0
