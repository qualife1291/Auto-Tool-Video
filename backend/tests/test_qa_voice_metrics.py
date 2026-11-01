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


def test_quiet_padding_does_not_hide_fast_audio_span(tmp_path):
    path = tmp_path / "padded.wav"
    sound = [round(7000 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(8320)]
    _write_wav(path, [0] * 3840 + sound + [0] * 3840)
    report = metrics.measure_voice_wav(path, "Chờ đèn đi bộ")
    assert report["units_per_minute"] == 120.0
    assert report["leading_quiet_seconds"] == 0.48
    assert report["trailing_quiet_seconds"] == 0.48
    assert report["speech_span_seconds"] == 1.04
    assert report["speech_span_units_per_minute"] == 230.8
    assert report["longest_quiet_seconds"] == 0.48
    assert "NOT lexical WPM" in report["speech_span_basis"]


def test_internal_quiet_pause_remains_inside_speech_span(tmp_path):
    path = tmp_path / "internal-pause.wav"
    tone = [round(7000 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(3200)]
    _write_wav(path, tone + [0] * 6400 + tone)
    report = metrics.measure_voice_wav(path, "Một hai ba bốn")
    assert report["leading_quiet_seconds"] == 0
    assert report["trailing_quiet_seconds"] == 0
    assert report["longest_quiet_seconds"] == 0.8
    assert report["speech_span_seconds"] == 1.6


def test_fully_quiet_audio_does_not_divide_by_zero(tmp_path):
    path = tmp_path / "all-quiet.wav"
    _write_wav(path, [0] * 8000)
    report = metrics.measure_voice_wav(path, "Xin chào")
    assert report["speech_span_seconds"] == 0
    assert report["speech_span_units_per_minute"] is None
    assert report["leading_quiet_seconds"] == 1
    assert report["trailing_quiet_seconds"] == 1
    assert "ALL_WINDOWS_QUIET" in report["audio_warnings"]


def test_partial_final_window_counts_actual_samples(tmp_path):
    path = tmp_path / "partial-tail.wav"
    tone = [round(7000 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(320)]
    _write_wav(path, tone + [0] * 160)
    report = metrics.measure_voice_wav(path, "Xin")
    assert report["duration"] == 0.06
    assert report["trailing_quiet_seconds"] == 0.02
    assert report["speech_span_seconds"] == 0.04
