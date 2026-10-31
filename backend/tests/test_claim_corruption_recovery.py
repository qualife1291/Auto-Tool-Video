"""A damaged persisted queue row must not starve healthy worker jobs."""

import json

import pytest

from auto_tool_video.store import Store


@pytest.mark.parametrize(
    "damaged_data",
    [
        "{invalid-json",
        "[]",
        '{"id":"wrong-id","project_id":"project","state":"queued","options":{"kind":"export"}}',
        '{"id":"damaged","project_id":"another-project","state":"queued","options":{"kind":"export"}}',
        '{"id":"damaged","project_id":"project","state":"queued","options":[]}',
        '{"id":"damaged","project_id":"project","state":"queued","options":{}}',
        '{"id":"damaged","project_id":"project","state":"queued","options":{"kind":42}}',
        '{"id":"damaged","project_id":"project","state":"queued","options":{"kind":"unknown"}}',
    ],
)
def test_claim_quarantines_malformed_queued_row_and_claims_next(tmp_path, damaged_data):
    store = Store(tmp_path)
    healthy = {
        "id": "healthy",
        "project_id": "project",
        "state": "queued",
        "options": {"kind": "export"},
    }
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO jobs VALUES(?,?,?,?,?,?)",
            ("damaged", "project", "damaged-key", "hash", "queued", damaged_data),
        )
        conn.execute(
            "INSERT INTO jobs VALUES(?,?,?,?,?,?)",
            ("healthy", "project", "healthy-key", "hash", "queued", json.dumps(healthy)),
        )

    claimed = store.claim()
    assert claimed is not None
    assert claimed["id"] == "healthy"
    assert claimed["state"] == "running"

    damaged = store.get("jobs", "damaged")
    assert damaged["state"] == "failed"
    assert damaged["error_code"] == "INVALID_JOB_DATA"
    assert "error" in damaged
    assert store.claim() is None


@pytest.mark.parametrize(
    "damaged_data",
    [
        "{invalid-json",
        "[]",
        '{"id":"wrong-id","project_id":"project","state":"running","options":{}}',
        '{"id":"damaged","project_id":"project","state":"queued","options":{}}',
    ],
)
def test_startup_quarantines_corrupt_running_row(tmp_path, damaged_data):
    """A single damaged running row must not prevent the worker from starting."""
    store = Store(tmp_path)
    healthy = {
        "id": "healthy",
        "project_id": "project",
        "state": "running",
        "options": {"kind": "export"},
    }
    queued = {
        "id": "queued",
        "project_id": "project",
        "state": "queued",
        "options": {"kind": "export"},
    }
    with store.connect() as conn:
        for identifier, state, data in (
            ("damaged", "running", damaged_data),
            ("healthy", "running", json.dumps(healthy)),
            ("queued", "queued", json.dumps(queued)),
        ):
            conn.execute(
                "INSERT INTO jobs VALUES(?,?,?,?,?,?)",
                (identifier, "project", identifier, "hash", state, data),
            )

    store.interrupt_running()

    damaged = store.get("jobs", "damaged")
    assert damaged["state"] == "failed"
    assert damaged["error_code"] == "INVALID_JOB_DATA"
    assert store.get("jobs", "healthy")["state"] == "interrupted"
    assert store.get("jobs", "queued")["state"] == "queued"
    assert store.claim()["id"] == "queued"
