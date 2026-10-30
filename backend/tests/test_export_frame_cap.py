"""P1-C regression: export duration must match the renderer's 30 FPS clock.

Every project is created through the real API and populated with valid PNG assets.
No FFmpeg encode is needed to prove the enqueue-side safety contract.
"""

from __future__ import annotations

import copy
from uuid import uuid4

import pytest
from conftest import attach, create_story, save

from auto_tool_video.timing import frames_for


@pytest.fixture
def prepared_project(client, image_bytes):
    """Twelve independent scenes with valid asset ownership and files."""
    script = "\n".join(f"Cảnh giáo dục tiếng Việt số {index}." for index in range(12))
    project = create_story(client, script)
    for index in range(12):
        project = attach(client, project, project["scenes"][index], image_bytes)
    assert len(project["scenes"]) == 12
    return project


def timed_project(client, project, durations):
    assert len(durations) == len(project["scenes"])
    for scene, duration in zip(project["scenes"], durations, strict=True):
        scene["duration"] = duration
    response = save(client, project)
    assert response.status_code == 200, response.text
    return response.json()


def export_request(project, *, aspect="portrait", silent=True, key=None, revision=None):
    return {
        "revision": project["revision"] if revision is None else revision,
        "silent": silent,
        "aspect": aspect,
        "idempotency_key": key or str(uuid4()),
    }


def job_count(client):
    with client.app.state.store.connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]


@pytest.mark.parametrize("aspect", ["portrait", "landscape"])
@pytest.mark.parametrize("silent", [True, False])
def test_raw_under_60_but_1806_rendered_frames_is_rejected(
    client, prepared_project, aspect, silent
):
    """RED on old jobs.enqueue: 59.94 raw seconds render as 60.2 seconds."""
    project = timed_project(client, prepared_project, [4.95] * 6 + [5.04] * 6)
    assert sum(s["duration"] for s in project["scenes"]) == pytest.approx(59.94)
    assert sum(frames_for(s["duration"]) for s in project["scenes"]) == 1806
    before = copy.deepcopy(project)
    response = client.post(
        f"/api/projects/{project['id']}/exports",
        json=export_request(project, aspect=aspect, silent=silent),
    )
    assert response.status_code == 400, response.text
    assert response.json()["code"] == "DURATION_LIMIT"
    assert job_count(client) == 0
    assert client.get(f"/api/projects/{project['id']}").json() == before
    for scene in project["scenes"]:
        asset = client.app.state.store.get("assets", scene["image_id"])
        assert client.app.state.store.asset_path(asset).is_file()


@pytest.mark.parametrize("aspect", ["portrait", "landscape"])
def test_exact_1800_frame_boundary_accepts_valid_silent_export(client, prepared_project, aspect):
    project = timed_project(client, prepared_project, [5.0] * 12)
    assert sum(frames_for(s["duration"]) for s in project["scenes"]) == 1800
    request = export_request(project, aspect=aspect)
    response = client.post(f"/api/projects/{project['id']}/exports", json=request)
    assert response.status_code == 202, response.text
    job = response.json()
    assert job["state"] == "queued"
    assert job["revision"] == project["revision"]
    assert job_count(client) == 1
    assert client.app.state.store.get("jobs", job["id"])["snapshot"] == project


@pytest.mark.parametrize(
    "durations,expected_frames",
    [
        ([5.01] * 12, 1812),  # Raw > 60s has always been rejected.
        ([4.99999, 5.00001] * 6, 1806),  # Raw 60.0, per-scene frame rounding.
    ],
)
def test_rejects_overrun_at_raw_and_fractional_frame_boundaries(
    client, prepared_project, durations, expected_frames
):
    project = timed_project(client, prepared_project, durations)
    assert sum(frames_for(s["duration"]) for s in project["scenes"]) == expected_frames
    response = client.post(f"/api/projects/{project['id']}/exports", json=export_request(project))
    assert response.status_code == 400
    assert response.json()["code"] == "DURATION_LIMIT"
    assert job_count(client) == 0


def test_existing_idempotent_snapshot_survives_later_overlong_revision(client, prepared_project):
    project = timed_project(client, prepared_project, [5.0] * 12)
    key = "stable-retry-key-0001"
    original = export_request(project, key=key)
    url = f"/api/projects/{project['id']}/exports"
    first = client.post(url, json=original)
    assert first.status_code == 202, first.text
    old_job = first.json()
    project = timed_project(client, project, [4.95] * 6 + [5.04] * 6)
    assert client.post(url, json=original).json()["id"] == old_job["id"]
    assert client.post(url, json={**original, "aspect": "landscape"}).status_code == 409
    overlong = client.post(url, json=export_request(project))
    assert overlong.status_code == 400
    assert overlong.json()["code"] == "DURATION_LIMIT"
    assert job_count(client) == 1
    assert (
        client.app.state.store.get("jobs", old_job["id"])["snapshot"]["revision"]
        == (original["revision"])
    )


def test_rejected_request_key_can_be_reused_after_valid_revision(client, prepared_project):
    project = timed_project(client, prepared_project, [4.95] * 6 + [5.04] * 6)
    key = "rejected-then-valid-key"
    url = f"/api/projects/{project['id']}/exports"
    assert client.post(url, json=export_request(project, key=key)).json()["code"] == (
        "DURATION_LIMIT"
    )
    assert job_count(client) == 0
    project = timed_project(client, project, [5.0] * 12)
    accepted = client.post(url, json=export_request(project, key=key))
    assert accepted.status_code == 202, accepted.text
    assert job_count(client) == 1


def test_stale_revision_precedes_duration_validation(client, prepared_project):
    project = timed_project(client, prepared_project, [4.95] * 6 + [5.04] * 6)
    response = client.post(
        f"/api/projects/{project['id']}/exports",
        json=export_request(project, revision=project["revision"] - 1),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "REVISION_CONFLICT"
    assert job_count(client) == 0


def test_exact_1800_frame_voiced_export_still_requires_audio(client, prepared_project):
    project = timed_project(client, prepared_project, [5.0] * 12)
    response = client.post(
        f"/api/projects/{project['id']}/exports",
        json=export_request(project, silent=False),
    )
    assert response.status_code == 400
    assert response.json()["code"] == "MISSING_AUDIO"
    assert job_count(client) == 0
