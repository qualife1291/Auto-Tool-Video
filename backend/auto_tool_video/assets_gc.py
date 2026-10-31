"""Quota accounting and conservative cleanup of unused imported assets."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from .store import Store

logger = logging.getLogger(__name__)
IMPORT_KINDS = frozenset({"image", "clip", "audio"})
MAX_PROJECT_IMPORT_BYTES = 500 * 1024**2
DEFAULT_GRACE_SECONDS = 24 * 60 * 60


def project_import_usage(conn: Any, project_id: str) -> int:
    """Exported videos are output evidence, not imported-media quota."""
    return sum(
        int(item.get("size", 0))
        for row in conn.execute("SELECT data FROM assets")
        if (item := json.loads(row[0])).get("project_id") == project_id
        and item.get("kind") in IMPORT_KINDS
    )


def _scene_references(project: dict[str, Any]) -> set[str]:
    return {
        value
        for scene in project.get("scenes", [])
        for field in ("image_id", "audio_id")
        if (value := scene.get(field))
    }


def _eligible_file(store: Store, asset: dict[str, Any], cutoff: float) -> Path | None:
    """Never follow or delete a path outside the dedicated asset directory."""
    directory = (store.root / "assets").resolve()
    try:
        raw = store.root / asset["path"]
        path = raw.resolve()
        if (
            not raw.is_relative_to(directory)
            or not path.is_relative_to(directory)
            or raw.is_symlink()
            or not path.is_file()
            or path.stat().st_mtime > cutoff
        ):
            return None
    except (KeyError, TypeError, ValueError, OSError):
        return None
    return path


def collect_garbage(
    store: Store, project_id: str | None = None, *, min_age_seconds: float = DEFAULT_GRACE_SECONDS
) -> dict[str, int]:
    """Delete only stale, unreferenced imported assets.

    Database row removal is serialized against uploads and job claims; physical
    file deletion follows commit so a filesystem error cannot corrupt the DB.
    The next sweep may remove files left behind by an interrupted unlink.
    """
    cutoff = time.time() - max(0, min_age_seconds)
    pending: list[tuple[Path, int]] = []
    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        protected: set[str] = set()
        for row in conn.execute("SELECT data FROM projects"):
            project = json.loads(row[0])
            protected.update(_scene_references(project))
        for row in conn.execute("SELECT data FROM jobs"):
            job = json.loads(row[0])
            if job["state"] in {"queued", "running"}:
                protected.update(_scene_references(job.get("snapshot", {})))
            if (
                job["state"] == "succeeded"
                and job.get("applied_revision") is None
                and job.get("options", {}).get("kind") == "image"
            ):
                candidate = (job.get("result") or {}).get("candidate_id")
                if candidate:
                    protected.add(candidate)
        for row in conn.execute("SELECT data FROM assets"):
            asset = json.loads(row[0])
            if (
                asset.get("kind") not in IMPORT_KINDS
                or asset.get("id") in protected
                or (project_id is not None and asset.get("project_id") != project_id)
            ):
                continue
            path = _eligible_file(store, asset, cutoff)
            if path is None:
                continue
            conn.execute("DELETE FROM assets WHERE id=?", (asset["id"],))
            pending.append((path, int(asset.get("size", 0))))
    deleted = 0
    freed_bytes = 0
    for path, size in pending:
        try:
            path.unlink(missing_ok=True)
            deleted += 1
            freed_bytes += size
        except OSError:
            logger.exception("Could not unlink unused asset %s", path)
    return {"deleted": deleted, "freed_bytes": freed_bytes}


def gc_after_mutation(store: Store, project_id: str) -> None:
    """Cleanup is best effort and must never fail a successful user request."""
    try:
        collect_garbage(store, project_id)
    except Exception:
        logger.exception("Asset cleanup failed for project %s", project_id)
