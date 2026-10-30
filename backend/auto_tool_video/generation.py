from __future__ import annotations

import hashlib
import io
import json
import shutil
import time
import warnings
from typing import Any
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from .domain import ApplyInput, ImageInput, PlanInput
from .planning import planner_data, prompt_messages, validate_proposal
from .providers import Comfy, Ollama, load_workflow
from .render import Cancelled
from .store import DomainError, Store, now


def enqueue_generation(
    store: Store, project_id: str, request: PlanInput | ImageInput, scene_id: str | None = None
) -> dict:
    kind = "image" if isinstance(request, ImageInput) else "plan"
    options = {
        **request.model_dump(exclude={"idempotency_key"}),
        "kind": kind,
        "scene_id": scene_id,
    }
    digest = hashlib.sha256(json.dumps(options, sort_keys=True).encode()).hexdigest()
    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            "SELECT data,input_hash FROM jobs WHERE project_id=? AND idem=?",
            (project_id, request.idempotency_key),
        ).fetchone()
        if existing:
            if existing["input_hash"] != digest:
                raise DomainError("REVISION_CONFLICT", "Khóa tác vụ đã dùng cho yêu cầu khác.", 409)
            return json.loads(existing["data"])
        project = store.get("projects", project_id, conn)
        if project["revision"] != request.revision:
            raise DomainError("REVISION_CONFLICT", "Lưu hoặc tải lại trước khi tạo nội dung.", 409)
        if kind == "plan":
            planner_data(project, options["mode"])
        else:
            scene = next((s for s in project["scenes"] if s["id"] == scene_id), None)
            if not scene:
                raise DomainError("NOT_FOUND", "Không tìm thấy cảnh.", 404)
            if not scene.get("image_prompt", "").strip():
                raise DomainError(
                    "VALIDATION_ERROR", "Điền prompt ảnh hoặc áp dụng storyboard trước."
                )
            if shutil.disk_usage(store.root).free < 2 * 1024**3:
                raise DomainError("DISK_LOW", "Cần ít nhất 2 GiB đĩa trống để tạo ảnh.")
        identifier = str(uuid4())
        job = {
            "id": identifier,
            "project_id": project_id,
            "revision": project["revision"],
            "state": "queued",
            "progress": 0,
            "options": options,
            "snapshot": project,
            "result_id": None,
            "result": None,
            "error": None,
            "created_at": now(),
            "heartbeat": now(),
        }
        conn.execute(
            "INSERT INTO jobs VALUES(?,?,?,?,?,?)",
            (identifier, project_id, request.idempotency_key, digest, "queued", json.dumps(job)),
        )
        return job


def candidate_asset(store: Store, job: dict, content: bytes, provenance: dict) -> dict:
    if (
        not content
        or len(content) > 20 * 1024**2
        or not content.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff"))
    ):
        raise DomainError("MODEL_OUTPUT_INVALID", "Model không trả ảnh PNG/JPEG hợp lệ.", 502)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as source:
                if (
                    source.format not in {"PNG", "JPEG"}
                    or source.width * source.height > 20_000_000
                ):
                    raise ValueError("image")
                source.load()
                rgba = ImageOps.exif_transpose(source).convert("RGBA")
                paper = Image.new("RGBA", rgba.size, "white")
                paper.alpha_composite(rgba)
                image = paper.convert("RGB")
                image.thumbnail((1920, 1920))
                output = io.BytesIO()
                image.save(output, "PNG")
                payload = output.getvalue()
    except (
        ValueError,
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise DomainError(
            "MODEL_OUTPUT_INVALID", "Ảnh model lỗi hoặc quá 20 megapixel.", 502
        ) from None
    identifier = str(uuid4())
    path = store.root / "assets" / f"{identifier}.png"
    asset = {
        "id": identifier,
        "project_id": job["project_id"],
        "scene_id": job["options"]["scene_id"],
        "kind": "image",
        "mime": "image/png",
        "path": str(path.relative_to(store.root)),
        "width": image.width,
        "height": image.height,
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source": "comfyui-local",
        "provenance": {**provenance, "original_sha256": hashlib.sha256(content).hexdigest()},
        "review_required": True,
    }
    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        state = store.get("jobs", job["id"], conn)
        if state["state"] == "cancelled":
            raise Cancelled()
        used = sum(
            item.get("size", 0)
            for row in conn.execute("SELECT data FROM assets")
            if (item := json.loads(row[0])).get("project_id") == job["project_id"]
        )
        if used + len(payload) > 500 * 1024**2:
            raise DomainError("DISK_LOW", "Kho tài nguyên dự án đạt 500 MiB.")
        path.write_bytes(payload)
        try:
            conn.execute("INSERT INTO assets VALUES(?,?)", (identifier, json.dumps(asset)))
        except Exception:
            path.unlink(missing_ok=True)
            raise
    return asset


def run_generation(
    store: Store, job: dict, ollama: Ollama | None = None, comfy: Comfy | None = None
) -> None:
    provider: Ollama | Comfy | None = None
    last_heartbeat = 0.0
    asset: dict | None = None
    result: dict[str, Any]

    def check() -> None:
        nonlocal last_heartbeat
        if store.get("jobs", job["id"])["state"] == "cancelled":
            raise Cancelled()
        if time.monotonic() - last_heartbeat > 1:
            store.update_job(job["id"], progress=0.1)
            last_heartbeat = time.monotonic()

    try:
        check()
        if job["options"]["kind"] == "plan":
            planner = ollama or Ollama()
            provider = planner
            identity = planner.identity()
            for attempt in range(2):
                check()
                store.update_job(job["id"], attempt=attempt + 1)
                raw = planner.chat(
                    prompt_messages(job["snapshot"], job["options"]["mode"], retry=attempt > 0),
                    check,
                )
                try:
                    proposal = validate_proposal(raw, job["snapshot"], job["options"]["mode"])
                    break
                except DomainError as error:
                    if error.code != "MODEL_OUTPUT_INVALID" or attempt == 1:
                        raise
            if planner.identity() != identity:
                raise DomainError(
                    "MODEL_OUTPUT_INVALID", "Model thay đổi trong lúc tạo. Hãy lập kế hoạch lại."
                )
            result = {"proposal": proposal, "provenance": {"provider": "ollama-local", **identity}}
        else:
            config = load_workflow()
            images = comfy or Comfy()
            provider = images
            identity = images.identity(config)
            project = job["snapshot"]
            scene = next(s for s in project["scenes"] if s["id"] == job["options"]["scene_id"])
            brief = project.get("brief", {})
            prompt = "\n".join(
                filter(
                    None,
                    [
                        scene["image_prompt"],
                        brief.get("style_bible", ""),
                        brief.get("character_bible", ""),
                        "No text, letters, logo or watermark. One clear focal subject.",
                    ],
                )
            )
            negative = "text, watermark, logo, unreadable labels, clutter, inconsistent character"
            graph = images.graph(
                config, prompt, negative, job["options"]["seed"], project["aspect"]
            )

            def submitted(prompt_id: str) -> None:
                store.update_job(job["id"], provider_prompt_id=prompt_id)

            content = images.generate(
                config,
                graph,
                job["id"],
                check,
                submitted,
            )
            check()
            asset = candidate_asset(
                store,
                job,
                content,
                {
                    "provider": "comfyui-local",
                    **identity,
                    "seed": job["options"]["seed"],
                    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                    "aspect": project["aspect"],
                },
            )
            result = {
                "candidate_id": asset["id"],
                "provenance": asset["provenance"],
                "review_required": True,
            }
        check()
        updated = store.update_job(job["id"], state="succeeded", progress=1, result=result)
        if updated["state"] == "cancelled" and asset:
            remove_candidate(store, asset)
    except Cancelled:
        if asset:
            remove_candidate(store, asset)
        store.update_job(job["id"], state="cancelled")
    except DomainError as error:
        store.update_job(job["id"], state="failed", error=error.message, error_code=error.code)
    except (OSError, ValueError, KeyError, TypeError):
        store.update_job(
            job["id"],
            state="failed",
            error="Dịch vụ AI trả dữ liệu lỗi. Kiểm cấu hình local rồi thử lại.",
            error_code="MODEL_OUTPUT_INVALID",
        )
    finally:
        if provider:
            provider.close()


def remove_candidate(store: Store, asset: dict) -> None:
    # Only our unpublished, newly created artifact is removed on cancellation.
    path = store.root / asset["path"]
    path.unlink(missing_ok=True)
    with store.connect() as conn:
        conn.execute("DELETE FROM assets WHERE id=?", (asset["id"],))


def apply_generation(
    store: Store, project_id: str, job_id: str, request: ApplyInput, kind: str
) -> dict[str, Any]:
    if not request.confirm:
        raise DomainError("CONFIRM_REQUIRED", "Xem đề xuất và xác nhận trước khi áp dụng.", 409)
    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        project = store.get("projects", project_id, conn)
        job = store.get("jobs", job_id, conn)
        if job["project_id"] != project_id or job["options"]["kind"] != kind:
            raise DomainError("NOT_FOUND", "Đề xuất không thuộc dự án hoặc loại tác vụ này.", 404)
        if job.get("applied_revision") is not None:
            return project
        if job["state"] != "succeeded" or not job.get("result"):
            raise DomainError("VALIDATION_ERROR", "Chỉ áp dụng được kết quả đã hoàn tất.")
        if project["revision"] != request.revision or project["revision"] != job["revision"]:
            raise DomainError(
                "REVISION_CONFLICT",
                "Dự án đã đổi sau lúc tạo. Hãy tạo đề xuất mới để tránh ghi đè.",
                409,
            )
        if kind == "plan":
            proposal = job["result"]["proposal"]
            project["scenes"] = proposal["scenes"]
            if proposal["mode"] == "brief":
                project["title"] = proposal["title"]
                project["narration"] = "\n".join(scene["narration"] for scene in proposal["scenes"])
        else:
            asset = store.get("assets", job["result"]["candidate_id"], conn)
            store.asset_path(asset)
            scene = next(
                (s for s in project["scenes"] if s["id"] == job["options"]["scene_id"]), None
            )
            if not scene or (asset["project_id"], asset["scene_id"]) != (project_id, scene["id"]):
                raise DomainError("INVALID_ASSET", "Ảnh không thuộc cảnh hiện tại.")
            scene["image_id"] = asset["id"]
            asset["review_required"] = False
            conn.execute("UPDATE assets SET data=? WHERE id=?", (json.dumps(asset), asset["id"]))
        project.update(revision=project["revision"] + 1, updated_at=now())
        job["applied_revision"] = project["revision"]
        conn.execute("UPDATE projects SET data=? WHERE id=?", (json.dumps(project), project_id))
        conn.execute("UPDATE jobs SET data=? WHERE id=?", (json.dumps(job), job_id))
        return project
