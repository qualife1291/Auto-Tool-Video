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
