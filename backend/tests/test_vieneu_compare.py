"""Offline VieNeu A/B manifest contracts; no model, speech or human verdict mocked."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import wave
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "review-tts" / "compare.py"
spec = importlib.util.spec_from_file_location("vieneu_compare", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _trial(root: Path, voice: str, narration: str = "Áo ướt sẽ khô.") -> Path:
    root.mkdir(parents=True)
    (root / "audio").mkdir()
    wav_file = root / "audio" / "scene-01.wav"
    with wave.open(str(wav_file), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(48000)
        wav.writeframes(b"\0\0" * 4800)
    sha = hashlib.sha256(wav_file.read_bytes()).hexdigest()
    story = {"scenes": [{"title": "Áo ướt", "narration": narration}]}
    provenance = {
        "sdk": "vieneu",
        "version": "3.8.3",
        "voice": voice,
        "models": [{"repository": "pnnbao-ump/VieNeu-TTS-v3-Turbo", "revision": "pinned", "license": "apache-2.0"}],
        "records": [{"narration": narration, "file": "audio/scene-01.wav", "sha256": sha}],
    }
    files = []
    for aspect in ("portrait", "landscape"):
        video = root / f"review-{aspect}.mp4"
        video.write_bytes(b"fixture-only-contract-not-real-video")
        files.append(
            {
                "aspect": aspect,
                "sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
                "full_decode": "passed",
            }
        )
    verification = {
        "files": files,
        "asr": [
            {
                "scene": 1,
                "expected": narration,
                "recognized": narration,
                "token_sequence_similarity": 1.0,
                "needs_listening_review": False,
            }
        ],
    }
    for name, value in (
        ("story.json", story),
        ("tts-provenance.json", provenance),
        ("verification.json", verification),
    ):
        (root / name).write_text(json.dumps(value, ensure_ascii=False))
    return root


def test_two_pinned_vieneu_trials_require_manual_listening_even_when_asr_matches(tmp_path):
    a = _trial(tmp_path / "a", "Hải Đăng")
    b = _trial(tmp_path / "b", "Minh Quân")
    report = module.compare_trials(a, b)
    assert report["source"].startswith("VieNeu")
    assert report["winner"] is None
    assert "PENDING" in report["human_listening"]
    assert report["same_story"]
    assert report["scenes"][0]["candidate_minus_baseline_asr"] == 0
    assert report["scenes"][0]["manual_listening"]["naturalness"] is None


def test_ab_rejects_different_narration_even_if_same_scene_count(tmp_path):
    a = _trial(tmp_path / "a", "Hải Đăng")
    b = _trial(tmp_path / "b", "Minh Quân", "Áo vừa giặt còn ướt.")
    with pytest.raises(ValueError, match="identical scripts"):
        module.compare_trials(a, b)


def test_ab_rejects_modified_voice_wav_and_model_license(tmp_path):
    a = _trial(tmp_path / "a", "Hải Đăng")
    wav_file = a / "audio" / "scene-01.wav"
    wav_file.write_bytes(wav_file.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="Modified"):
        module.load_trial(a)

    b = _trial(tmp_path / "b", "Minh Quân")
    path = b / "tts-provenance.json"
    data = json.loads(path.read_text())
    data["models"][0]["license"] = "unknown"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="pinned VieNeu"):
        module.load_trial(b)


def test_ab_rejects_unverified_or_missing_export(tmp_path):
    a = _trial(tmp_path / "a", "Hải Đăng")
    (a / "review-portrait.mp4").unlink()
    with pytest.raises(ValueError, match="Evidence path"):
        module.load_trial(a)


def test_ab_rejects_audio_path_escape_and_symlinks(tmp_path):
    a = _trial(tmp_path / "a", "Hải Đăng")
    path = a / "tts-provenance.json"
    data = json.loads(path.read_text())
    data["records"][0]["file"] = "audio/../story.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="unavailable or unsafe"):
        module.load_trial(a)
