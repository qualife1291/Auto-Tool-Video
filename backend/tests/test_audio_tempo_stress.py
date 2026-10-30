"""A04 failure-atomicity and real-media regression checks."""

import hashlib
import json
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import audio_tempo


def make_wav(path: Path, seconds: float, rate: int = 24000) -> Path:
    t = np.arange(round(rate * seconds)) / rate
    samples = (np.sin(2 * np.pi * 440 * t) * 9000).astype("<i2")
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(samples.tobytes())
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_project(root: Path, durations: tuple[float, ...]) -> bytes:
    scenes = [
        {"title": f"Scene {i}", "narration": f"Đây là lời đọc {i}."}
        for i in range(len(durations))
    ]
    original = (
        json.dumps({"title": "Kiểm thử", "scenes": scenes}, ensure_ascii=False) + "\n"
    ).encode()
    (root / "story.json").write_bytes(original)
    records = []
    for index, duration in enumerate(durations):
        path = make_wav(root / f"raw-{index}.wav", duration)
        records.append(
            {
                "file": path.name,
                "sha256": digest(path),
                "narration": scenes[index]["narration"],
            }
        )
    (root / "tts-provenance.json").write_text(json.dumps({"records": records}))
    return original


def test_late_scene_failure_keeps_all_previous_audio(tmp_path):
    original = make_project(tmp_path, (1.5, 19.0))
    old = {}
    for folder in ("audio-tempo", "audio-tight"):
        path = tmp_path / folder / "scene-01.wav"
        path.parent.mkdir(parents=True, exist_ok=True)
        old[path] = b"APPROVED-VOICE-" + folder.encode()
        path.write_bytes(old[path])
    with pytest.raises(ValueError, match="scene limit"):
        audio_tempo.prepare_timeline(tmp_path)
    assert (tmp_path / "story.json").read_bytes() == original
    assert not (tmp_path / "audio-timing.json").exists()
    assert all(path.read_bytes() == data for path, data in old.items())
    assert not list(tmp_path.glob(".audio-stage-*"))


def test_mid_publish_error_rolls_back_all_audio_and_metadata(tmp_path, monkeypatch):
    original = make_project(tmp_path, (1.4, 1.6))
    old = {}
    for folder in ("audio-tight", "audio-tempo"):
        for index in (1, 2):
            path = tmp_path / folder / f"scene-{index:02}.wav"
            path.parent.mkdir(parents=True, exist_ok=True)
            old[path] = f"approved:{folder}:{index}".encode()
            path.write_bytes(old[path])
    timing = tmp_path / "audio-timing.json"
    timing.write_bytes(b'[{"approved":true}]')
    replace = audio_tempo.os.replace
    failed = False

    def fault_once(source, destination):
        nonlocal failed
        if Path(destination) == tmp_path / "story.json" and not failed:
            failed = True
            raise OSError("simulated disk error")
        return replace(source, destination)

    monkeypatch.setattr(audio_tempo.os, "replace", fault_once)
    with pytest.raises(OSError, match="simulated disk error"):
        audio_tempo.prepare_timeline(tmp_path)
    assert failed
    assert (tmp_path / "story.json").read_bytes() == original
    assert timing.read_bytes() == b'[{"approved":true}]'
    assert all(path.read_bytes() == data for path, data in old.items())
    assert not list(tmp_path.glob(".audio-stage-*"))


@pytest.mark.parametrize("rate", [8000, 16000, 24000, 44100, 48000])
def test_real_pitch_and_tempo_across_sample_rates(tmp_path, rate):
    source = make_wav(tmp_path / "source.wav", 1.8, rate)
    output = tmp_path / "slower.wav"
    info = audio_tempo.stretch_narration(source, output, digest(source))
    with wave.open(str(output), "rb") as stream:
        assert stream.getframerate() == rate
        values = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2")
    section = values[int(rate * 0.5) : int(rate * 1.0)].astype(float)
    bins = np.fft.rfftfreq(len(section), 1 / rate)
    pitch = bins[np.abs(np.fft.rfft(section * np.hanning(len(section)))).argmax()]
    assert 434 <= pitch <= 446
    assert info["sha256"] == digest(output)
    assert abs(info["duration"] - 1.8 / 0.92) < 0.025


def test_success_references_published_files_and_measured_frame_counts(tmp_path):
    make_project(tmp_path, (1.4, 1.6, 1.8))
    story = audio_tempo.prepare_timeline(tmp_path)
    report = json.loads((tmp_path / "audio-timing.json").read_text())
    assert len(report) == 3
    for scene, record in zip(story["scenes"], report, strict=True):
        slowed = tmp_path / record["file"]
        trimmed = tmp_path / record["trimmed_file"]
        assert slowed.is_file() and trimmed.is_file()
        assert digest(slowed) == record["sha256"]
        assert digest(trimmed) == record["trimmed_sha256"]
        assert round(scene["duration"] * 30) == record["scene_frames"]
        assert scene["duration"] - record["duration"] >= 0.09
    assert not list(tmp_path.glob(".audio-stage-*"))


def test_silent_wave_does_not_publish_a_timeline(tmp_path):
    original = make_project(tmp_path, (1.2,))
    source = tmp_path / "raw-0.wav"
    with wave.open(str(source), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(24000)
        output.writeframes(bytes(24000 * 2))
    records_path = tmp_path / "tts-provenance.json"
    records = json.loads(records_path.read_text())
    records["records"][0]["sha256"] = digest(source)
    records_path.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="no measurable speech"):
        audio_tempo.prepare_timeline(tmp_path)
    assert (tmp_path / "story.json").read_bytes() == original
    assert not (tmp_path / "audio-timing.json").exists()
    assert not list(tmp_path.glob(".audio-stage-*"))
