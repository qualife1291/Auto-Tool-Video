from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from .domain import (
    PROFILES,
    ApplyInput,
    ExportInput,
    FitAudioInput,
    ImageInput,
    PlanInput,
    ProjectInput,
    ProjectUpdate,
    QualityReviewInput,
    SplitInput,
    split_script,
)
from .generation import apply_generation, enqueue_generation
from .jobs import enqueue, public_job, publish_pack
from .media import MAX_UPLOAD, import_asset
from .providers import capabilities
from .quality import csv_sheet, quality_job, quality_payload, save_review
from .render import FONT_DIR
from .social import upload_hub
from .store import DomainError, Store
from .timing import frames_for


class BodyLimit:
    """Count the stream too: Content-Length alone is insufficient for chunked uploads."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        total = 0

        async def limited_receive():
            nonlocal total
            message = await receive()
            if message["type"] == "http.request":
                total += len(message.get("body", b""))
                if total > MAX_UPLOAD + 1_048_576:
                    raise HTTPException(413, "Yêu cầu quá lớn.")
            return message

        await self.app(scope, limited_receive, send)


def create_app(data_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="Whiteboard Studio", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(BodyLimit)
    store = Store(data_dir)
    app.state.store = store
    port = os.environ.get("APP_PORT", "8765")
    allowed_origins = {
        f"http://{host}:{p}" for host in ("localhost", "127.0.0.1") for p in (port, "5173")
    }

    @app.middleware("http")
    async def guard(request: Request, call_next):
        host = request.url.hostname
        if host not in {"127.0.0.1", "localhost"}:
            return JSONResponse(
                {"code": "FORBIDDEN", "message": "Chỉ dùng trên máy local."}, status_code=403
            )
        if request.method not in {"GET", "HEAD", "OPTIONS"} and (
            request.headers.get("x-studio-client") != "local"
            or request.headers.get("origin", "") not in allowed_origins | {""}
        ):
            return JSONResponse(
                {"code": "FORBIDDEN", "message": "Nguồn yêu cầu không hợp lệ."}, status_code=403
            )
        try:
            length = int(request.headers.get("content-length", "0"))
        except ValueError:
            length = MAX_UPLOAD + 1_048_577
        if length > MAX_UPLOAD + 1_048_576:
            return JSONResponse(
                {"code": "INVALID_ASSET", "message": "Yêu cầu quá lớn."}, status_code=413
            )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        )
        return response

    @app.exception_handler(DomainError)
    async def domain_error(request, exc: DomainError):
        return JSONResponse({"code": exc.code, "message": exc.message}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(
            {
                "code": "VALIDATION_ERROR",
                "message": "Dữ liệu chưa hợp lệ. Kiểm tra độ dài, thời lượng và các trường bắt buộc.",
            },
            status_code=422,
        )

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "ffmpeg": bool(shutil.which("ffmpeg") and shutil.which("ffprobe")),
            "font": (FONT_DIR / "NotoSans-Regular.ttf").is_file(),
            "database": store.db.is_file(),
            "ai": {
                "script": "local_provider",
                "image": "local_provider",
                "speech": "not_implemented",
            },
            "milestone": "M2",
        }

    @app.get("/api/profiles")
    def profiles():
        return PROFILES

    @app.get("/api/capabilities")
    def ai_capabilities():
        return capabilities()

    @app.post("/api/projects/{identifier}/plan", status_code=202)
    def plan(identifier: str, data: PlanInput):
        return public_job(enqueue_generation(store, identifier, data))

    @app.post("/api/projects/{identifier}/plans/{job_id}/apply")
    def apply_plan(identifier: str, job_id: str, data: ApplyInput):
        return apply_generation(store, identifier, job_id, data, "plan")

    @app.post("/api/projects/{identifier}/scenes/{scene_id}/images", status_code=202)
    def generate_image(identifier: str, scene_id: str, data: ImageInput):
        return public_job(enqueue_generation(store, identifier, data, scene_id))

    @app.post("/api/projects/{identifier}/images/{job_id}/apply")
    def apply_image(identifier: str, job_id: str, data: ApplyInput):
        return apply_generation(store, identifier, job_id, data, "image")

    @app.get("/api/social")
    def social():
        return upload_hub()

    @app.get("/api/assets/{identifier}/info")
    def asset_info(identifier: str):
        data = store.get("assets", identifier)
        return {key: value for key, value in data.items() if key not in {"path", "narration"}}

    @app.get("/api/projects")
    def projects():
        return store.list_projects()

    @app.post("/api/projects", status_code=201)
    def create(data: ProjectInput):
        return store.create(data.model_dump())

    @app.get("/api/projects/{identifier}")
    def get_project(identifier: str):
        return store.get("projects", identifier)

    @app.put("/api/projects/{identifier}")
    def save(identifier: str, data: ProjectUpdate):
        payload = data.model_dump()
        if "brief" not in data.model_fields_set:
            payload.pop("brief")
        before = {scene["id"]: scene for scene in store.get("projects", identifier)["scenes"]}
        legacy_defaults = {
            "layout": "board",
            "visual_fit": "contain",
            "transition": "cut",
            "draw_fraction": 0.65,
            "focal_x": 0.5,
            "focal_y": 0.5,
        }
        for scene, original in zip(payload["scenes"], data.scenes, strict=True):
            if scene["id"] in before:
                for key, default in legacy_defaults.items():
                    if key not in original.model_fields_set:
                        scene[key] = before[scene["id"]].get(key, default)
                # Old clients know nothing about per-second beats: don't overwrite
                # an authored plan with Pydantic's empty-list/default-status values.
                # An explicit [] still clears the beats, allowing intentional edits.
                for key, default in (
                    ("second_by_second", []),
                    ("beat_plan_status", "needs_review"),
                ):
                    if key not in original.model_fields_set:
                        scene[key] = before[scene["id"]].get(key, default)
        return store.save(identifier, payload)

    @app.post("/api/projects/{identifier}/fit-audio")
    def fit_audio(identifier: str, data: FitAudioInput):
        project = store.get("projects", identifier)
        if project["revision"] != data.revision:
            raise DomainError("REVISION_CONFLICT", "Lưu hoặc tải lại dự án trước khớp nhịp.", 409)
        if not project["scenes"]:
            raise DomainError("VALIDATION_ERROR", "Tạo cảnh và nhập giọng trước khớp nhịp.")
        for scene in project["scenes"]:
            if not scene.get("audio_id") or scene.get("audio_stale"):
                raise DomainError(
                    "MISSING_AUDIO", "Mọi cảnh cần giọng khớp lời trước khi khớp nhịp."
                )
            asset = store.get("assets", scene["audio_id"])
            frames = max(30, frames_for(asset["duration"] + data.pause_after))
            if scene.get("image_id"):
                visual = store.get("assets", scene["image_id"])
                if visual["kind"] == "clip":
                    frames = max(frames, frames_for(visual["duration"]))
            scene["duration"] = frames / 30
        # All audio references are checked before global limits (MISSING_AUDIO
        # keeps its priority). Count 30fps renderer frames to enforce 600/1800.
        # Store.save accepts raw project dicts and cannot enforce Scene's 20s field.
        if any(frames_for(scene["duration"]) > 600 for scene in project["scenes"]):
            raise DomainError(
                "DURATION_LIMIT",
                "Giọng và khoảng nghỉ vượt 20 giây mỗi cảnh; rút gọn lời trước.",
            )
        if sum(frames_for(s["duration"]) for s in project["scenes"]) > 1800:
            raise DomainError(
                "DURATION_LIMIT", "Giọng và khoảng nghỉ vượt 60 giây; rút gọn lời trước."
            )
        return store.save(identifier, project)

    @app.post("/api/projects/{identifier}/split")
    def split(identifier: str, data: SplitInput):
        project = store.get("projects", identifier)
        if project["scenes"] and not data.replace_existing:
            raise DomainError(
                "CONFIRM_REPLACE", "Đã có cảnh. Xác nhận trước khi thay bằng phân cảnh mới.", 409
            )
        try:
            scenes = split_script(project["narration"])
        except ValueError as error:
            raise DomainError("VALIDATION_ERROR", str(error)) from None
        update = {
            key: project[key] for key in ("title", "profile", "platform", "narration", "aspect")
        }
        return store.save(
            identifier,
            {**update, "revision": data.revision, "scenes": [s.model_dump() for s in scenes]},
        )

    @app.post("/api/projects/{identifier}/scenes/{scene_id}/assets")
    async def upload(
        identifier: str,
        scene_id: str,
        revision: Annotated[int, Form()],
        file: Annotated[UploadFile, File()],
    ):
        try:
            content = await file.read(MAX_UPLOAD + 1)
            return import_asset(store, identifier, scene_id, revision, content)
        finally:
            await file.close()

    @app.get("/api/assets/{identifier}")
    def asset(identifier: str):
        item = store.get("assets", identifier)
        return FileResponse(
            store.asset_path(item),
            media_type=item["mime"],
            filename=f"whiteboard-{item['id']}{Path(item['path']).suffix}",
            content_disposition_type="inline",
        )

    @app.post("/api/projects/{identifier}/exports", status_code=202)
    def export(identifier: str, data: ExportInput):
        return public_job(enqueue(store, identifier, data))

    @app.get("/api/jobs/{identifier}")
    def job(identifier: str):
        return public_job(store.get("jobs", identifier))

    @app.post("/api/jobs/{identifier}/cancel")
    def cancel(identifier: str):
        job = store.get("jobs", identifier)
        if job["state"] not in {"queued", "running"}:
            raise DomainError("REVISION_CONFLICT", "Tác vụ đã kết thúc.", 409)
        return public_job(store.update_job(identifier, state="cancelled"))

    @app.get("/api/projects/{identifier}/exports/{job_id}/quality")
    def export_quality(identifier: str, job_id: str):
        return quality_payload(quality_job(store, identifier, job_id))

    @app.get("/api/projects/{identifier}/exports/{job_id}/quality.csv")
    def export_quality_sheet(identifier: str, job_id: str):
        return Response(
            csv_sheet(quality_payload(quality_job(store, identifier, job_id))),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="quality-review.csv"'},
        )

    @app.put("/api/projects/{identifier}/exports/{job_id}/quality-review")
    def review_export(identifier: str, job_id: str, values: QualityReviewInput):
        return save_review(store, identifier, job_id, values)

    @app.get("/api/projects/{identifier}/publish-pack")
    def pack(
        identifier: str,
        audience: str = "pending",
        rights: str = "pending",
        job_id: str | None = None,
    ):
        from .domain import PublishInput

        try:
            values = PublishInput.model_validate({"audience": audience, "rights": rights})
        except ValueError:
            raise DomainError(
                "VALIDATION_ERROR", "Quyết định audience hoặc bản quyền không hợp lệ."
            ) from None
        project = store.get("projects", identifier)
        if job_id:
            job_data = store.get("jobs", job_id)
            if (
                job_data["project_id"] != identifier
                or job_data["state"] != "succeeded"
                or job_data["options"]["kind"] not in {"preview", "export"}
            ):
                raise DomainError("VALIDATION_ERROR", "Chọn đúng bản xuất thành công của dự án.")
            project = {
                **job_data["snapshot"],
                "aspect": job_data["options"].get("aspect", "portrait"),
            }
        result = publish_pack(project, values.audience, values.rights)
        result.update(export_job_id=job_id, source="export_snapshot" if job_id else "project_draft")
        if job_id:
            result["resolution"] = "1920x1080" if project["aspect"] == "landscape" else "1080x1920"
            quality = quality_payload(job_data)
            result["quality"] = {
                key: quality.get(key)
                for key in (
                    "policy_version",
                    "artifact",
                    "gate",
                    "review_revision",
                    "manual_review",
                )
            }
            review = quality.get("manual_review") or {}
            result["generation_disclosure"] = {
                "origin": review.get("content_origin", "unknown"),
                "creator_note": review.get("disclosure_note", ""),
                "unsigned_provenance": quality.get("provenance"),
                "legal_compliance_certified": False,
            }
            if review.get("content_origin") == "ai_assisted":
                result["description_draft"] += "\nThông tin AI do creator xác nhận: " + (
                    review.get("disclosure_note")
                    or "Nội dung có AI hỗ trợ; kiểm nhãn phù hợp trước đăng."
                )
            if job_data["options"]["kind"] == "preview":
                result["resolution"] = "640x360" if project["aspect"] == "landscape" else "360x640"
        return result

    web = Path(__file__).resolve().parents[2] / "apps" / "web" / "dist"
    if web.is_dir():
        app.mount("/", StaticFiles(directory=web, html=True), name="studio")
    return app
