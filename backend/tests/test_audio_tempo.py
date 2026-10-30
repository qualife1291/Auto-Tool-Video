"""A04 uses actual FFmpeg/WAV IO, not mocked provider or fake speed metadata."""

import hashlib
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from audio_tempo import TEMPO, prepare_timeline, stretch_narration


def wav(path: Path, rate: int = 24000, seconds: float = 2.0, markers: bool = False) -> Path:
    t = np.arange(round(rate * seconds)) / rate
    tone = np.sin(t * 2 * np.pi * 440) * 0.35
    if markers:
        end = t >= seconds - 0.20
        tone[end] = 0.35 * np.sin(2 * np.pi * 880 * t[end])
    data = (tone * 32767).astype("<i2")
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(data.tobytes())
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def samples(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path), "rb") as stream:
        data = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2")
        return stream.getframerate(), data


def fundamental(segment: np.ndarray, rate: int) -> float:
    values = segment.astype(float)
    values -= values.mean()
    spectrum = abs(np.fft.rfft(values * np.hanning(len(values))))
    return float(np.fft.rfftfreq(len(values), 1 / rate)[int(spectrum.argmax())])


def test_real_ffmpeg_092_slows_without_lowering_pitch_or_cutting_tail(tmp_path):
    src = wav(tmp_path / "source.wav", seconds=2.1, markers=True)
    out = tmp_path / "result.wav"
    info = stretch_narration(src, out, digest(src))
    original_rate, original = samples(src)
    result_rate, transformed = samples(out)
    assert info["tempo"] == TEMPO == 0.92
    assert info["filter"] == "atempo=0.92"
    assert result_rate == original_rate == 24000
    assert out.is_file() and info["sha256"] == digest(out)
    assert info["source_sha256"] == digest(src)
    assert info["source_frames"] == len(original)
    assert info["output_frames"] == len(transformed)
    assert info["duration"] == pytest.approx(len(transformed) / result_rate)
    assert abs(info["duration"] - info["source_duration"] / 0.92) < 0.03
    start = int(0.4 * result_rate)
    middle = transformed[start : start + int(0.4 * result_rate)]
    assert 430 <= fundamental(middle, result_rate) <= 450
    # 880Hz marker must survive near the end, not be truncated to silence.
    tail = transformed[-int(0.12 * result_rate) :]
    assert np.sqrt(np.mean(tail.astype(float) ** 2)) > 1000
    assert 860 <= fundamental(tail, result_rate) <= 900
    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=codec_name,sample_rate,channels,duration",
                "-of",
                "json",
                str(out),
            ]
        )
    )
    assert probe["streams"][0]["codec_name"] == "pcm_s16le"
    assert probe["streams"][0]["channels"] == 1
    assert int(probe["streams"][0]["sample_rate"]) == 24000


@pytest.mark.parametrize("duration", [0.25, 0.5, 1.25, 3.5, 15.0])
def test_tempo_duration_is_measured_at_real_varied_lengths(tmp_path, duration):
    src = wav(tmp_path / "voice.wav", seconds=duration)
    result = stretch_narration(src, tmp_path / "slow.wav", digest(src))
    assert result["duration"] > duration
    tolerance = max(0.06, duration / TEMPO * 0.03)
    assert abs(result["duration"] - duration / TEMPO) < tolerance


def test_changed_source_hash_cannot_reuse_old_output(tmp_path):
    src = wav(tmp_path / "voice.wav")
    out = tmp_path / "slow.wav"
    out.write_bytes(b"keep previous approved audio")
    with pytest.raises(ValueError, match="SHA256"):
        stretch_narration(src, out, "0" * 64)
    assert out.read_bytes() == b"keep previous approved audio"
    with pytest.raises(ValueError, match="overwrite"):
        stretch_narration(src, src, digest(src))


def test_invalid_wave_rejected_without_calling_ffmpeg(tmp_path):
    src = tmp_path / "stereo.wav"
    with wave.open(str(src), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(24000)
        output.writeframes(b"\\0\\0\\0\\0" * 3000)
    with pytest.raises(ValueError, match="mono"):
        stretch_narration(src, tmp_path / "slow.wav", digest(src))
    assert not (tmp_path / "slow.wav").exists()


def test_failed_ffmpeg_never_replaces_approved_audio(tmp_path, monkeypatch):
    src = wav(tmp_path / "voice.wav")
    out = tmp_path / "slow.wav"
    out.write_bytes(b"previous approved")

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0], stderr=b"fixture ffmpeg error")

    monkeypatch.setattr("audio_tempo.subprocess.run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        stretch_narration(src, out, digest(src))
    assert out.read_bytes() == b"previous approved"
    assert not list(tmp_path.glob(".slow-*.wav"))


def test_timeline_from_measured_outputs_and_repeatable(tmp_path):
    stories = [
        {
            "title": "Cảnh 1",
            "narration": "Áo còn ướt.",
            "duration": 7,
            "second_by_second": [{"second": 0}],
            "beat_plan_status": "authored",
        },
        {"title": "Cảnh 2", "narration": "Nước bay hơi.", "duration": 8},
    ]
    original = {"title": "Mẫu", "scenes": stories}
    (tmp_path / "story.json").write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")
    records = []
    for n, scene in enumerate(stories, 1):
        source = wav(tmp_path / f"raw-{n}.wav", seconds=1.3 + n / 10)
        records.append(
            {"file": source.name, "sha256": digest(source), "narration": scene["narration"]}
        )
    (tmp_path / "tts-provenance.json").write_text(
        json.dumps({"records": records}), encoding="utf-8"
    )
    result = prepare_timeline(tmp_path)
    timing = json.loads((tmp_path / "audio-timing.json").read_text())
    assert len(timing) == 2
    for scene, voice in zip(result["scenes"], timing, strict=True):
        output = tmp_path / voice["file"]
        assert output.exists()
        assert digest(output) == voice["sha256"]
        rate, array = samples(output)
        assert voice["duration"] == pytest.approx(len(array) / rate)
        assert voice["tempo"] == 0.92
        assert scene["audio"] == voice["file"]
        assert scene["duration"] >= voice["duration"] + 0.09
        assert scene["duration"] - voice["duration"] <= 0.135
        assert voice["original_source_sha256"] == records[int(voice["file"][-6:-4]) - 1]["sha256"]
    assert result["scenes"][0]["beat_plan_status"] == "needs_review"
    assert result["scenes"][0]["second_by_second"] == [{"second": 0}]
    assert prepare_timeline(tmp_path) == result


def test_invalid_second_source_does_not_rewrite_story(tmp_path):
    scenes = [{"title": "A", "narration": "Đúng."}, {"title": "B", "narration": "Khác."}]
    data = json.dumps({"title": "Mẫu", "scenes": scenes}, ensure_ascii=False)
    (tmp_path / "story.json").write_text(data, encoding="utf-8")
    records = []
    for n, scene in enumerate(scenes):
        src = wav(tmp_path / f"{n}.wav")
        records.append({"file": src.name, "sha256": digest(src), "narration": scene["narration"]})
    records[-1]["sha256"] = "0" * 64
    (tmp_path / "tts-provenance.json").write_text(json.dumps({"records": records}))
    with pytest.raises(ValueError, match="SHA256"):
        prepare_timeline(tmp_path)
    assert (tmp_path / "story.json").read_text() == data
    assert not (tmp_path / "audio-timing.json").exists()


def test_long_audio_is_rejected_before_story_is_replaced(tmp_path):
    scene = {"title": "A", "narration": "Âm thanh dài.", "duration": 19}
    original = {"title": "Mẫu", "scenes": [scene]}
    text = json.dumps(original, ensure_ascii=False)
    (tmp_path / "story.json").write_text(text, encoding="utf-8")
    source = wav(tmp_path / "long.wav", seconds=19)
    (tmp_path / "tts-provenance.json").write_text(
        json.dumps(
            {
                "records": [
                    {"file": source.name, "sha256": digest(source), "narration": scene["narration"]}
                ]
            }
        )
    )
    with pytest.raises(ValueError, match="scene limit"):
        prepare_timeline(tmp_path)
    assert (tmp_path / "story.json").read_text() == text
    assert not (tmp_path / "audio-timing.json").exists()
