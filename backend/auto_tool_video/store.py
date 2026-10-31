from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .timing import DURATION_EPS


def now() -> str:
    return datetime.now(UTC).isoformat()


class DomainError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code, self.message, self.status = code, message, status


class Store:
    def __init__(self, root: Path | None = None):
        self.root = (
            (root or Path(os.environ.get("APP_DATA_DIR", "~/.local/share/auto-tool-video")))
            .expanduser()
            .resolve()
        )
        for folder in ("assets", "exports", "tmp"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        self.db = self.root / "app.sqlite3"
        with self.connect() as conn:
            conn.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs(
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, idem TEXT NOT NULL,
                input_hash TEXT NOT NULL, state TEXT NOT NULL, data TEXT NOT NULL,
                UNIQUE(project_id, idem));
            """)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def get(
        self, table: str, identifier: str, conn: sqlite3.Connection | None = None
    ) -> dict[str, Any]:
        if table not in {"projects", "assets", "jobs"}:
            raise ValueError("Unknown table")
        if conn is None:
            with self.connect() as connection:
                return self.get(table, identifier, connection)
        row = conn.execute(f"SELECT data FROM {table} WHERE id=?", (identifier,)).fetchone()
        if not row:
            raise DomainError("NOT_FOUND", "Không tìm thấy dữ liệu.", 404)
        return json.loads(row["data"])

    def list_projects(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            data = [json.loads(row[0]) for row in conn.execute("SELECT data FROM projects")]
        return sorted(data, key=lambda item: item["updated_at"], reverse=True)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        project = {
            **data,
            "id": str(uuid4()),
            "revision": 0,
            "scenes": [],
            "created_at": now(),
            "updated_at": now(),
        }
        with self.connect() as conn:
            conn.execute("INSERT INTO projects VALUES(?,?)", (project["id"], json.dumps(project)))
        return project

    def save(self, identifier: str, data: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            old = self.get("projects", identifier, conn)
            if old["revision"] != data["revision"]:
                raise DomainError(
                    "REVISION_CONFLICT", "Dự án đã đổi ở nơi khác. Tải lại trước khi lưu.", 409
                )
            ids = [scene["id"] for scene in data["scenes"]]
            if len(set(ids)) != len(ids):
                raise DomainError("VALIDATION_ERROR", "Mã cảnh không được trùng nhau.")
            old_scenes = {scene["id"]: scene for scene in old["scenes"]}
            for scene in data["scenes"]:
                for field, kind in (("image_id", "image"), ("audio_id", "audio")):
                    if scene.get(field):
                        asset = self.get("assets", scene[field], conn)
                        if (asset["project_id"], asset["scene_id"]) != (
                            identifier,
                            scene["id"],
                        ) or asset["kind"] not in (
                            {"image", "clip"} if kind == "image" else {"audio"}
                        ):
                            raise DomainError("INVALID_ASSET", "Tài nguyên không thuộc cảnh này.")
                before = old_scenes.get(scene["id"], {})
                if before:
                    # Also protect direct Store.save callers which omit the new fields.
                    # API callers are handled before model_dump fills missing defaults.
                    for key, default in (
                        ("second_by_second", []),
                        ("beat_plan_status", "needs_review"),
                    ):
                        if key not in scene:
                            scene[key] = before.get(key, default)
                    # Editing authored cues or narration invalidates their reviewed meaning.
                    # A separate unchanged save can explicitly confirm the revised plan.
                    if (
                        before.get("beat_plan_status") == "authored"
                        and scene.get("beat_plan_status") == "authored"
                        and (
                            scene.get("second_by_second") != before.get("second_by_second")
                            or scene.get("narration") != before.get("narration")
                        )
                    ):
                        scene["beat_plan_status"] = "needs_review"
                    # The timeline was authored against the exact old duration.
                    # Never erase/reindex the creator's beats automatically.
                    if scene["duration"] != before.get("duration"):
                        scene["beat_plan_status"] = "needs_review"
                # A client cannot clear stale audio by simply sending false.
                if scene.get("audio_id"):
                    audio = self.get("assets", scene["audio_id"], conn)
                    scene["audio_stale"] = audio.get("narration") != scene["narration"]
                    if scene["duration"] + DURATION_EPS < audio["duration"]:
                        raise DomainError(
                            "DURATION_LIMIT", "Thời lượng cảnh không được cắt ngắn âm thanh."
                        )
                elif before.get("audio_id"):
                    scene["audio_stale"] = False
            project = {**old, **data, "revision": old["revision"] + 1, "updated_at": now()}
            conn.execute("UPDATE projects SET data=? WHERE id=?", (json.dumps(project), identifier))
        return project

    def asset_path(self, asset: dict[str, Any]) -> Path:
        raw = self.root / asset["path"]
        path = raw.resolve()
        if raw.is_symlink() or not path.is_relative_to(self.root) or not path.is_file():
            raise DomainError("INVALID_ASSET", "Tệp tài nguyên bị thiếu hoặc không hợp lệ.")
        return path

    def transition(self, identifier: str, from_states: set[str], **changes: Any) -> dict[str, Any]:
        """Atomically perform a compare-and-set state transition."""
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            job = self.get("jobs", identifier, conn)
            if job["state"] not in from_states:
                raise DomainError("REVISION_CONFLICT", "Tác vụ đã kết thúc.", 409)
            job.update(changes, heartbeat=now())
            conn.execute(
                "UPDATE jobs SET state=?, data=? WHERE id=?",
                (job["state"], json.dumps(job), identifier),
            )
        return job

    def update_job(self, identifier: str, **changes: Any) -> dict[str, Any]:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            job = self.get("jobs", identifier, conn)
            # Terminal jobs cannot be resurrected by late worker callbacks.
            terminal = {"cancelled", "succeeded", "failed", "interrupted"}
            if job["state"] in terminal and changes.get("state", job["state"]) != job["state"]:
                return job
            job.update(changes, heartbeat=now())
            conn.execute(
                "UPDATE jobs SET state=?, data=? WHERE id=?",
                (job["state"], json.dumps(job), identifier),
            )
        return job

    def claim(self) -> dict[str, Any] | None:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            while True:
                row = conn.execute(
                    "SELECT id,project_id,data FROM jobs WHERE state='queued' ORDER BY rowid LIMIT 1"
                ).fetchone()
                if row is None:
                    return None
                try:
                    job = json.loads(row["data"])
                    if (
                        not isinstance(job, dict)
                        or job.get("id") != row["id"]
                        or job.get("state") != "queued"
                    ):
                        raise ValueError("Queued job metadata does not match its database row")
                except (ValueError, TypeError):
                    # A corrupt row must not poison the entire FIFO queue.
                    # Quarantine it atomically before claiming the next job.
                    failed = {
                        "id": row["id"],
                        "project_id": row["project_id"],
                        "state": "failed",
                        "progress": 0,
                        "options": {},
                        "result_id": None,
                        "error": "Dữ liệu tác vụ trong hàng đợi không hợp lệ.",
                        "error_code": "INVALID_JOB_DATA",
                        "heartbeat": now(),
                    }
                    conn.execute(
                        "UPDATE jobs SET state='failed',data=? WHERE id=?",
                        (json.dumps(failed), row["id"]),
                    )
                    continue
                job.update(state="running", heartbeat=now())
                conn.execute(
                    "UPDATE jobs SET state='running',data=? WHERE id=?",
                    (json.dumps(job), row["id"]),
                )
                return job

    def interrupt_running(self) -> None:
        with self.connect() as conn:
            ids = [row[0] for row in conn.execute("SELECT id FROM jobs WHERE state='running'")]
        for identifier in ids:
            self.update_job(
                identifier, state="interrupted", error="Worker đã dừng. Hãy xuất lại khi sẵn sàng."
            )
