"""Execute the QA voice adapter with deterministic offline WAV fixtures."""

import hashlib
import importlib
import math
import pathlib
import shutil
import struct
import subprocess
import wave

import pytest


SOURCE = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "qa_video_scenarios.py"


def _voice_function(monkeypatch):
    monkeypatch.syspath_prepend(str(SOURCE.parent))
    return importlib.import_module("qa_video_scenarios").voice


def _stub_voice_tools(monkeypatch, frames, *, silent=False):
    monkeypatch.setattr(shutil, "which", lambda name: "espeak")

    def fake_run(command, **kwargs):
        if command[0] == "espeak":
            with wave.open(str(command[-2]), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                samples = [
                    0 if silent else round(5000 * math.sin(2 * math.pi * 440 * i / 16000))
                    for i in range(frames)
                ]
                wav.writeframes(struct.pack("<" + "h" * frames, *samples))
        else:
            shutil.copyfile(command[command.index("-i") + 1], command[-1])
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)


def test_voice_reports_whitespace_units_not_vietnamese_lexical_words(monkeypatch, tmp_path):
    _stub_voice_tools(monkeypatch, frames=32000)
    path = tmp_path / "voice.wav"
    result = _voice_function(monkeypatch)("Chờ đèn đi bộ", path, 95)

    assert result["duration"] == pytest.approx(2.0)
    assert result["space_delimited_units"] == 4
    assert result["units_per_minute"] == 120.0
    assert result["voice_review"] == "NOT RUN"
    assert result["audio_warnings"] == []
    assert result["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert '"voice_approval": "NOT APPROVED"' in SOURCE.read_text(encoding="utf-8")


def test_voice_rejects_empty_wav_even_if_pcm_header_is_valid(monkeypatch, tmp_path):
    _stub_voice_tools(monkeypatch, frames=0)
    with pytest.raises(ValueError, match="no audio frames"):
        _voice_function(monkeypatch)("Chờ đèn đi bộ", tmp_path / "empty.wav", 95)


def test_voice_rejects_fully_silent_audio(monkeypatch, tmp_path):
    _stub_voice_tools(monkeypatch, frames=16000, silent=True)
    with pytest.raises(ValueError, match="Source voice is silent"):
        _voice_function(monkeypatch)("Chờ đèn đi bộ", tmp_path / "silent.wav", 95)
