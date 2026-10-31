"""Duration tolerance and path alias safety regressions."""

import json
from uuid import uuid4

import pytest

from auto_tool_video.domain import ExportInput
from auto_tool_video.jobs import enqueue
from auto_tool_video.store import DomainError, Store


def test_save_and_export_accept_same_audio_duration_slack(tmp_path):
    store = Store(tmp_path)
    project = store.create(
        {
            "title": "Timing",
            "narration": "Chào bạn.",
            "platform": "shorts",
            "profile": "family",
            "aspect": "portrait",
        }
    )
    scene = {
        "id": "scene",
        "title": "Một cảnh",
        "narration": "Chào bạn.",
        "duration": 4.0,
        "image_id": "img",
        "audio_id": "wav",
        "audio_stale": False,
    }
    for identifier, kind, extra in [
        ("img", "image", {}),
        ("wav", "audio", {"narration": scene["narration"], "duration": 4.009}),
    ]:
        path = store.root / "assets" / identifier
        path.write_bytes(b"data")
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO assets VALUES (?, ?)",
                (
                    identifier,
                    json.dumps(
                        {
                            "id": identifier,
                            "path": str(path.relative_to(store.root)),
                            "project_id": project["id"],
                            "scene_id": scene["id"],
                            "kind": kind,
                            **extra,
                        }
                    ),
                ),
            )
    saved = store.save(project["id"], {**project, "scenes": [scene]})
    job = enqueue(
        store,
        saved["id"],
        ExportInput(revision=saved["revision"], silent=False, idempotency_key=str(uuid4())),
    )
    assert job["state"] == "queued"


def test_symlink_inside_assets_directory_is_not_accepted(tmp_path):
    store = Store(tmp_path)
    destination = store.root / "assets" / "original.png"
    destination.write_bytes(b"data")
    alias = store.root / "assets" / "alias.png"
    alias.symlink_to(destination)
    with pytest.raises(DomainError) as error:
        store.asset_path({"path": str(alias.relative_to(store.root))})
    assert error.value.code == "INVALID_ASSET"
