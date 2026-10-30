from __future__ import annotations

import hashlib
import json
import shutil
from typing import Any
from uuid import uuid4

from .domain import ExportInput
from .store import DomainError, Store, now


def enqueue(store: Store, project_id: str, options: ExportInput) -> dict[str, Any]:
    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        project = store.get("projects", project_id, conn)
        # Only the request payload participates: a retried request can retrieve its old snapshot.
        request_hash = hashlib.sha256(
            options.model_dump_json(exclude={"idempotency_key"}).encode()
        ).hexdigest()
        existing = conn.execute(
            "SELECT data,input_hash FROM jobs WHERE project_id=? AND idem=?",
            (project_id, options.idempotency_key),
        ).fetchone()
        if existing:
            if existing["input_hash"] != request_hash:
                raise DomainError("REVISION_CONFLICT", "Khóa xuất đã dùng cho yêu cầu khác.", 409)
            return json.loads(existing["data"])
        if project["revision"] != options.revision:
            raise DomainError("REVISION_CONFLICT", "Lưu hoặc tải lại dự án trước khi xuất.", 409)
        if not project["scenes"]:
            raise DomainError("MISSING_IMAGE", "Tạo cảnh và nhập ảnh trước khi xuất.")
        duration = sum(scene["duration"] for scene in project["scenes"])
        if duration > 60:
            raise DomainError(
                "DURATION_LIMIT", "Preset chung tối đa 60 giây. Hãy rút gọn các cảnh."
            )
        for scene in project["scenes"]:
            if not scene["image_id"]:
                raise DomainError("MISSING_IMAGE", f"{scene['title']}: chưa có ảnh.")
            visual = store.get("assets", scene["image_id"], conn)
            store.asset_path(visual)
            if visual["kind"] == "clip" and scene.get("style") != "motion":
                raise DomainError("INVALID_ASSET", "Clip cần chế độ Minh họa chuyển động.")
            if not options.silent:
                if not scene["audio_id"]:
                    raise DomainError(
                        "MISSING_AUDIO",
                        f"{scene['title']}: nhập giọng đọc hoặc chọn xuất không lời đọc.",
                    )
                audio = store.get("assets", scene["audio_id"], conn)
                store.asset_path(audio)
                if scene["audio_stale"] or audio["narration"] != scene["narration"]:
                    raise DomainError(
                        "AUDIO_STALE",
                        f"{scene['title']}: lời thoại đã đổi, cần thu/nhập lại giọng.",
                    )
                if audio["duration"] > scene["duration"]:
                    raise DomainError("DURATION_LIMIT", "Âm thanh dài hơn cảnh.")
        if shutil.disk_usage(store.root).free < 2 * 1024**3:
            raise DomainError("DISK_LOW", "Cần ít nhất 2 GiB đĩa trống để xuất.")
        identifier = str(uuid4())
        job = {
            "id": identifier,
            "project_id": project_id,
            "state": "queued",
            "progress": 0,
            "revision": project["revision"],
            "options": options.model_dump(),
            "snapshot": project,
            "result_id": None,
            "error": None,
            "created_at": now(),
            "heartbeat": now(),
        }
        conn.execute(
            "INSERT INTO jobs VALUES(?,?,?,?,?,?)",
            (
                identifier,
                project_id,
                options.idempotency_key,
                request_hash,
                "queued",
                json.dumps(job),
            ),
        )
    return public_job(job)


def public_job(job: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in job.items() if key not in {"snapshot"}}


def publish_pack(project: dict[str, Any], audience: str, rights: str) -> dict[str, Any]:
    sources = [s for s in project.get("brief", {}).get("sources", []) if s.strip()]
    description = "Video minh họa. Kiểm nguồn kiến thức và quyền tài nguyên trước khi đăng."
    if sources:
        description += "\nNguồn tham khảo (creator cần kiểm chứng):\n" + "\n".join(sources)
    return {
        "schema_version": 1,
        "project_id": project["id"],
        "revision": project["revision"],
        "title": project["title"],
        "language": "vi",
        "platform": project["platform"],
        "viewer_profile": project["profile"],
        "audience_decision": audience,
        "rights_review": rights,
        "resolution": "1920x1080" if project.get("aspect") == "landscape" else "1080x1920",
        "fps": 30,
        "duration_estimate": sum(s["duration"] for s in project["scenes"]),
        "description_draft": description,
        "knowledge_sources": sources,
        "caption_timing": "scene-estimate; chưa căn từng từ",
        "checklist": [
            "Người lớn kiểm nội dung, độ tuổi, sự thật và nguồn tham khảo.",
            "Kiểm quyền dùng ảnh, giọng, nhạc và khai báo nội dung tổng hợp khi cần.",
            "Kiểm mixed audience/made-for-kids; profile không tự quyết định phân loại.",
            "Xem trên điện thoại để kiểm chữ, nút nền tảng che nội dung và âm lượng.",
            "Tải lên YouTube không bảo đảm video xuất hiện trong YouTube Kids.",
        ],
        "auto_upload": False,
        "youtube_kids_inclusion_guaranteed": False,
    }
