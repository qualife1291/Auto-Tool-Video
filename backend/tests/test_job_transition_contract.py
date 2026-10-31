"""Cancellation and oversized body responses remain race-safe and structured."""

import concurrent.futures
from uuid import uuid4

import pytest
from conftest import attach, create_story

from auto_tool_video.domain import ExportInput
from auto_tool_video.jobs import enqueue
from auto_tool_video.store import DomainError


def queued_job(client, image_bytes):
    project = create_story(client, "Một cảnh.")
    project = attach(client, project, project["scenes"][0], image_bytes)
    return enqueue(
        client.app.state.store,
        project["id"],
        ExportInput(revision=project["revision"], silent=True, idempotency_key=str(uuid4())),
    )


def test_cancel_after_success_is_conflict_and_does_not_mutate_result(client, image_bytes):
    job = queued_job(client, image_bytes)
    store = client.app.state.store
    completed = store.update_job(job["id"], state="succeeded", result_id="immutable")
    response = client.post(f"/api/jobs/{job['id']}/cancel")
    assert response.status_code == 409
    assert response.json()["code"] == "REVISION_CONFLICT"
    assert store.get("jobs", job["id"]) == completed
    assert store.update_job(job["id"], state="cancelled")["state"] == "succeeded"


def test_atomic_cancel_has_one_winner(client, image_bytes):
    job = queued_job(client, image_bytes)
    store = client.app.state.store

    def cancel(_):
        try:
            return store.transition(job["id"], {"queued", "running"}, state="cancelled")[
                "state"
            ]
        except DomainError as exc:
            return exc.status

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(cancel, range(2)))
    assert sorted(results, key=str) == [409, "cancelled"]
    assert store.get("jobs", job["id"])["state"] == "cancelled"


@pytest.mark.parametrize("size_mb", [22, 30])
def test_chunked_oversize_upload_has_consistent_json_413(client, size_mb):
    data = (b"x" * (1024 * 1024) for _ in range(size_mb))
    response = client.post(
        "/api/projects",
        content=data,
        headers={"content-type": "application/json", "content-length": "10"},
    )
    assert response.status_code == 413
    assert response.json() == {
        "code": "INVALID_ASSET",
        "message": "Yêu cầu quá lớn.",
    }


def test_terminal_state_does_not_reopen_when_worker_returns_late(client, image_bytes):
    job = queued_job(client, image_bytes)
    store = client.app.state.store
    store.update_job(job["id"], state="failed", error="decode failure")
    after = store.update_job(job["id"], state="running")
    assert after["state"] == "failed"
    assert after["error"] == "decode failure"
