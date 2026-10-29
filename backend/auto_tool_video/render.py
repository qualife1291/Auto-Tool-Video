from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from itertools import pairwise
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

from .media import probe
from .store import Store

FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
FPS = 30


class Cancelled(Exception):
    pass


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        str(FONT_DIR / ("NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf")), size
    )


def wrap(text: str, face: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        # Hard-wrap unbroken user input, not just ordinary Vietnamese words.
        for char in word:
            if face.getlength(current + char) > width and current:
                lines.append(current.rstrip())
                current = ""
            current += char
        if face.getlength(current + " ") > width:
            lines.append(current)
            current = ""
        else:
            current += " "
    if current.strip():
        lines.append(current.strip())
    return lines or [""]


def caption_pages(text: str, face: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines = wrap(text, face, width)
    return ["\n".join(lines[index : index + 2]) for index in range(0, len(lines), 2)]


class ScenePainter:
    """One monotonic frame stream; preview and final use the same portrait coordinates."""

    def __init__(
        self,
        image_path: Path,
        scene: dict[str, Any],
        width: int,
        height: int,
        captions: bool,
        is_clip: bool = False,
    ):
        self.width, self.height, self.scene = width, height, scene
        self.landscape = width > height
        self.scale = width / (1920 if self.landscape else 1080)
        self.caption_box = (240, 860, 1440, 150) if self.landscape else (90, 1335, 810, 170)
        self.image_box = (240, 230, 1440, 580) if self.landscape else (90, 420, 810, 850)
        self.base = Image.new("RGB", (width, height), "#FFF8EB")
        draw = ImageDraw.Draw(self.base)
        self.subtitle_font = font(max(14, round(48 * self.scale)))
        face = font(max(16, round(56 * self.scale)), True)
        heading = wrap(scene["title"], face, round((1560 if self.landscape else 810) * self.scale))
        while len(heading) > 2 and face.size > round(32 * self.scale):
            face = font(round(face.size) - 1, True)
            heading = wrap(
                scene["title"], face, round((1560 if self.landscape else 810) * self.scale)
            )
        draw.multiline_text(
            (
                round((140 if self.landscape else 90) * self.scale),
                round((80 if self.landscape else 210) * self.scale),
            ),
            "\n".join(heading),
            font=face,
            fill="#254D3D",
            spacing=round(10 * self.scale),
        )
        self.capture = cv2.VideoCapture(str(image_path)) if is_clip else None
        self.clip_index = -1
        self.clip_fps = self.capture.get(cv2.CAP_PROP_FPS) if self.capture else 0
        if self.capture:
            ok, first = self.capture.read()
            if not ok:
                raise RuntimeError("Không giải mã được clip.")
            self.clip_index = 0
            self.source_image = Image.fromarray(cv2.cvtColor(first, cv2.COLOR_BGR2RGB))
        else:
            with Image.open(image_path) as source:
                self.source_image = source.convert("RGB")
        x, y, box_width, box_height = [round(v * self.scale) for v in self.image_box]
        self.image = ImageOps.contain(
            self.source_image, (box_width, box_height), Image.Resampling.LANCZOS
        )
        self.origin = (
            x + (box_width - self.image.width) // 2,
            y + (box_height - self.image.height) // 2,
        )
        gray = cv2.cvtColor(np.array(self.image), cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 60, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        candidates = [
            cv2.approxPolyDP(c, max(0.5, self.scale), False).reshape(-1, 2)
            for c in contours
            if cv2.arcLength(c, False) > 6 * self.scale
        ]
        # A deterministic spatial order avoids flicker and makes cached plans reproducible.
        candidates.sort(
            key=lambda c: (
                int(c[:, 1].min()) // max(1, round(100 * self.scale)),
                int(c[:, 0].min()),
            )
        )
        self.segments: list[tuple[tuple[int, int], tuple[int, int], float]] = []
        cumulative = 0.0
        for contour in candidates[:1200]:
            for a, b in pairwise(contour):
                length = float(np.linalg.norm(b.astype(float) - a.astype(float)))
                if length > 0:
                    cumulative += length
                    self.segments.append(
                        ((int(a[0]), int(a[1])), (int(b[0]), int(b[1])), cumulative)
                    )
        self.total_length = cumulative
        self.mask = Image.new("L", self.image.size, 0)
        self.cursor = 0
        self.pages = (
            caption_pages(
                scene["narration"],
                self.subtitle_font,
                round((self.caption_box[2] - 40) * self.scale),
            )
            if captions and scene["narration"]
            else []
        )

    def frame(self, progress: float) -> Image.Image:
        frame = self.base.copy()
        if self.scene.get("style") == "motion":
            if self.capture:
                target = round(progress * self.scene["duration"] * self.clip_fps)
                while self.clip_index < target:
                    ok, clip_frame = self.capture.read()
                    if not ok:
                        break
                    self.clip_index += 1
                    self.source_image = Image.fromarray(cv2.cvtColor(clip_frame, cv2.COLOR_BGR2RGB))
            x, y, bw, bh = [round(v * self.scale) for v in self.image_box]
            zoom = 0.94 + 0.06 * progress if not self.capture else 1
            visual = ImageOps.contain(
                self.source_image,
                (max(1, round(bw * zoom)), max(1, round(bh * zoom))),
                Image.Resampling.LANCZOS,
            )
            frame.paste(visual, (x + (bw - visual.width) // 2, y + (bh - visual.height) // 2))
            pen = None
        else:
            paper, pen = self.visual_frame(progress)
            frame.paste(paper, self.origin)
        draw = ImageDraw.Draw(frame)
        if pen is not None and 0.015 < progress < 0.65:
            # Original illustrated hand, with the marker tip anchored to the active stroke.
            x, y = pen[0] + self.origin[0], pen[1] + self.origin[1]
            s = self.scale
            draw.polygon(
                [
                    (x + round(dx * s), y + round(dy * s))
                    for dx, dy in [
                        (25, 48),
                        (48, 28),
                        (78, 52),
                        (126, 150),
                        (74, 180),
                        (45, 113),
                        (18, 94),
                    ]
                ],
                fill="#E8B587",
                outline="#B47A54",
            )
            draw.line(
                (x, y, x + round(68 * s), y + round(79 * s)),
                fill="#254D3D",
                width=max(2, round(13 * s)),
            )
            draw.line(
                (x, y, x + round(12 * s), y + round(14 * s)),
                fill="#292B29",
                width=max(1, round(5 * s)),
            )
        if self.pages:
            index = min(len(self.pages) - 1, int(progress * len(self.pages)))
            cx, cy, cw, ch = self.caption_box
            x, y = round(cx * self.scale), round(cy * self.scale)
            draw.rounded_rectangle(
                (x, y, x + round(cw * self.scale), y + round(ch * self.scale)),
                radius=max(4, round(18 * self.scale)),
                fill="#FFFFFF",
            )
            draw.multiline_text(
                (x + round(20 * self.scale), y + round(16 * self.scale)),
                self.pages[index],
                font=self.subtitle_font,
                fill="#202922",
                spacing=max(2, round(12 * self.scale)),
            )
        return frame

    def visual_frame(self, progress: float) -> tuple[Image.Image, tuple[int, int] | None]:
        draw_progress = min(1, progress / 0.65)
        target = self.total_length * draw_progress
        pen = None
        ink = ImageDraw.Draw(self.mask)
        thickness = max(1, round(3 * self.scale))
        while self.cursor < len(self.segments) and self.segments[self.cursor][2] <= target:
            a, b, _ = self.segments[self.cursor]
            ink.line((a, b), fill=255, width=thickness)
            pen = b
            self.cursor += 1
        current_mask = self.mask.copy()
        if self.cursor < len(self.segments) and draw_progress < 1:
            a, b, end = self.segments[self.cursor]
            start = self.segments[self.cursor - 1][2] if self.cursor else 0
            ratio = max(0.0, min(1.0, (target - start) / max(0.001, end - start)))
            pen = (round(a[0] + (b[0] - a[0]) * ratio), round(a[1] + (b[1] - a[1]) * ratio))
            ImageDraw.Draw(current_mask).line((a, pen), fill=255, width=thickness)
        paper = Image.new("RGB", self.image.size, "#FFF8EB")
        paper.paste(Image.new("RGB", self.image.size, "#202922"), mask=current_mask)
        color_progress = max(0.0, min(1.0, (progress - 0.65) / 0.15))
        if color_progress:
            paper = Image.blend(paper, self.image, color_progress)
        return paper, pen

    def close(self) -> None:
        if self.capture:
            self.capture.release()


def encode_scene(
    store: Store,
    scene: dict[str, Any],
    path: Path,
    width: int,
    height: int,
    silent: bool,
    captions: bool,
    progress: Callable[[int], None],
) -> None:
    frames = math.ceil(scene["duration"] * FPS)
    duration = frames / FPS
    visual = store.get("assets", scene["image_id"])
    painter = ScenePainter(
        store.asset_path(visual), scene, width, height, captions, visual["kind"] == "clip"
    )
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(FPS),
        "-i",
        "pipe:0",
    ]
    if silent:
        command += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono"]
    else:
        command += ["-i", str(store.asset_path(store.get("assets", scene["audio_id"])))]
    command += [
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-threads",
        "2",
        "-filter_threads",
        "1",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-ac",
        "1",
        "-af",
        f"apad,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=duration={duration}",
        "-t",
        str(duration),
        str(path),
    ]
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=errors
        )
        try:
            assert process.stdin is not None
            for index in range(frames):
                process.stdin.write(painter.frame(index / max(1, frames - 1)).tobytes())
                if index % 10 == 0:
                    progress(index)
            process.stdin.close()
            if process.wait(timeout=90):
                raise RuntimeError(
                    "Không thể mã hóa cảnh. Kiểm tra FFmpeg/codec và tài nguyên máy."
                )
        except BaseException:
            process.kill()
            process.wait(timeout=10)
            raise
        finally:
            painter.close()


def render_job(store: Store, job: dict[str, Any]) -> None:
    root = store.root / "tmp" / job["id"]
    root.mkdir(exist_ok=False)
    output = store.root / "exports" / f"{job['id']}.mp4"
    landscape = job["options"].get("aspect") == "landscape"
    width, height = (
        ((640, 360) if landscape else (360, 640))
        if job["options"]["kind"] == "preview"
        else ((1920, 1080) if landscape else (1080, 1920))
    )
    total_frames = sum(math.ceil(s["duration"] * FPS) for s in job["snapshot"]["scenes"])
    completed = 0

    def report(frame: int) -> None:
        if store.get("jobs", job["id"])["state"] == "cancelled":
            raise Cancelled()
        if shutil.disk_usage(store.root).free < 256 * 1024**2:
            raise RuntimeError("Đĩa không còn đủ trống.")
        store.update_job(job["id"], progress=min(0.95, (completed + frame) / total_frames * 0.95))

    try:
        segments = []
        for index, scene in enumerate(job["snapshot"]["scenes"]):
            report(0)
            segment = root / f"scene-{index}.mp4"
            encode_scene(
                store,
                scene,
                segment,
                width,
                height,
                job["options"]["silent"],
                job["options"]["captions"],
                report,
            )
            segments.append(segment)
            completed += math.ceil(scene["duration"] * FPS)
        concat = root / "concat.txt"
        concat.write_text(
            "\n".join("file '" + str(p).replace("'", "'\\''") + "'" for p in segments)
        )
        pending = root / "final.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(pending),
            ],
            capture_output=True,
            check=True,
            timeout=120,
        )
        info = probe(pending)
        video = next(stream for stream in info["streams"] if stream["codec_type"] == "video")
        if (video["width"], video["height"], video["codec_name"]) != (width, height, "h264"):
            raise RuntimeError("File xuất không đúng định dạng đã chọn.")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-xerror", "-i", str(pending), "-f", "null", "-"],
            capture_output=True,
            check=True,
            timeout=300,
        )
        report(0)
        pending.replace(output)
        asset = {
            "id": job["id"],
            "project_id": job["project_id"],
            "scene_id": None,
            "kind": "video",
            "mime": "video/mp4",
            "path": str(output.relative_to(store.root)),
            "width": width,
            "height": height,
            "duration": float(info["format"]["duration"]),
            "size": output.stat().st_size,
        }
        with store.connect() as conn:
            conn.execute("INSERT INTO assets VALUES(?,?)", (asset["id"], json.dumps(asset)))
        updated = store.update_job(job["id"], state="succeeded", progress=1, result_id=asset["id"])
        if updated["state"] == "cancelled":
            output.unlink(missing_ok=True)
            with store.connect() as conn:
                conn.execute("DELETE FROM assets WHERE id=?", (asset["id"],))
    except Cancelled:
        store.update_job(job["id"], state="cancelled")
    except Exception:
        store.update_job(
            job["id"],
            state="failed",
            error="Xuất video thất bại. Kiểm tra tệp đầu vào, dung lượng và FFmpeg rồi thử lại.",
        )
        raise
    finally:
        shutil.rmtree(root)
