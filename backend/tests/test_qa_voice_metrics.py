"""Actual PCM regression for Vietnamese voice QA evidence."""

from __future__ import annotations

import importlib.util
import math
import struct
import wave
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "qa_voice_metrics.py"
spec = importlib.util.spec_from_file_location("qa_voice_metrics", MODULE_PATH)
assert spec is not None and spec.loader is not None
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


def _write_wav(path: Path, samples: list[int], *, channels: int = 1, width: int = 2):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(width)
        wav.setframerate(8000)
        wav.writeframes(struct.pack("<" + "h" * len(samples), *samples))


def test_vietnamese_whitespace_units_not_lexical_words(tmp_path):
    path = tmp_path / "tone.wav"
    _write_wav(path, [round(10000 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(8000)])
    report = metrics.measure_voice_wav(path, "Thành phố")
    assert report["duration"] == 1
    assert report["space_delimited_units"] == 2
    assert report["units_per_minute"] == 120
    assert "words" in report["pace_basis"]
    assert "effective_wpm" not in report
    assert report["voice_review"] == "NOT RUN"
    assert -11 <= report["peak_dbfs"] <= -10
    assert report["quiet_window_fraction"] == 0
    assert report["audio_warnings"] == []


def test_quiet_windows_are_not_single_sample_zero_crossings(tmp_path):
    path = tmp_path / "pause.wav"
    samples = [0] * 4000 + [
        round(4000 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(4000)
    ]
    _write_wav(path, samples)
    report = metrics.measure_voice_wav(path, "Xin chào")
    assert 0.48 <= report["quiet_window_fraction"] <= 0.52
    assert report["near_full_scale_samples"] == 0
    assert report["peak_dbfs"] < 0


def test_full_scale_warning_is_not_human_approval(tmp_path):
    path = tmp_path / "loud.wav"
    _write_wav(path, [32767] * 8000)
    report = metrics.measure_voice_wav(path, "Rất to")
    assert report["near_full_scale_samples"] == 8000
    assert report["audio_warnings"] == ["NEAR_FULL_SCALE_SAMPLES"]
    assert report["voice_review"] == "NOT RUN"


def test_silence_and_zero_frames(tmp_path):
    silent = tmp_path / "silent.wav"
    _write_wav(silent, [0] * 800)
    report = metrics.measure_voice_wav(silent, "Im lặng")
    assert report["peak_dbfs"] is None
    assert report["quiet_window_fraction"] == 1
    assert "ALL_WINDOWS_QUIET" in report["audio_warnings"]
    empty = tmp_path / "empty.wav"
    _write_wav(empty, [])
    with pytest.raises(ValueError, match="no audio frames"):
        metrics.measure_voice_wav(empty, "")


def test_rejects_wrong_channels(tmp_path):
    path = tmp_path / "stereo.wav"
    _write_wav(path, [100] * 160, channels=2)
    with pytest.raises(ValueError, match="mono PCM16"):
        metrics.measure_voice_wav(path, "a")
