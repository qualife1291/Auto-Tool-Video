"""C04 #89 RED -> BA-approved #94 GREEN: keep motion source frames.

Synthetic WAV/MP4 tests preserve immutable original RED in GitHub Actions
#41173149131 and exercise the new source change without real creator data.
No renderer, Store, timing, workflow or QA thresholds are modified.
"""

from __future__ import annotations

import copy
import io
import math
import subprocess
import wave

import pytest
from conftest import attach, create_story, save

from auto_tool_video.timing import frames_for


def _wav(seconds: float) -> bytes:
    """Inert mono 48 kHz WAV; no recorded voice or private data."""
    output = io.BytesIO()
    with wave.open(output, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(48000)
        stream.writeframes(b"\x00\x00" * round(48000 * seconds))
    return output.getvalue()


@pytest.fixture(scope="module")
def long_clip(tmp_path_factory) -> bytes:
    """53 frames at 25 FPS = 2.12s, off the 30 FPS renderer frame grid."""
    path = tmp_path_factory.mktemp("c04-grid-parity") / "clip.mp4"
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
            "color=c=black:s=64x64:r=25:d=2.12",
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


def _scene(project: dict) -> dict:
    return project["scenes"][0]


def _import(client, project: dict, content: bytes, name: str) -> dict:
    return attach(client, project, _scene(project), content, name)


def _fit(client, project: dict, pause_after: float = 0.12):
    return client.post(
        f"/api/projects/{project['id']}/fit-audio",
        json={"revision": project["revision"], "pause_after": pause_after},
    )


def _beats(count: int) -> list[dict]:
    return [
        {
            "second": second,
            "visual_state": f"Áo ướt ở giây {second}",
            "action": f"Áo khô dần ở giây {second}",
            "camera": "Góc cố định",
            "on_screen_text": "",
            "narration_cue": "Giữ lời tiếng Việt",
            "continuity": "Cùng một áo",
        }
        for second in range(count)
    ]


@pytest.mark.parametrize("aspect", ["portrait", "landscape"])
@pytest.mark.parametrize("seconds", [1.0, 2.0, 19.65])
def test_import_and_fit_same_wav_pause_have_identical_30fps_grid(
    client, aspect: str, seconds: float
):
    project = create_story(client, "Một chiếc áo ướt.")
    project["aspect"] = aspect
    saved = save(client, project)
    assert saved.status_code == 200, saved.text
    project = saved.json()

    project = _import(client, project, _wav(seconds), "voice.wav")
    audio_id = _scene(project)["audio_id"]
    asset = client.app.state.store.get("assets", audio_id)
    imported_duration = _scene(project)["duration"]
    expected = max(1, frames_for(asset["duration"] + 0.12) / 30)

    assert asset["duration"] == pytest.approx(seconds)
    assert imported_duration == expected
    assert frames_for(imported_duration) / 30 == imported_duration
    assert 1 <= imported_duration <= 20

    response = _fit(client, project, 0.12)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["aspect"] == aspect
    assert _scene(result)["duration"] == imported_duration
    assert _scene(result)["audio_id"] == audio_id
    assert result["revision"] == project["revision"] + 1
    assert client.get(f"/api/projects/{project['id']}").json() == result


def test_real_pause_change_invalidates_authored_beats_but_preserves_text(client):
    project = create_story(client, "Một chiếc áo đang khô.")
    project = _import(client, project, _wav(2.0), "voice.wav")
    original_duration = _scene(project)["duration"]
    beats = _beats(math.ceil(original_duration))
    _scene(project).update(second_by_second=beats, beat_plan_status="authored")

    saved = save(client, project)
    assert saved.status_code == 200, saved.text
    project = saved.json()
    assert _scene(project)["beat_plan_status"] == "authored"

    unchanged = _fit(client, project, 0.12)
    assert unchanged.status_code == 200, unchanged.text
    result = unchanged.json()
    assert _scene(result)["duration"] == original_duration
    assert _scene(result)["beat_plan_status"] == "authored"

    changed = _fit(client, result, 0.35)
    assert changed.status_code == 200, changed.text
    updated = changed.json()
    assert _scene(updated)["duration"] == frames_for(2.0 + 0.35) / 30
    assert _scene(updated)["beat_plan_status"] == "needs_review"
    assert _scene(updated)["second_by_second"] == beats
    assert client.get(f"/api/projects/{project['id']}").json() == updated


@pytest.mark.parametrize("clip_first", [True, False])
def test_short_clip_with_long_wav_is_order_independent(client, long_clip: bytes, clip_first: bool):
    project = create_story(client, "Đổi cảnh không cắt lời.")
    if clip_first:
        project = _import(client, project, long_clip, "short.mp4")
        project = _import(client, project, _wav(2.0), "long.wav")
    else:
        project = _import(client, project, _wav(2.0), "long.wav")
        project = _import(client, project, long_clip, "short.mp4")

    audio = client.app.state.store.get("assets", _scene(project)["audio_id"])
    clip = client.app.state.store.get("assets", _scene(project)["image_id"])
    expected = max(
        1,
        frames_for(clip["duration"]) / 30,
        frames_for(audio["duration"] + 0.12) / 30,
    )
    assert _scene(project)["duration"] == expected
    assert _scene(project)["style"] == "motion"
    fitted = _fit(client, project, 0.12)
    assert fitted.status_code == 200, fitted.text
    assert _scene(fitted.json())["duration"] == expected


def test_long_clip_plus_short_wav_import_order_preserves_visual_frame_floor(
    client, long_clip: bytes
):
    """Potential source RED: imported audio must not truncate a longer visual clip."""
    project = create_story(client, "Khung quay dài hơn lời.")
    project = _import(client, project, long_clip, "long.mp4")
    clip_id = _scene(project)["image_id"]
    clip = client.app.state.store.get("assets", clip_id)
    clip_floor = frames_for(clip["duration"]) / 30
    assert clip_floor > frames_for(1.0 + 0.12) / 30

    original_beats = _beats(math.ceil(_scene(project)["duration"]))
    _scene(project).update(second_by_second=original_beats, beat_plan_status="authored")
    saved = save(client, project)
    assert saved.status_code == 200, saved.text
    project = saved.json()
    assert _scene(project)["beat_plan_status"] == "authored"

    result = _import(client, project, _wav(1.0), "short.wav")
    assert result["revision"] == project["revision"] + 1
    assert _scene(result)["image_id"] == clip_id
    assert _scene(result)["second_by_second"] == original_beats
    # With the full clip unchanged, creator-authored timing remains valid.
    assert _scene(result)["beat_plan_status"] == "authored"

    # The visual clip must remain playable in full, irrespective of the shorter audio.
    assert _scene(result)["duration"] >= clip_floor, (
        f"imported audio shortened a {clip_floor:.6f}s clip to {_scene(result)['duration']:.6f}s"
    )


def test_long_clip_short_wav_fit_does_not_drop_clip_frames(client, long_clip: bytes):
    """Potential source RED: Fit Audio should preserve an existing longer clip."""
    project = create_story(client, "Clip vẫn đủ khung hình.")
    project = _import(client, project, _wav(1.0), "short.wav")
    project = _import(client, project, long_clip, "long.mp4")
    clip_id = _scene(project)["image_id"]
    clip = client.app.state.store.get("assets", clip_id)
    clip_floor = frames_for(clip["duration"]) / 30
    assert _scene(project)["duration"] >= clip_floor

    response = _fit(client, project, 0.12)
    assert response.status_code == 200, response.text
    result = response.json()
    assert _scene(result)["image_id"] == clip_id
    assert result["revision"] == project["revision"] + 1

    # The same pause and media must not make the clip shorter after Fit Audio.
    assert _scene(result)["duration"] >= clip_floor, (
        f"fit-audio reduced clip from {clip_floor:.6f}s to {_scene(result)['duration']:.6f}s"
    )


def test_stale_revision_and_missing_audio_never_change_persisted_project(client):
    project = create_story(client, "Không ghi đè dữ liệu.")
    project = _import(client, project, _wav(2.0), "voice.wav")
    before = copy.deepcopy(project)
    wrong_revision = client.post(
        f"/api/projects/{project['id']}/fit-audio",
        json={"revision": project["revision"] - 1, "pause_after": 0.12},
    )
    assert wrong_revision.status_code == 409, wrong_revision.text
    assert wrong_revision.json()["code"] == "REVISION_CONFLICT"
    assert client.get(f"/api/projects/{project['id']}").json() == before

    missing = create_story(client, "Chưa có giọng.")
    response = _fit(client, missing, 0.12)
    assert response.status_code == 400, response.text
    assert response.json()["code"] == "MISSING_AUDIO"
    assert client.get(f"/api/projects/{missing['id']}").json() == missing


def test_three_scenes_exact_60s_respect_fit_boundaries(client):
    project = create_story(client, "Cảnh một.\nCảnh hai.\nCảnh ba.")
    for index in range(3):
        project = attach(client, project, project["scenes"][index], _wav(19.65), f"{index}.wav")

    before = copy.deepcopy(project)
    fit = _fit(client, project, 0.35)
    assert fit.status_code == 200, fit.text
    result = fit.json()
    assert [scene["duration"] for scene in result["scenes"]] == [20.0] * 3
    assert result["revision"] == before["revision"] + 1

    rejected = _fit(client, result, 0.36)
    assert rejected.status_code == 400, rejected.text
    assert rejected.json()["code"] == "DURATION_LIMIT"
    assert client.get(f"/api/projects/{result['id']}").json() == result


@pytest.mark.parametrize("clip_first", [True, False])
@pytest.mark.parametrize("audio_seconds", [1.0, 3.0])
@pytest.mark.parametrize("pause_after", [0.0, 0.35])
def test_motion_clip_audio_order_and_pause_use_measured_frame_maximum(
    client, long_clip: bytes, clip_first: bool, audio_seconds: float, pause_after: float
):
    """Neither upload order nor Fit Audio may implicitly clip off video frames."""
    project = create_story(client, "Không cắt đuôi clip chuyển động.")
    if clip_first:
        project = _import(client, project, long_clip, "source.mp4")
        project = _import(client, project, _wav(audio_seconds), "narration.wav")
    else:
        project = _import(client, project, _wav(audio_seconds), "narration.wav")
        project = _import(client, project, long_clip, "source.mp4")
    store = client.app.state.store
    scene = _scene(project)
    audio = store.get("assets", scene["audio_id"])
    clip = store.get("assets", scene["image_id"])
    imported_expected = max(
        30, frames_for(clip["duration"]), frames_for(audio["duration"] + 0.12)
    )
    assert frames_for(scene["duration"]) == imported_expected

    response = _fit(client, project, pause_after)
    assert response.status_code == 200, response.text
    result = response.json()
    expected = max(
        30, frames_for(clip["duration"]), frames_for(audio["duration"] + pause_after)
    )
    assert frames_for(_scene(result)["duration"]) == expected
    assert _scene(result)["image_id"] == scene["image_id"]
    assert _scene(result)["audio_id"] == scene["audio_id"]
    assert _scene(result)["style"] == "motion"
    assert result["revision"] == project["revision"] + 1
    assert client.get(f"/api/projects/{project['id']}").json() == result


def test_audio_only_fit_shrinks_after_smaller_pause_without_stale_duration_floor(client):
    """No prior scene length may become a permanent minimum in whiteboard mode."""
    project = create_story(client, "Chỉ có giọng đọc.")
    project = _import(client, project, _wav(2.0), "voice.wav")
    enlarged = _fit(client, project, 0.35)
    assert enlarged.status_code == 200, enlarged.text
    expanded = enlarged.json()
    assert frames_for(_scene(expanded)["duration"]) == frames_for(2.35)

    reduced = _fit(client, expanded, 0.0)
    assert reduced.status_code == 200, reduced.text
    assert _scene(reduced.json())["duration"] == 2.0


def test_audio_import_exceeding_1800_frames_leaves_no_orphan_asset(client):
    """The fourth imported WAV must fail atomically, including staged file cleanup."""
    project = create_story(client, "Một.\nHai.\nBa.\nBốn.")
    for index in range(3):
        project = attach(
            client, project, project["scenes"][index], _wav(15.0), f"voice{index}.wav"
        )
    before = copy.deepcopy(project)
    store = client.app.state.store
    asset_files_before = {p.name for p in (store.root / "assets").iterdir()}

    response = client.post(
        f"/api/projects/{project['id']}/scenes/{project['scenes'][3]['id']}/assets",
        data={"revision": project["revision"]},
        files={"file": ("voice-last.wav", _wav(15.0))},
    )
    assert response.status_code == 400, response.text
    assert response.json()["code"] == "DURATION_LIMIT"
    assert client.get(f"/api/projects/{project['id']}").json() == before
    assert {p.name for p in (store.root / "assets").iterdir()} == asset_files_before


def test_scene_limit_fails_closed_on_motion_plus_oversized_pause(client, long_clip: bytes):
    """A valid clip floor must not override per-scene 600-frame narration cap."""
    project = create_story(client, "Clip cần giọng ngắn hơn 20 giây.")
    project = _import(client, project, long_clip, "source.mp4")
    project = _import(client, project, _wav(19.65), "voice.wav")
    before = copy.deepcopy(project)

    response = _fit(client, project, 0.36)
    assert response.status_code == 400, response.text
    assert response.json()["code"] == "DURATION_LIMIT"
    assert client.get(f"/api/projects/{project['id']}").json() == before
