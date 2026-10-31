"""Regression tests for import quota, active snapshot safety, and stale file GC."""

import json
import os
import time
from uuid import uuid4

from conftest import attach, create_story

from auto_tool_video.assets_gc import collect_garbage, project_import_usage


def add_fake_asset(store, project_id, scene_id, kind, size=1, suffix=".png"):
    identifier = str(uuid4())
    path = store.root / "assets" / (identifier + suffix)
    path.write_bytes(b"fixture")
    asset = {
        "id": identifier,
        "project_id": project_id,
        "scene_id": scene_id,
        "kind": kind,
        "size": size,
        "path": str(path.relative_to(store.root)),
    }
    with store.connect() as conn:
        conn.execute("INSERT INTO assets VALUES (?,?)", (identifier, json.dumps(asset)))
    return asset


def test_exported_video_bytes_never_consume_import_quota(client, image_bytes):
    project = create_story(client, "Một cảnh.")
    store = client.app.state.store
    scene = project["scenes"][0]
    for _ in range(10):
        add_fake_asset(store, project["id"], scene["id"], "video", 55 * 1024**2)
    with store.connect() as conn:
        assert project_import_usage(conn, project["id"]) == 0
    attached = attach(client, project, scene, image_bytes)
    assert attached["scenes"][0]["image_id"]


def test_replaced_image_collects_only_stale_orphans(client, image_bytes):
    project = create_story(client, "Một cảnh.")
    scene = project["scenes"][0]
    store = client.app.state.store
    ids = []
    for _ in range(3):
        project = attach(client, project, scene, image_bytes)
        ids.append(project["scenes"][0]["image_id"])
    for identifier in ids[:2]:
        asset = store.get("assets", identifier)
        path = store.root / asset["path"]
        old = time.time() - 7200
        os.utime(path, (old, old))
    assert collect_garbage(store, project["id"], min_age_seconds=0)["deleted"] == 2
    assert store.get("assets", ids[2])["id"] == ids[2]
    assert len(list((store.root / "assets").glob("*.png"))) == 1


def test_queued_snapshot_keeps_replaced_image(client, image_bytes):
    project = create_story(client, "Một cảnh.")
    store = client.app.state.store
    scene = project["scenes"][0]
    project = attach(client, project, scene, image_bytes)
    first_id = project["scenes"][0]["image_id"]
    job_id = str(uuid4())
    job = {
        "id": job_id,
        "project_id": project["id"],
        "state": "running",
        "options": {"kind": "export"},
        "snapshot": project,
    }
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO jobs VALUES(?,?,?,?,?,?)",
            (job_id, project["id"], job_id, "digest", "running", json.dumps(job)),
        )
    project = attach(client, project, scene, image_bytes)
    first = store.get("assets", first_id)
    path = store.root / first["path"]
    old = time.time() - 7200
    os.utime(path, (old, old))
    assert collect_garbage(store, project["id"], min_age_seconds=0)["deleted"] == 0
    assert path.exists()


def test_gc_does_not_touch_video_or_escape_asset_directory(client, tmp_path):
    project = create_story(client, "Một cảnh.")
    store = client.app.state.store
    scene = project["scenes"][0]
    exported = add_fake_asset(store, project["id"], scene["id"], "video", 100, ".mp4")
    outside = tmp_path.parent / "keep-gc-outside.txt"
    outside.write_text("intact")
    hostile = add_fake_asset(store, project["id"], scene["id"], "image")
    with store.connect() as conn:
        asset = store.get("assets", hostile["id"], conn)
        asset["path"] = "../keep-gc-outside.txt"
        conn.execute("UPDATE assets SET data=? WHERE id=?", (json.dumps(asset), hostile["id"]))
    collect_garbage(store, project["id"], min_age_seconds=0)
    assert outside.read_text() == "intact"
    assert (store.root / exported["path"]).exists()


def test_gc_failure_does_not_fail_successful_import(client, image_bytes, monkeypatch):
    from auto_tool_video import assets_gc

    def broken(*args, **kwargs):
        raise OSError("disk")

    monkeypatch.setattr(assets_gc, "collect_garbage", broken)
    project = create_story(client, "Một cảnh.")
    assert attach(client, project, project["scenes"][0], image_bytes)["revision"] > 0
