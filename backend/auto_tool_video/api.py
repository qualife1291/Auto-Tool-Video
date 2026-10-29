from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from .domain import PROFILES, ExportInput, ProjectInput, ProjectUpdate, SplitInput, split_script
from .jobs import enqueue, public_job, publish_pack
from .media import MAX_UPLOAD, import_asset
from .render import FONT_DIR
from .social import upload_hub
from .store import DomainError, Store


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
                "script": "not_implemented",
                "image": "not_implemented",
                "speech": "not_implemented",
            },
            "milestone": "M1",
        }

    @app.get("/api/profiles")
    def profiles():
        return PROFILES

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
        return store.save(identifier, data.model_dump())

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
            if job_data["project_id"] != identifier or job_data["state"] != "succeeded":
                raise DomainError("VALIDATION_ERROR", "Chọn đúng bản xuất thành công của dự án.")
            project = {
                **job_data["snapshot"],
                "aspect": job_data["options"].get("aspect", "portrait"),
            }
        result = publish_pack(project, values.audience, values.rights)
        result.update(export_job_id=job_id, source="export_snapshot" if job_id else "project_draft")
        if job_id:
            result["resolution"] = "1920x1080" if project["aspect"] == "landscape" else "1080x1920"
            if job_data["options"]["kind"] == "preview":
                result["resolution"] = "640x360" if project["aspect"] == "landscape" else "360x640"
        return result

    web = Path(__file__).resolve().parents[2] / "apps" / "web" / "dist"
    if web.is_dir():
        app.mount("/", StaticFiles(directory=web, html=True), name="studio")
    return app
