"""C04 P1-B: Fit Audio cannot persist a frame-aligned scene >20 seconds.

The first test was an actual RED on unpatched production code at SHA
788078490f9443ac1829bcecd1787ec989825c09 (main CI 41110342760).
WAVs below are synthetic silence, not human-approved narration.
"""

from __future__ import annotations

import copy
import io
import wave

import pytest
from conftest import attach, create_story, save


def _wav(seconds: float) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(48000)
        output.writeframes(b"\x00\x00" * round(48000 * seconds))
    return buffer.getvalue()


def _import_audio(client, project: dict, index: int, seconds: float) -> dict:
    return attach(client, project, project["scenes"][index], _wav(seconds), "voice.wav")


def _fit(client, project: dict, pause_after: float, revision: int | None = None):
    return client.post(
        f"/api/projects/{project['id']}/fit-audio",
        json={
            "revision": project["revision"] if revision is None else revision,
            "pause_after": pause_after,
        },
    )


def _beats(count: int) -> list[dict]:
    return [
        {
            "second": index,
            "visual_state": f"Áo ướt tại giây {index}",
            "action": f"Khô dần tại giây {index}",
            "camera": "Giữ khung",
            "on_screen_text": "Nước bay hơi",
            "narration_cue": "Giữ nguyên lời tiếng Việt",
            "continuity": "Một chiếc áo duy nhất",
        }
        for index in range(count)
    ]


@pytest.mark.parametrize("pause_after", [0.36, 1.0])
def test_fit_audio_never_persists_scene_over_20_seconds(client, pause_after):
    """Old-code RED: valid 19.65s WAV plus pause crosses the 600-frame cap."""
    project = create_story(client, "Áo ướt khô nhờ nước bay hơi.")
    project = _import_audio(client, project, 0, 19.65)
    audio_id = project["scenes"][0]["audio_id"]
    store = client.app.state.store
    asset_before = copy.deepcopy(store.get("assets", audio_id))
    original_bytes = store.asset_path(asset_before).read_bytes()
    before = copy.deepcopy(project)

    response = _fit(client, project, pause_after)

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "DURATION_LIMIT"
    assert client.get(f"/api/projects/{project['id']}").json() == before
    assert store.get("assets", audio_id) == asset_before
    assert store.asset_path(asset_before).read_bytes() == original_bytes


def test_fit_audio_exact_20_seconds_accepted_with_review_invalidation(client):
    """19.65s WAV + 0.35s pause => exactly 600 frames, not 601."""
    project = create_story(client, "Nước bay hơi.")
    project = _import_audio(client, project, 0, 19.65)
    beats = _beats(20)
    project["scenes"][0].update(second_by_second=beats, beat_plan_status="authored")
    saved = save(client, project)
    assert saved.status_code == 200, saved.text
    project = saved.json()
    assert project["scenes"][0]["beat_plan_status"] == "authored"

    response = _fit(client, project, 0.35)

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["revision"] == project["revision"] + 1
    assert result["scenes"][0]["duration"] == 20.0
    assert result["scenes"][0]["audio_id"] == project["scenes"][0]["audio_id"]
    assert result["scenes"][0]["second_by_second"] == beats
    assert result["scenes"][0]["beat_plan_status"] == "needs_review"
    assert client.get(f"/api/projects/{project['id']}").json() == result


def test_fit_audio_one_second_minimum_remains_supported(client):
    project = create_story(client, "Giọng ngắn.")
    project = _import_audio(client, project, 0, 0.5)
    response = _fit(client, project, 0.0)
    assert response.status_code == 200, response.text
    assert response.json()["scenes"][0]["duration"] == 1.0


def test_fit_audio_overlong_later_scene_is_atomic_and_preserves_authored_beats(client):
    project = create_story(client, "Cảnh một.\nCảnh hai.")
    project = _import_audio(client, project, 0, 1.0)
    project = _import_audio(client, project, 1, 19.65)
    beats = _beats(20)
    project["scenes"][1].update(second_by_second=beats, beat_plan_status="authored")
    saved = save(client, project)
    assert saved.status_code == 200, saved.text
    project = saved.json()
    assert project["scenes"][1]["beat_plan_status"] == "authored"
    before = copy.deepcopy(project)

    response = _fit(client, project, 1.0)

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "DURATION_LIMIT"
    assert client.get(f"/api/projects/{project['id']}").json() == before
    assert before["scenes"][1]["second_by_second"] == beats


def test_fit_audio_total_duration_over_60_still_rejected(client):
    project = create_story(client, "Cảnh một.\nCảnh hai.\nCảnh ba.\nCảnh bốn.")
    for index in range(4):
        project = _import_audio(client, project, index, 15.0)
    before = copy.deepcopy(project)

    response = _fit(client, project, 0.5)

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "DURATION_LIMIT"
    assert client.get(f"/api/projects/{project['id']}").json() == before


def test_fit_audio_three_scenes_at_60_seconds_is_valid(client):
    project = create_story(client, "Cảnh một.\nCảnh hai.\nCảnh ba.")
    for index in range(3):
        project = _import_audio(client, project, index, 19.65)

    response = _fit(client, project, 0.35)

    assert response.status_code == 200, response.text
    result = response.json()
    assert [scene["duration"] for scene in result["scenes"]] == [20.0] * 3
    assert result["revision"] == project["revision"] + 1


def test_fit_audio_missing_audio_keeps_original_project(client):
    project = create_story(client, "Thiếu giọng.")
    response = _fit(client, project, 0.12)
    assert response.status_code == 400
    assert response.json()["code"] == "MISSING_AUDIO"
    assert client.get(f"/api/projects/{project['id']}").json() == project


def test_fit_audio_stale_audio_preserves_project(client):
    project = create_story(client, "Giọng hiện tại.")
    project = _import_audio(client, project, 0, 2.0)
    project["scenes"][0]["narration"] = "Giọng khác, cần nhập lại."
    saved = save(client, project)
    assert saved.status_code == 200, saved.text
    project = saved.json()
    assert project["scenes"][0]["audio_stale"] is True

    response = _fit(client, project, 0.12)

    assert response.status_code == 400
    assert response.json()["code"] == "MISSING_AUDIO"
    assert client.get(f"/api/projects/{project['id']}").json() == project


def test_fit_audio_stale_revision_precedes_duration_limit(client):
    project = create_story(client, "Không ghi đè phiên bản mới.")
    project = _import_audio(client, project, 0, 19.65)

    response = _fit(client, project, 1.0, revision=project["revision"] - 1)

    assert response.status_code == 409
    assert response.json()["code"] == "REVISION_CONFLICT"
    assert client.get(f"/api/projects/{project['id']}").json() == project


def test_fit_audio_missing_audio_takes_priority_over_other_scene_duration(client):
    project = create_story(client, "Có giọng.\nThiếu giọng.")
    project = _import_audio(client, project, 0, 19.65)

    response = _fit(client, project, 1.0)

    assert response.status_code == 400
    assert response.json()["code"] == "MISSING_AUDIO"
    assert client.get(f"/api/projects/{project['id']}").json() == project


def test_fit_audio_rejects_invalid_pause_without_persistence(client):
    project = create_story(client, "Nhịp đọc.")
    project = _import_audio(client, project, 0, 1.0)
    response = _fit(client, project, 1.01)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert client.get(f"/api/projects/{project['id']}").json() == project
