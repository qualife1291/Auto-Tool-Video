"""P1-A regression: importing assets must not silently approve a retimed beat plan.

Synthetic WAV/MP4 fixtures only; this does not validate a human narrator or video content.
"""

from __future__ import annotations

import io
import math
import subprocess
import wave

import pytest

from conftest import create_story, save


def _beats(count: int) -> list[dict]:
    return [
        {
            "second": second,
            "visual_state": f"Áo ướt ở giây {second}",
            "action": f"Áo khô dần ở giây {second}",
            "camera": "Giữ khung hình ổn định",
            "on_screen_text": "",
            "narration_cue": f"Đọc ở giây {second}",
            "continuity": "Giữ nguyên chiếc áo",
        }
        for second in range(count)
    ]


def _pcm_wav(seconds: float) -> bytes:
    """Deterministic valid mono 48 kHz PCM16 fixture; no original voice data."""
    stream = io.BytesIO()
    with wave.open(stream, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(48000)
        output.writeframes(b"\x00\x00" * round(48000 * seconds))
    return stream.getvalue()


def _approved_project(client, duration: float = 3.0):
    project = create_story(client)
    project["scenes"][0]["duration"] = duration
    stored = save(client, project)
    assert stored.status_code == 200, stored.text
    project = stored.json()
    beat_set = _beats(math.ceil(duration))
    project["scenes"][0].update(second_by_second=beat_set, beat_plan_status="authored")
    authored = save(client, project)
    assert authored.status_code == 200, authored.text
    project = authored.json()
    assert project["scenes"][0]["beat_plan_status"] == "authored"
    return project, beat_set


def _import(client, project: dict, content: bytes, filename: str):
    return client.post(
        f"/api/projects/{project['id']}/scenes/{project['scenes'][0]['id']}/assets",
        data={"revision": project["revision"]},
        files={"file": (filename, content)},
    )


@pytest.mark.parametrize("audio_seconds", [2.0, 1.0])
def test_audio_import_retime_invalidates_authored_beats_without_discarding_text(
    client, audio_seconds
):
    """Same ceil bucket (3 -> 2.12) is the critical path missed by model validation."""
    project, beat_set = _approved_project(client)
    unchanged_scenes = project["scenes"][1:]
    imported = _import(client, project, _pcm_wav(audio_seconds), "voice.wav")
    assert imported.status_code == 200, imported.text

    result = imported.json()
    scene = result["scenes"][0]
    assert result["revision"] == project["revision"] + 1
    assert scene["duration"] == pytest.approx(audio_seconds + 0.12)
    assert scene["beat_plan_status"] == "needs_review"
    assert scene["second_by_second"] == beat_set
    assert result["scenes"][1:] == unchanged_scenes

    reloaded = client.get(f"/api/projects/{project['id']}")
    assert reloaded.status_code == 200
    assert reloaded.json()["scenes"] == result["scenes"]


def test_import_does_not_invalidate_when_duration_is_unchanged(client):
    project, beat_set = _approved_project(client, duration=2.12)
    imported = _import(client, project, _pcm_wav(2.0), "unchanged.wav")
    assert imported.status_code == 200, imported.text
    scene = imported.json()["scenes"][0]
    assert scene["duration"] == pytest.approx(2.12)
    assert scene["beat_plan_status"] == "authored"
    assert scene["second_by_second"] == beat_set


def test_image_import_keeps_authored_beat_timing(client, image_bytes):
    project, beat_set = _approved_project(client)
    result = _import(client, project, image_bytes, "shirt.png")
    assert result.status_code == 200, result.text
    scene = result.json()["scenes"][0]
    assert scene["duration"] == 3.0
    assert scene["beat_plan_status"] == "authored"
    assert scene["second_by_second"] == beat_set


def test_mp4_import_retime_invalidates_authored_beats(client, tmp_path):
    """Both audio and visual asset duration mutations have the same invariant."""
    video = tmp_path / "clip.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=64x64:r=30:d=2.2",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(video),
        ],
        check=True,
        timeout=30,
        capture_output=True,
    )
    project, beat_set = _approved_project(client)
    response = _import(client, project, video.read_bytes(), video.name)
    assert response.status_code == 200, response.text
    scene = response.json()["scenes"][0]
    assert scene["duration"] == pytest.approx(2.2)
    assert scene["style"] == "motion"
    assert scene["beat_plan_status"] == "needs_review"
    assert scene["second_by_second"] == beat_set


def test_stale_revision_rejects_upload_without_mutating_authored_beats(client):
    project, beat_set = _approved_project(client)
    stale = dict(project)
    stale["revision"] -= 1
    rejected = _import(client, stale, _pcm_wav(2.0), "old.wav")
    assert rejected.status_code == 409
    assert rejected.json()["code"] == "REVISION_CONFLICT"
    reloaded = client.get(f"/api/projects/{project['id']}").json()
    assert reloaded["revision"] == project["revision"]
    assert reloaded["scenes"][0]["duration"] == 3.0
    assert reloaded["scenes"][0]["beat_plan_status"] == "authored"
    assert reloaded["scenes"][0]["second_by_second"] == beat_set
