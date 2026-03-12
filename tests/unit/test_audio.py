"""Unit tests for audio utilities."""
import struct

import pytest

from cati.utils.audio import chunk_audio, compute_rms, pcm_to_wav, resample_pcm, wav_to_pcm


def _make_pcm(n_samples: int = 100, value: int = 1000) -> bytes:
    """Create a constant-value 16-bit PCM buffer."""
    return struct.pack(f"<{n_samples}h", *([value] * n_samples))


class TestPcmWavRoundtrip:
    def test_pcm_to_wav_returns_bytes(self):
        pcm = _make_pcm(160)
        wav = pcm_to_wav(pcm, sample_rate=16000)
        assert isinstance(wav, bytes)
        assert wav[:4] == b"RIFF"

    def test_wav_to_pcm_roundtrip(self):
        pcm = _make_pcm(160)
        wav = pcm_to_wav(pcm, sample_rate=16000)
        recovered_pcm, rate = wav_to_pcm(wav)
        assert rate == 16000
        assert recovered_pcm == pcm

    def test_different_sample_rates(self):
        pcm = _make_pcm(240)
        wav = pcm_to_wav(pcm, sample_rate=8000)
        _, rate = wav_to_pcm(wav)
        assert rate == 8000


class TestResamplePcm:
    def test_same_rate_returns_input(self):
        pcm = _make_pcm(100)
        result = resample_pcm(pcm, 16000, 16000)
        assert result == pcm

    def test_upsample_doubles_length(self):
        pcm = _make_pcm(100)
        result = resample_pcm(pcm, 8000, 16000)
        n_samples = len(result) // 2
        assert n_samples == 200

    def test_downsample_halves_length(self):
        pcm = _make_pcm(200)
        result = resample_pcm(pcm, 16000, 8000)
        n_samples = len(result) // 2
        assert n_samples == 100


class TestChunkAudio:
    def test_chunks_correct_count(self):
        # 1 second at 16kHz = 16000 samples = 32000 bytes; 20ms chunks = 50 chunks
        pcm = _make_pcm(16000)
        chunks = chunk_audio(pcm, chunk_ms=20, sample_rate=16000)
        assert len(chunks) == 50

    def test_each_chunk_size(self):
        pcm = _make_pcm(16000)
        chunks = chunk_audio(pcm, chunk_ms=20, sample_rate=16000)
        expected = 16000 * 20 // 1000 * 2  # 640 bytes
        for chunk in chunks:
            assert len(chunk) == expected


class TestComputeRms:
    def test_silence_returns_zero(self):
        pcm = _make_pcm(100, value=0)
        assert compute_rms(pcm) == 0.0

    def test_nonzero_signal(self):
        pcm = _make_pcm(100, value=16384)
        rms = compute_rms(pcm)
        assert 0.0 < rms <= 1.0

    def test_empty_returns_zero(self):
        assert compute_rms(b"") == 0.0
