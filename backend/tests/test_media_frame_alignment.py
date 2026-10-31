"""P1-D: imported media scene clocks must agree with the 30 FPS renderer.

Synthetic PCM/MP3/MP4 fixtures exercise real API imports, database persistence,
and Fit Audio, not human-approved narration or visual quality.
First commit intentionally targets unpatched media.py to preserve behavioral RED.
"""

from __future__ import annotations

import io
import subprocess
import wave

import pytest
from conftest import attach, create_story, save

from auto_tool_video.timing import frames_for


def _wav(seconds: float) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(48000)
        output.writeframes(b"\x00\x00" * round(48000 * seconds))
    return buffer.getvalue()


def _mp3(tmp_path) -> bytes:
    path = tmp_path / "test.mp3"
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
            "anullsrc=r=48000:cl=mono",
            "-t",
            "2",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(path),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    return path.read_bytes()


def _mp4(tmp_path, seconds: float = 2.12) -> bytes:
    """25 FPS H.264: 53 frames / 25 = 2.12s, off the renderer's grid."""
    path = tmp_path / "test.mp4"
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
            f"color=c=black:s=64x64:r=25:d={seconds}",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    return path.read_bytes()


def _beats(count: int) -> list[dict]:
    return [
        {
            "second": index,
            "visual_state": f"Áo ướt ở giây {index}",
            "action": f"Áo đang khô ở giây {index}",
            "camera": "Khung cố định",
            "on_screen_text": "",
            "narration_cue": "Giữ lời tiếng Việt",
            "continuity": "Một chiếc áo",
        }
        for index in range(count)
    ]


def _scene(project: dict) -> dict:
    return project["scenes"][0]


def _asset(client, project: dict, content: bytes, name: str) -> dict:
    return attach(client, project, _scene(project), content, name)


@pytest.mark.parametrize("seconds", [1.0, 2.0, 19.65])
def test_imported_wav_scene_uses_renderer_frame_grid(client, seconds):
    project = create_story(client)
    updated = _asset(client, project, _wav(seconds), "test.wav")
    scene = _scene(updated)
    asset = client.app.state.store.get("assets", scene["audio_id"])
    expected = max(1, frames_for(asset["duration"] + 0.12) / 30)

    assert asset["duration"] == pytest.approx(seconds)
    assert scene["duration"] == expected
    assert frames_for(scene["duration"]) / 30 == scene["duration"]
    assert 1 <= scene["duration"] <= 20
    assert updated["revision"] == project["revision"] + 1
    assert client.get(f"/api/projects/{project['id']}").json() == updated


def test_import_mp3_keeps_measured_asset_duration_and_aligns_scene(client, tmp_path):
    project = create_story(client)
    updated = _asset(client, project, _mp3(tmp_path), "test.mp3")
    scene = _scene(updated)
    asset = client.app.state.store.get("assets", scene["audio_id"])

    assert asset["kind"] == "audio"
    assert asset["mime"] == "audio/mpeg"
    assert asset["duration"] > 0
    assert scene["duration"] == max(1, frames_for(asset["duration"] + 0.12) / 30)
    assert frames_for(scene["duration"]) / 30 == scene["duration"]


def test_import_non_30fps_mp4_uses_renderer_grid_without_mutating_source(client, tmp_path):
    project = create_story(client)
    updated = _asset(client, project, _mp4(tmp_path), "test.mp4")
    scene = _scene(updated)
    asset = client.app.state.store.get("assets", scene["image_id"])

    assert asset["kind"] == "clip"
    assert asset["duration"] == pytest.approx(2.12)
    assert scene["style"] == "motion"
    assert scene["duration"] == frames_for(asset["duration"]) / 30
    assert frames_for(scene["duration"]) / 30 == scene["duration"]


def test_import_mp4_with_attached_audio_compares_on_same_grid(client, tmp_path):
    project = create_story(client)
    project = _asset(client, project, _wav(2.0), "narration.wav")
    audio = client.app.state.store.get("assets", _scene(project)["audio_id"])
    updated = _asset(client, project, _mp4(tmp_path, 1.4), "short.mp4")

    expected = max(
        1,
        frames_for(1.4) / 30,
        frames_for(audio["duration"] + 0.12) / 30,
    )
    assert _scene(updated)["duration"] == expected
    assert _scene(updated)["audio_id"] == _scene(project)["audio_id"]
    assert _scene(updated)["style"] == "motion"


def test_import_author_beat_then_fit_default_pause_keeps_authored(client):
    """True user-visible RED: equal intended rendered duration must not stale beats."""
    project = create_story(client, "Áo ướt đang khô.")
    project = _asset(client, project, _wav(2.0), "narration.wav")
    import_duration = _scene(project)["duration"]

    _scene(project).update(
        second_by_second=_beats(3),
        beat_plan_status="authored",
    )
    saved = save(client, project)
    assert saved.status_code == 200, saved.text
    project = saved.json()
    assert _scene(project)["beat_plan_status"] == "authored"

    response = client.post(
        f"/api/projects/{project['id']}/fit-audio",
        json={"revision": project["revision"], "pause_after": 0.12},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert _scene(result)["duration"] == import_duration
    assert _scene(result)["beat_plan_status"] == "authored"
    assert _scene(result)["second_by_second"] == _beats(3)
    assert result["revision"] == project["revision"] + 1
    assert client.get(f"/api/projects/{project['id']}").json() == result


def test_genuine_frame_change_still_invalidates_authored_beat(client):
    project = create_story(client, "Áo ướt đang khô.")
    project = _asset(client, project, _wav(2.0), "narration.wav")
    _scene(project).update(second_by_second=_beats(3), beat_plan_status="authored")
    response = save(client, project)
    assert response.status_code == 200, response.text
    project = response.json()

    fit = client.post(
        f"/api/projects/{project['id']}/fit-audio",
        json={"revision": project["revision"], "pause_after": 0.35},
    )
    assert fit.status_code == 200, fit.text
    result = fit.json()
    assert _scene(result)["duration"] == frames_for(2.0 + 0.35) / 30
    assert _scene(result)["beat_plan_status"] == "needs_review"
    assert _scene(result)["second_by_second"] == _beats(3)


def test_stale_revision_import_does_not_write_asset_or_retime(client):
    project = create_story(client)
    before = client.get(f"/api/projects/{project['id']}").json()
    asset_count = len(list((client.app.state.store.root / "assets").iterdir()))
    response = client.post(
        f"/api/projects/{project['id']}/scenes/{_scene(project)['id']}/assets",
        data={"revision": project["revision"] - 1},
        files={"file": ("test.wav", _wav(2.0))},
    )
    assert response.status_code == 422 or response.status_code == 409
    assert client.get(f"/api/projects/{project['id']}").json() == before
    assert len(list((client.app.state.store.root / "assets").iterdir())) == asset_count


def test_image_import_does_not_change_scene_duration(client, image_bytes):
    project = create_story(client)
    before = _scene(project)["duration"]
    updated = _asset(client, project, image_bytes, "test.png")
    assert _scene(updated)["duration"] == before
