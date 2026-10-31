from __future__ import annotations

import hashlib
import io
import json
import math
import subprocess
import warnings
from pathlib import Path
from typing import Any
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from .assets_gc import MAX_PROJECT_IMPORT_BYTES, gc_after_mutation, project_import_usage
from .store import DomainError, Store
from .timing import frames_for

MAX_UPLOAD = 20 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 20_000_000


def probe(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True,
        timeout=15,
        check=True,
    )
    return json.loads(result.stdout)


def import_asset(
    store: Store, project_id: str, scene_id: str, revision: int, content: bytes
) -> dict[str, Any]:
    if not content or len(content) > MAX_UPLOAD:
        raise DomainError("INVALID_ASSET", "Tệp phải có dữ liệu và không quá 20 MiB.")
    project = store.get("projects", project_id)
    if project["revision"] != revision:
        raise DomainError("REVISION_CONFLICT", "Tải lại dự án trước khi nhập tệp.", 409)
    scene = next((item for item in project["scenes"] if item["id"] == scene_id), None)
    if scene is None:
        raise DomainError("NOT_FOUND", "Không tìm thấy cảnh.", 404)
    with store.connect() as conn:
        total = project_import_usage(conn, project_id)
    if total + len(content) > MAX_PROJECT_IMPORT_BYTES:
        raise DomainError("DISK_LOW", "Kho tài nguyên đạt giới hạn 500 MiB của bản đầu tiên.")
    identifier = str(uuid4())
    metadata: dict[str, Any] = {}
    is_image = content.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff"))
    if is_image:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as source:
                    if source.format not in ("PNG", "JPEG"):
                        raise ValueError("format")
                    source.load()
                    if source.width * source.height > 20_000_000:
                        raise ValueError("pixels")
                    image = ImageOps.exif_transpose(source).convert("RGBA")
                    background = Image.new("RGBA", image.size, "white")
                    background.alpha_composite(image)
                    image_rgb = background.convert("RGB")
                    # Bound renderer cost without changing the uploaded original's provenance hash.
                    image_rgb.thumbnail((1920, 1920))
                    buffer = io.BytesIO()
                    image_rgb.save(buffer, "PNG")
                    payload = buffer.getvalue()
                    metadata.update(width=image_rgb.width, height=image_rgb.height)
        except (
            ValueError,
            OSError,
            UnidentifiedImageError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ):
            raise DomainError("INVALID_ASSET", "Ảnh PNG/JPEG lỗi hoặc quá 20 megapixel.") from None
        kind, mime, suffix = "image", "image/png", ".png"
    elif content[4:8] == b"ftyp":
        temp = store.root / "tmp" / f"{identifier}.upload"
        temp.write_bytes(content)
        try:
            info = probe(temp)
            video = next(stream for stream in info["streams"] if stream["codec_type"] == "video")
            duration = float(info["format"]["duration"])
            if (
                not math.isfinite(duration)
                or not 0 < duration <= 19.65
                or video["codec_name"] != "h264"
                or video["width"] * video["height"] > 8_300_000
            ):
                raise ValueError("clip")
            metadata.update(width=video["width"], height=video["height"], duration=duration)
            kind, mime, suffix, payload = "clip", "video/mp4", ".mp4", content
        except (StopIteration, KeyError, ValueError, OSError, subprocess.SubprocessError):
            raise DomainError(
                "INVALID_ASSET", "Clip cần là MP4 H.264, tối đa 19,65s và khoảng 4K mỗi cảnh."
            ) from None
        finally:
            temp.unlink(missing_ok=True)
    elif (
        (content.startswith(b"RIFF") and content[8:12] == b"WAVE")
        or content.startswith(b"ID3")
        or (content[0] == 255 and content[1:2] and content[1] & 224 == 224)
    ):
        temp = store.root / "tmp" / f"{identifier}.upload"
        temp.write_bytes(content)
        try:
            info = probe(temp)
            audio = [s for s in info["streams"] if s["codec_type"] == "audio"]
            duration = float(info["format"]["duration"])
            if not audio or not math.isfinite(duration) or duration <= 0 or duration > 19.65:
                raise ValueError("duration")
            if info["format"]["format_name"] not in ("wav", "mp3"):
                raise ValueError("format")
            metadata.update(duration=duration, narration=scene["narration"])
            suffix = ".wav" if info["format"]["format_name"] == "wav" else ".mp3"
            mime = "audio/wav" if suffix == ".wav" else "audio/mpeg"
            kind, payload = "audio", content
        except (KeyError, ValueError, subprocess.SubprocessError, OSError):
            raise DomainError(
                "INVALID_ASSET", "Chỉ nhận WAV/MP3 giải mã được, tối đa 19,65 giây mỗi cảnh."
            ) from None
        finally:
            temp.unlink(missing_ok=True)
    else:
        raise DomainError("INVALID_ASSET", "Chỉ nhận PNG, JPEG, MP4 H.264, WAV hoặc MP3 thực sự.")
    path = store.root / "assets" / (identifier + suffix)
    asset = {
        "id": identifier,
        "project_id": project_id,
        "scene_id": scene_id,
        "kind": kind,
        "mime": mime,
        "path": str(path.relative_to(store.root)),
        "sha256": hashlib.sha256(content).hexdigest(),
        "size": len(payload),
        "source": "user-import",
        **metadata,
    }
    path.write_bytes(payload)
    try:
        with store.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            current = store.get("projects", project_id, conn)
            if current["revision"] != revision:
                raise DomainError("REVISION_CONFLICT", "Dự án vừa đổi; hãy thử nhập lại.", 409)
            target = next(item for item in current["scenes"] if item["id"] == scene_id)
            previous_duration = target["duration"]
            target[f"{'image' if kind == 'clip' else kind}_id"] = identifier
            clip_attached = kind == "clip"
            if kind == "clip":
                # Use the new measured clip, not a stale prior scene duration.
                frames = max(30, frames_for(duration))
                if target.get("audio_id"):
                    existing_audio = store.get("assets", target["audio_id"], conn)
                    frames = max(frames, frames_for(existing_audio["duration"] + 0.12))
                target.update(style="motion", duration=frames / 30)
            if kind == "audio":
                frames = max(30, frames_for(duration + 0.12))
                if target.get("image_id"):
                    visual = store.get("assets", target["image_id"], conn)
                    if visual["kind"] == "clip":
                        clip_attached = True
                        frames = max(frames, frames_for(visual["duration"]))
                target.update(duration=frames / 30, audio_stale=False)
            if kind in {"clip", "audio"}:
                # Reject before inserting asset/project rows; the staged upload
                # file is removed by the existing rollback handler on errors.
                if frames_for(target["duration"]) > 600:
                    raise DomainError("DURATION_LIMIT", "Clip và giọng vượt 20 giây mỗi cảnh.")
                # Preserve legacy audio-only staging: Fit Audio/export enforce 1800
                # frames when the creator finishes arranging the narration.
                # Motion imports/retimes must reject oversized projects now.
                if (
                    clip_attached
                    and sum(frames_for(s["duration"]) for s in current["scenes"]) > 1800
                ):
                    raise DomainError("DURATION_LIMIT", "Tổng thời lượng vượt 60 giây.")
            # This direct SQL path bypasses Store.save's duration-change invalidation.
            # Keep authored beat text intact, but require re-review after any retime.
            if target["duration"] != previous_duration:
                target["beat_plan_status"] = "needs_review"
            current["revision"] += 1
            from .store import now

            current["updated_at"] = now()
            conn.execute("INSERT INTO assets VALUES(?,?)", (identifier, json.dumps(asset)))
            conn.execute("UPDATE projects SET data=? WHERE id=?", (json.dumps(current), project_id))
    except Exception:
        path.unlink(missing_ok=True)
        raise
    gc_after_mutation(store, project_id)
    return current
