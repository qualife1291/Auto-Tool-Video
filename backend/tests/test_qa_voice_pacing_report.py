"""Execute the QA voice measurement with deterministic offline WAV fixtures."""

import ast
import hashlib
import math
import shutil
import subprocess
import wave
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[2] / "scripts" / "qa_video_scenarios.py"


def _voice_function():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    function = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "voice"
    )
    namespace = {
        "Path": Path,
        "shutil": shutil,
        "subprocess": subprocess,
        "wave": wave,
        "math": math,
        "COMPRESSOR": "acompressor=threshold=-25dB:ratio=3:attack=20:release=200",
        "digest": lambda path: hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace["voice"]


def _stub_voice_tools(monkeypatch, frames):
    monkeypatch.setattr(shutil, "which", lambda name: "espeak")

    def fake_run(command, **kwargs):
        if command[0] == "espeak":
            with wave.open(str(command[-2]), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(b"\\x00\\x00" * frames)
        else:
            shutil.copyfile(command[command.index("-i") + 1], command[-1])
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)


def test_voice_reports_whitespace_units_not_vietnamese_lexical_words(monkeypatch, tmp_path):
    _stub_voice_tools(monkeypatch, frames=32000)
    path = tmp_path / "voice.wav"
    result = _voice_function()("Chờ đèn đi bộ", path, 95)

    assert result["duration"] == pytest.approx(2.0)
    assert result["space_delimited_units"] == 4
    assert result["units_per_minute"] == 120.0
    assert result["voice_review"] == "NOT RUN"
    assert result["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert '"voice_approval": "NOT APPROVED"' in SOURCE.read_text(encoding="utf-8")


def test_voice_rejects_empty_wav_even_if_pcm_header_is_valid(monkeypatch, tmp_path):
    _stub_voice_tools(monkeypatch, frames=0)
    with pytest.raises(ValueError, match="no playable samples"):
        _voice_function()("Chờ đèn đi bộ", tmp_path / "empty.wav", 95)
