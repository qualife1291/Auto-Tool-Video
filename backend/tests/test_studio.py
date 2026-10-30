import concurrent.futures
import io
import subprocess
from uuid import uuid4

import numpy as np
import pytest
from conftest import attach, create_story, save
from PIL import Image

from auto_tool_video.domain import ExportInput, split_script
from auto_tool_video.jobs import enqueue
from auto_tool_video.media import probe
from auto_tool_video.render import ScenePainter, render_job
from auto_tool_video.store import DomainError, Store


def options(project, **changes):
    return {
        "revision": project["revision"],
        "silent": True,
        "idempotency_key": str(uuid4()),
        **changes,
    }


def test_split_preserves_vietnamese_and_never_invents_narration():
    text = "Nước bay hơi.\nTrẻ em và người lớn cùng quan sát!"
    assert [s.narration for s in split_script(text)] == text.splitlines()
    with pytest.raises(ValueError):
        split_script(" ")
    with pytest.raises(ValueError):
        split_script("\n".join(["a"] * 21))


def test_create_update_restart_and_revision_conflict(client):
    project = create_story(client)
    old = dict(project)
    project["title"] = "Áo ướt và nước"
    saved = save(client, project)
    assert saved.status_code == 200
    assert save(client, old).status_code == 409
    restored = Store(client.app.state.store.root).get("projects", project["id"])
    assert restored["title"] == "Áo ướt và nước"
    assert restored["scenes"][0]["narration"] == "Nước đi vào không khí."


@pytest.mark.parametrize("title", ["", "x" * 71, " "])
def test_invalid_title_is_rejected(client, title):
    assert client.post("/api/projects", json={"title": title}).status_code == 422


def test_duplicate_scene_ids_rejected(client):
    project = create_story(client)
    project["scenes"][1]["id"] = project["scenes"][0]["id"]
    assert save(client, project).status_code == 400


def test_caption_options_survive_save_and_store_restart(client):
    project = create_story(client)
    assert project["scenes"][0]["caption_style"] == "card"
    project["scenes"][0].update(caption_style="accent", caption_emphasis="không khí")
    response = save(client, project)
    assert response.status_code == 200
    restored = Store(client.app.state.store.root).get("projects", project["id"])
    assert restored["scenes"][0]["caption_style"] == "accent"
    assert restored["scenes"][0]["caption_emphasis"] == "không khí"
    # Old client snapshots without the new fields remain valid and use defaults.
    old = response.json()
    for scene in old["scenes"]:
        scene.pop("caption_style")
        scene.pop("caption_emphasis")
    assert save(client, old).json()["scenes"][0]["caption_style"] == "card"


@pytest.mark.parametrize(
    "patch",
    [
        {"caption_style": "karaoke"},
        {"caption_emphasis": "x" * 71},
        {"caption_style": "<script>"},
    ],
)
def test_invalid_caption_options_rejected(client, patch):
    project = create_story(client)
    project["scenes"][0].update(patch)
    assert save(client, project).status_code == 422


def test_replace_storyboard_requires_confirmation(client):
    project = create_story(client)
    assert (
        client.post(
            f"/api/projects/{project['id']}/split", json={"revision": project["revision"]}
        ).status_code
        == 409
    )


def test_image_import_uses_content_not_name_and_cannot_cross_scene(client, image_bytes):
    project = create_story(client)
    project = attach(client, project, project["scenes"][0], image_bytes, "../../code.html")
    identifier = project["scenes"][0]["image_id"]
    response = client.get(f"/api/assets/{identifier}")
    assert response.status_code == 200 and response.headers["content-type"] == "image/png"
    assert Image.open(io.BytesIO(response.content)).size == (1000, 800)
    project["scenes"][1]["image_id"] = identifier
    assert save(client, project).status_code == 400


@pytest.mark.parametrize(
    "payload",
    [
        b"<script>alert(1)</script>",
        b"\x89PNG\r\n\x1a\nbroken",
        b"RIFFxxxxWAVEbroken",
        b"0000ftypbroken",
    ],
)
def test_fake_media_rejected(client, payload):
    project = create_story(client)
    response = client.post(
        f"/api/projects/{project['id']}/scenes/{project['scenes'][0]['id']}/assets",
        data={"revision": project["revision"]},
        files={"file": ("safe.png", payload)},
    )
    assert response.status_code == 400
    assert client.get(f"/api/projects/{project['id']}").json()["revision"] == project["revision"]


def test_upload_limits_and_source_path_security(client, tmp_path):
    response = client.post(
        "/api/projects",
        content=b"{}",
        headers={"content-length": str(30 * 1024**2), "content-type": "application/json"},
    )
    assert response.status_code == 413
    store = client.app.state.store
    secret = tmp_path.parent / "outside-test.txt"
    secret.write_text("fixture")
    with pytest.raises(DomainError):
        store.asset_path({"path": "../outside-test.txt"})
    (store.root / "assets" / "linked").symlink_to(secret)
    with pytest.raises(DomainError):
        store.asset_path({"path": "assets/linked"})
    secret.unlink()


def test_source_origin_host_and_security_headers(client):
    assert (
        client.post(
            "/api/projects", json={"title": "x"}, headers={"origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert client.get("/api/health", headers={"host": "evil.example"}).status_code == 403
    response = client.get("/api/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.json()["ai"]["image"] == "local_provider"


def test_audio_duration_staleness_and_no_truncation(client, audio_bytes):
    project = create_story(client)
    project = attach(client, project, project["scenes"][0], audio_bytes, "voice.wav")
    assert project["scenes"][0]["duration"] == pytest.approx(1)
    # Uploaded audio is shorter than the minimum editable scene: import must clamp to one second.
    project["scenes"][0]["duration"] = 1
    project["scenes"][0]["narration"] = "Lời thoại mới."
    project["scenes"][0]["audio_stale"] = False
    response = save(client, project)
    assert response.status_code == 200
    assert response.json()["scenes"][0]["audio_stale"] is True


def test_missing_assets_and_silent_confirmation(client, image_bytes):
    project = create_story(client, "Một cảnh.")
    endpoint = f"/api/projects/{project['id']}/exports"
    assert client.post(endpoint, json=options(project)).json()["code"] == "MISSING_IMAGE"
    project = attach(client, project, project["scenes"][0], image_bytes)
    assert (
        client.post(endpoint, json=options(project, silent=False)).json()["code"] == "MISSING_AUDIO"
    )
    assert client.post(endpoint, json=options(project)).status_code == 202


def test_export_idempotency_snapshot_and_payload_conflict(client, image_bytes):
    project = create_story(client, "Một cảnh.")
    project = attach(client, project, project["scenes"][0], image_bytes)
    request = options(project)
    endpoint = f"/api/projects/{project['id']}/exports"
    first = client.post(endpoint, json=request).json()
    assert "snapshot" not in first
    assert client.post(endpoint, json=request).json()["id"] == first["id"]
    assert client.post(endpoint, json={**request, "aspect": "landscape"}).status_code == 409
    project["title"] = "Đã đổi"
    assert save(client, project).status_code == 200
    assert client.post(endpoint, json=request).json()["id"] == first["id"]
    assert client.app.state.store.get("jobs", first["id"])["snapshot"]["title"] != "Đã đổi"


def test_concurrent_double_submit_single_job(client, image_bytes):
    project = create_story(client, "Một cảnh.")
    project = attach(client, project, project["scenes"][0], image_bytes)
    store = client.app.state.store
    request = ExportInput(**options(project))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs = list(pool.map(lambda _: enqueue(store, project["id"], request), range(2)))
    assert jobs[0]["id"] == jobs[1]["id"]


def test_worker_claim_cancel_and_restart(client, image_bytes):
    project = create_story(client, "Một cảnh.")
    project = attach(client, project, project["scenes"][0], image_bytes)
    store = client.app.state.store
    queued = enqueue(store, project["id"], ExportInput(**options(project)))
    assert store.claim()["id"] == queued["id"]
    assert store.claim() is None
    store.interrupt_running()
    assert store.get("jobs", queued["id"])["state"] == "interrupted"
    new = enqueue(store, project["id"], ExportInput(**options(project)))
    client.post(f"/api/jobs/{new['id']}/cancel")
    assert store.update_job(new["id"], state="succeeded")["state"] == "cancelled"


def test_timeline_limit(client, image_bytes):
    project = create_story(client)
    for scene in project["scenes"]:
        project = attach(client, project, scene, image_bytes)
    for scene in project["scenes"]:
        scene["duration"] = 20
    project["scenes"].append(
        {**project["scenes"][0], "id": str(uuid4()), "image_id": None, "duration": 1}
    )
    project = save(client, project).json()
    response = client.post(f"/api/projects/{project['id']}/exports", json=options(project))
    assert response.json()["code"] == "DURATION_LIMIT"


def test_publish_pack_and_manual_upload_are_truthful(client):
    project = create_story(client)
    pack = client.get(f"/api/projects/{project['id']}/publish-pack").json()
    assert pack["audience_decision"] == "pending"
    assert not pack["youtube_kids_inclusion_guaranteed"] and not pack["auto_upload"]
    assert (
        client.get(f"/api/projects/{project['id']}/publish-pack?audience=anything").status_code
        == 400
    )
    social = client.get("/api/social").json()
    assert not social["connected"] and not social["direct_upload_implemented"]
    assert {p["upload_url"] for p in social["providers"].values()} == {
        "https://studio.youtube.com/",
        "https://www.tiktok.com/tiktokstudio/upload",
        "https://www.facebook.com/reels/create/",
    }


def test_renderer_paths_motion_and_caption_boundaries(tmp_path, image_bytes):
    path = tmp_path / "image.png"
    path.write_bytes(image_bytes)
    scene = {
        "title": "Nước ở đâu?",
        "narration": "Chữ tiếng Việt rất dài. " * 10,
        "duration": 1,
        "style": "whiteboard",
    }
    painter = ScenePainter(path, scene, 360, 640, True)
    first = np.array(painter.frame(0))
    last = np.array(painter.frame(1))
    assert np.abs(first.astype(int) - last.astype(int)).sum() > 1000
    assert all(len(page.splitlines()) <= 2 for page in painter.pages)
    motion = ScenePainter(path, {**scene, "style": "motion"}, 640, 360, True)
    assert motion.frame(0).size == (640, 360)
    assert motion.frame(1).size == (640, 360)


@pytest.mark.parametrize(
    "aspect,kind,resolution",
    [
        ("portrait", "preview", (360, 640)),
        ("landscape", "preview", (640, 360)),
        ("portrait", "export", (1080, 1920)),
        ("landscape", "export", (1920, 1080)),
    ],
)
def test_actual_mp4_full_decode_both_aspects(client, image_bytes, aspect, kind, resolution):
    project = create_story(client, "Nước đi đâu?")
    project = attach(client, project, project["scenes"][0], image_bytes)
    project["scenes"][0]["duration"] = 1
    project["brief"]["sources"] = ["https://lab.tongjiang.app/c/water-cycle-step/"]
    project = save(client, project).json()
    store = client.app.state.store
    job = enqueue(store, project["id"], ExportInput(**options(project, kind=kind, aspect=aspect)))
    claimed = store.claim()
    render_job(store, claimed)
    result = store.get("jobs", job["id"])
    assert result["state"] == "succeeded"
    info = probe(store.asset_path(store.get("assets", result["result_id"])))
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"]) == resolution
    assert video["r_frame_rate"] == "30/1"
    assert float(info["format"]["duration"]) == pytest.approx(1, abs=0.06)
    project["brief"]["sources"] = ["https://example.org/new-draft-source"]
    assert save(client, project).status_code == 200
    pack = client.get(f"/api/projects/{project['id']}/publish-pack?job_id={job['id']}").json()
    assert pack["resolution"] == f"{resolution[0]}x{resolution[1]}"
    assert pack["knowledge_sources"] == ["https://lab.tongjiang.app/c/water-cycle-step/"]
    assert pack["knowledge_sources"][0] in pack["description_draft"]
    assert "new-draft-source" not in pack["description_draft"]


def test_mp4_clip_import_and_narration_export(client, image_bytes, audio_bytes, tmp_path):
    clip = tmp_path / "clip.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=640x360:rate=30",
            "-t",
            "1",
            "-c:v",
            "libx264",
            "-threads",
            "1",
            "-pix_fmt",
            "yuv420p",
            str(clip),
        ],
        check=True,
    )
    project = create_story(client, "Giọng fixture là tiếng sine, không phải TTS.")
    project = attach(client, project, project["scenes"][0], clip.read_bytes(), "motion.mp4")
    assert project["scenes"][0]["style"] == "motion"
    project = attach(client, project, project["scenes"][0], audio_bytes, "voice.wav")
    project["scenes"][0]["duration"] = 1
    project = save(client, project).json()
    store = client.app.state.store
    job = enqueue(
        store,
        project["id"],
        ExportInput(**options(project, kind="preview", aspect="landscape", silent=False)),
    )
    render_job(store, store.claim())
    result = store.get("jobs", job["id"])
    assert result["state"] == "succeeded"
    output = store.asset_path(store.get("assets", result["result_id"]))
    samples = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(output), "-map", "0:a:0", "-f", "f32le", "-"],
        capture_output=True,
        check=True,
    ).stdout
    assert np.abs(np.frombuffer(samples, dtype=np.float32)).max() > 0.01


def test_render_failure_not_success(client, image_bytes, monkeypatch):
    project = create_story(client, "Một cảnh.")
    project = attach(client, project, project["scenes"][0], image_bytes)
    store = client.app.state.store
    job = enqueue(store, project["id"], ExportInput(**options(project)))
    claimed = store.claim()
    monkeypatch.setattr(
        "auto_tool_video.render.encode_scene",
        lambda *args: (_ for _ in ()).throw(RuntimeError("failure")),
    )
    with pytest.raises(RuntimeError):
        render_job(store, claimed)
    assert store.get("jobs", job["id"])["state"] == "failed"
    assert not (store.root / "exports" / f"{job['id']}.mp4").exists()


def test_chunked_body_limit_cannot_trust_false_content_length(client):
    chunks = (b"x" * (1024 * 1024) for _ in range(22))
    response = client.post(
        "/api/projects",
        content=chunks,
        headers={"content-length": "10", "content-type": "application/json"},
    )
    assert response.status_code == 413


def test_low_disk_preflight_keeps_previous_state(client, image_bytes, monkeypatch):
    from types import SimpleNamespace

    project = create_story(client, "Một cảnh.")
    project = attach(client, project, project["scenes"][0], image_bytes)
    monkeypatch.setattr(
        "auto_tool_video.jobs.shutil.disk_usage", lambda _: SimpleNamespace(free=100)
    )
    response = client.post(f"/api/projects/{project['id']}/exports", json=options(project))
    assert response.json()["code"] == "DISK_LOW"
    assert client.get(f"/api/projects/{project['id']}").json() == project


def test_cancel_running_encoder_cleans_only_its_job(client, image_bytes):
    import time

    project = create_story(client, "Một cảnh.")
    project = attach(client, project, project["scenes"][0], image_bytes)
    project["scenes"][0]["duration"] = 5
    project = save(client, project).json()
    store = client.app.state.store
    job = enqueue(store, project["id"], ExportInput(**options(project, kind="preview")))
    claimed = store.claim()
    sentinel = store.root / "exports" / "previous.mp4"
    sentinel.write_bytes(b"previous user result fixture")

    def cancel_when_running():
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if store.get("jobs", job["id"])["progress"] > 0:
                store.update_job(job["id"], state="cancelled")
                return
            time.sleep(0.005)
        raise AssertionError("Encoder never reported progress")

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        canceller = pool.submit(cancel_when_running)
        render_job(store, claimed)
        canceller.result()
    assert store.get("jobs", job["id"])["state"] == "cancelled"
    assert not (store.root / "tmp" / job["id"]).exists()
    assert not (store.root / "exports" / f"{job['id']}.mp4").exists()
    assert sentinel.read_bytes() == b"previous user result fixture"


def test_blender_original_template_produces_real_clip(tmp_path):
    import shutil
    from pathlib import Path

    blender = shutil.which("blender")
    if not blender:
        pytest.skip("Blender not installed: original 3D prototype test not run")
    root = Path(__file__).resolve().parents[2]
    output = tmp_path / "particles.mp4"
    subprocess.run(
        [
            blender,
            "-b",
            "--threads",
            "2",
            "--python",
            str(root / "scripts" / "blender_scene.py"),
            "--",
            "--output",
            str(output),
            "--width",
            "320",
            "--height",
            "180",
            "--frames",
            "2",
            "--fps",
            "2",
            "--samples",
            "4",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=90,
    )
    info = probe(output)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"]) == (320, 180)
    assert float(info["format"]["duration"]) == pytest.approx(1)
