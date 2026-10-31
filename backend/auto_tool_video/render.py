from __future__ import annotations

import json
import logging
import math
import re
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from functools import cache
from itertools import pairwise
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

from .layout import boxes, fitted_image
from .media import probe
from .quality import inspect_video, provenance_for
from .store import Store
from .timing import frames_for

FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
FPS = 30


class Cancelled(Exception):
    pass


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        str(FONT_DIR / ("NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf")), size
    )


def wrap(text: str, face: ImageFont.FreeTypeFont, width: int) -> list[str]:
    if width <= 0:
        raise ValueError("Text width must be positive.")
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if face.getlength(candidate) <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        # Preserve Vietnamese words; only split a token that cannot fit an empty line.
        while face.getlength(word) > width and len(word) > 1:
            cut = 1
            while cut < len(word) and face.getlength(word[: cut + 1]) <= width:
                cut += 1
            lines.append(word[:cut])
            word = word[cut:]
        current = word
    if current:
        lines.append(current)
    return lines or [""]


def caption_pages(text: str, face: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines = wrap(text, face, width)
    groups = [lines[i : i + 2] for i in range(0, len(lines), 2)]
    if len(groups) > 1:
        # Balance the entire cue, not only each pair of lines: a greedy last page
        # can otherwise hold just "hơi." for half of the spoken sentence.
        words = [word for line in lines for word in line.split()]
        ideal = len(words) / len(groups)

        @cache
        def partition(start: int, count: int) -> tuple[float, tuple[tuple[str, ...], ...]]:
            if count == 0:
                return (0 if start == len(words) else math.inf, ())
            best: tuple[float, tuple[tuple[str, ...], ...]] = (math.inf, ())
            for end in range(start + 1, len(words) - count + 2):
                candidate = tuple(wrap(" ".join(words[start:end]), face, width))
                if len(candidate) > 2:
                    break
                cost, rest = partition(end, count - 1)
                cost += (end - start - ideal) ** 2 + (1000 if end - start < 3 else 0)
                if cost < best[0]:
                    best = cost, (candidate, *rest)
            return best

        _, balanced = partition(0, len(groups))
        if balanced:
            groups = [list(group) for group in balanced]
    pages = []
    for pair in groups:
        if len(pair) == 2:
            first, second = pair[0].split(), pair[1].split()
            while len(first) > 1:
                old_difference = abs(
                    face.getlength(" ".join(first)) - face.getlength(" ".join(second))
                )
                proposed = [first[-1], *second]
                new_difference = abs(
                    face.getlength(" ".join(first[:-1])) - face.getlength(" ".join(proposed))
                )
                if face.getlength(" ".join(proposed)) > width or new_difference >= old_difference:
                    break
                first, second = first[:-1], proposed
            pair = [" ".join(first), " ".join(second)]
        pages.append("\n".join(pair))
    return pages


def emphasis_spans(lines: list[str], phrase: str) -> list[tuple[int, int] | None]:
    phrase = " ".join(phrase.split())
    match = re.search(re.escape(phrase), " ".join(lines), re.IGNORECASE) if phrase else None
    spans: list[tuple[int, int] | None] = []
    offset = 0
    for line in lines:
        start = max(0, match.start() - offset) if match else 0
        end = min(len(line), match.end() - offset) if match else 0
        spans.append((start, end) if start < end else None)
        offset += len(line) + 1
    return spans


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
        self.layout = scene.get("layout", "board")
        self.fit = scene.get("visual_fit", "contain")
        self.focal = (scene.get("focal_x", 0.5), scene.get("focal_y", 0.5))
        self.draw_fraction = scene.get("draw_fraction", 0.65)
        self.scale = width / (1920 if self.landscape else 1080)
        geometry = boxes(
            1920 if self.landscape else 1080, 1080 if self.landscape else 1920, self.layout
        )
        self.caption_box, self.image_box = geometry["caption"], geometry["image"]
        self.base = Image.new("RGB", (width, height), "#FFF8EB")
        self.heading_layer = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(self.heading_layer)
        self.caption_style = scene.get("caption_style", "card")
        self.subtitle_font = font(max(14, round(48 * self.scale)), self.caption_style != "card")
        face = font(max(16, round(56 * self.scale)), True)
        heading = wrap(scene["title"], face, round((1560 if self.landscape else 810) * self.scale))
        while len(heading) > 2 and face.size > round(32 * self.scale):
            face = font(round(face.size) - 1, True)
            heading = wrap(
                scene["title"], face, round((1560 if self.landscape else 810) * self.scale)
            )
        heading_origin = (
            round((140 if self.landscape else 90) * self.scale),
            round((80 if self.landscape else 190) * self.scale),
        )
        if self.layout == "full_frame":
            bounds = draw.multiline_textbbox(
                heading_origin, "\n".join(heading), font=face, spacing=round(10 * self.scale)
            )
            pad = round(14 * self.scale)
            draw.rounded_rectangle(
                (bounds[0] - pad, bounds[1] - pad, bounds[2] + pad, bounds[3] + pad),
                radius=max(3, round(18 * self.scale)),
                fill=(255, 248, 235, 240),
            )
        draw.multiline_text(
            heading_origin,
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
        self.image = (
            fitted_image(self.source_image, (box_width, box_height), self.fit, self.focal)
            if self.layout == "full_frame"
            else ImageOps.contain(
                self.source_image, (box_width, box_height), Image.Resampling.LANCZOS
            )
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
        # Reveal large silhouettes before small annotations, in a reproducible order.
        candidates.sort(
            key=lambda c: (
                -abs(cv2.contourArea(c)),
                int(c[:, 1].min()) // max(1, round(100 * self.scale)),
                int(c[:, 0].min()),
            )
        )
        # Keep the silhouette first, then choose nearby endpoints to avoid a teleporting pen.
        remaining = candidates[:1200]
        ordered = remaining[:1]
        remaining = remaining[1:]
        while remaining:
            anchor = ordered[-1][-1]
            endpoints = np.array([(c[0], c[-1]) for c in remaining])
            distances = ((endpoints - anchor) ** 2).sum(axis=2)
            choice, reverse = np.unravel_index(distances.argmin(), distances.shape)
            contour = remaining.pop(int(choice))
            ordered.append(contour[::-1] if reverse else contour)
        self.segments: list[tuple[tuple[int, int], tuple[int, int], float, bool]] = []
        cumulative = 0.0
        last: tuple[int, int] | None = None
        for contour in ordered:
            if last is not None:
                start_point = (int(contour[0][0]), int(contour[0][1]))
                cumulative += math.dist(last, start_point) * 0.35
                self.segments.append((last, start_point, cumulative, False))
            for a, b in pairwise(contour):
                length = float(np.linalg.norm(b.astype(float) - a.astype(float)))
                if length > 0:
                    cumulative += length
                    self.segments.append(
                        ((int(a[0]), int(a[1])), (int(b[0]), int(b[1])), cumulative, True)
                    )
            last = (int(contour[-1][0]), int(contour[-1][1]))
        self.pen_down = True
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

    def frame(self, progress: float, overlays: bool = True) -> Image.Image:
        frame = self.base.copy()
        if self.scene.get("style") == "motion":
            if self.capture:
                frame_time = progress * (frames_for(self.scene["duration"]) - 1) / FPS
                target = int(frame_time * self.clip_fps + 1e-6)
                while self.clip_index < target:
                    ok, clip_frame = self.capture.read()
                    if not ok:
                        break
                    self.clip_index += 1
                    self.source_image = Image.fromarray(cv2.cvtColor(clip_frame, cv2.COLOR_BGR2RGB))
            x, y, bw, bh = [round(v * self.scale) for v in self.image_box]
            eased = progress * progress * (3 - 2 * progress)
            zoom = (
                (1 + 0.025 * eased if self.layout == "full_frame" else 0.94 + 0.06 * eased)
                if not self.capture
                else 1
            )
            visual = fitted_image(
                self.source_image,
                (bw, bh),
                self.fit if self.layout == "full_frame" else "contain",
                self.focal,
                zoom,
            )
            frame.paste(visual, (x, y))
            pen = None
        else:
            paper, pen = self.visual_frame(progress)
            frame.paste(paper, self.origin)
        draw = ImageDraw.Draw(frame)
        if pen is not None and 0.005 < progress < self.draw_fraction:
            # Original illustrated hand, with the marker tip anchored to the active stroke.
            x, y = pen[0] + self.origin[0], pen[1] + self.origin[1]
            s = self.scale
            if self.layout == "full_frame":
                # A compact illustrated marker, rather than a large flat hand hiding the art.
                ink = "#173D33" if self.pen_down else "#72978E"
                draw.line(
                    (x, y, x + round(36 * s), y + round(65 * s)),
                    fill="#FFF8EB",
                    width=max(2, round(16 * s)),
                )
                draw.line(
                    (x, y, x + round(36 * s), y + round(65 * s)),
                    fill=ink,
                    width=max(2, round(10 * s)),
                )
                draw.ellipse(
                    (x - round(3 * s), y - round(3 * s), x + round(3 * s), y + round(3 * s)),
                    fill=ink,
                )
            else:
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
        if overlays:
            self.draw_overlays(frame, progress)
        return frame

    def draw_overlays(self, frame: Image.Image, progress: float) -> None:
        frame.paste(self.heading_layer, mask=self.heading_layer)
        if self.pages:
            self.draw_caption(frame, progress)

    def draw_caption(self, frame: Image.Image, progress: float) -> None:
        draw = ImageDraw.Draw(frame)
        index = min(len(self.pages) - 1, int(progress * len(self.pages)))
        cx, cy, cw, ch = self.caption_box
        x, y, width, height = [round(v * self.scale) for v in (cx, cy, cw, ch)]
        contrast = self.caption_style == "contrast"
        accent = self.caption_style == "accent"
        # Only a brief damped entry for EACH caption page. Afterwards both the
        # background card and glyphs are stationary for comfortable reading.
        page_seconds = self.scene["duration"] / len(self.pages)
        local_seconds = max(0.0, progress * self.scene["duration"] - index * page_seconds)
        if local_seconds < 0.12:
            phase = local_seconds / 0.12
            bounce = 10 * (1 - phase) ** 2 - 3 * math.sin(math.pi * phase)
        elif local_seconds < 0.26:
            bounce = -2.5 * math.sin(math.pi * (local_seconds - 0.12) / 0.14)
        else:
            bounce = 0
        y += round(bounce * self.scale)
        radius = max(4, round((28 if contrast else 18) * self.scale))
        if accent:
            offset = max(1, round(5 * self.scale))
            draw.rounded_rectangle(
                (x + offset, y + offset, x + width + offset, y + height + offset),
                radius=radius,
                fill="#E8E0D0",
            )
        draw.rounded_rectangle(
            (x, y, x + width, y + height), radius=radius, fill="#173D33" if contrast else "#FFFFFF"
        )
        if accent:
            draw.rounded_rectangle(
                (
                    x + round(8 * self.scale),
                    y + round(16 * self.scale),
                    x + round(14 * self.scale),
                    y + height - round(16 * self.scale),
                ),
                radius=max(1, round(3 * self.scale)),
                fill="#F4BE53",
            )
        lines = self.pages[index].splitlines()
        spans = (
            emphasis_spans(lines, self.scene.get("caption_emphasis", ""))
            if accent
            else [None] * len(lines)
        )
        line_height = self.subtitle_font.getbbox("A")[3] + max(2, round(12 * self.scale))
        bounds = [self.subtitle_font.getbbox(line) for line in lines]
        block_top = min(box[1] for box in bounds)
        block_bottom = max(i * line_height + box[3] for i, box in enumerate(bounds))
        text_y = y + round((height - (block_bottom - block_top)) / 2) - block_top
        for line_index, (line, span) in enumerate(zip(lines, spans, strict=True)):
            tx = x + (
                round((width - self.subtitle_font.getlength(line)) / 2)
                if contrast
                else round(24 * self.scale)
            )
            ty = text_y + line_index * line_height
            if span:
                a, b = span
                left = tx + self.subtitle_font.getlength(line[:a])
                right = tx + self.subtitle_font.getlength(line[:b])
                bbox = draw.textbbox((tx, ty), line, font=self.subtitle_font)
                pad = max(1, round(3 * self.scale))
                draw.rounded_rectangle(
                    (round(left) - pad, bbox[1] - pad, round(right) + pad, bbox[3] + pad),
                    radius=max(2, round(5 * self.scale)),
                    fill="#F4BE53",
                )
            draw.text(
                (tx, ty), line, font=self.subtitle_font, fill="#FFF8EB" if contrast else "#202922"
            )

    def visual_frame(self, progress: float) -> tuple[Image.Image, tuple[int, int] | None]:
        draw_progress = min(1, progress / self.draw_fraction)
        target = self.total_length * draw_progress
        pen = None
        ink = ImageDraw.Draw(self.mask)
        thickness = max(1, round(3 * self.scale))
        while self.cursor < len(self.segments) and self.segments[self.cursor][2] <= target:
            a, b, _, down = self.segments[self.cursor]
            if down:
                ink.line((a, b), fill=255, width=thickness)
            pen = b
            self.cursor += 1
        current_mask = self.mask.copy()
        if self.cursor < len(self.segments) and draw_progress < 1:
            a, b, end, self.pen_down = self.segments[self.cursor]
            start = self.segments[self.cursor - 1][2] if self.cursor else 0
            ratio = max(0.0, min(1.0, (target - start) / max(0.001, end - start)))
            pen = (round(a[0] + (b[0] - a[0]) * ratio), round(a[1] + (b[1] - a[1]) * ratio))
            if self.pen_down:
                ImageDraw.Draw(current_mask).line((a, pen), fill=255, width=thickness)
        paper = Image.new("RGB", self.image.size, "#FFF8EB")
        paper.paste(Image.new("RGB", self.image.size, "#202922"), mask=current_mask)
        color_progress = max(
            0.0, min(1.0, (progress - self.draw_fraction) / min(0.12, 1 - self.draw_fraction))
        )
        if color_progress:
            paper = Image.blend(paper, self.image, color_progress)
        return paper, pen

    def close(self) -> None:
        if self.capture:
            self.capture.release()


def transition_visual(
    previous: Image.Image | None, current: Image.Image, index: int, frames: int, enabled: bool
) -> Image.Image:
    length = min(5, max(1, frames // 6))
    if previous is None or not enabled or index >= length:
        return current
    return Image.blend(previous, current, (index + 1) / length)


def encode_scene(
    store: Store,
    scene: dict[str, Any],
    path: Path,
    width: int,
    height: int,
    silent: bool,
    captions: bool,
    progress: Callable[[int], None],
    previous_visual: Image.Image | None = None,
) -> Image.Image:
    frames = frames_for(scene["duration"])
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
        "-map",
        "0:v:0",
        "-an",
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
        str(path),
    ]
    last_visual = None
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=errors
        )
        try:
            assert process.stdin is not None
            for index in range(frames):
                t = index / max(1, frames - 1)
                last_visual = painter.frame(t, overlays=False)
                composed = transition_visual(
                    previous_visual,
                    last_visual,
                    index,
                    frames,
                    scene.get("transition", "cut") == "dissolve",
                ).copy()
                painter.draw_overlays(composed, t)
                process.stdin.write(composed.tobytes())
                if index % 10 == 0:
                    progress(index)
            process.stdin.close()
            if process.wait(timeout=90):
                raise RuntimeError("Không thể mã hóa cảnh. Kiểm tra FFmpeg và tài nguyên máy.")
        except BaseException:
            process.kill()
            process.wait(timeout=10)
            raise
        finally:
            painter.close()
    assert last_visual is not None
    return last_visual


def narration_track(store: Store, job: dict, output: Path) -> int:
    scenes = job["snapshot"]["scenes"]
    counts = [frames_for(scene["duration"]) * (48000 // FPS) for scene in scenes]
    command = ["ffmpeg", "-v", "error", "-y", "-filter_complex_threads", "1"]
    if job["options"]["silent"]:
        command += [
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=mono",
            "-af",
            f"atrim=end_sample={sum(counts)}",
        ]
    else:
        filters = []
        for index, (scene, samples) in enumerate(zip(scenes, counts, strict=True)):
            command += ["-i", str(store.asset_path(store.get("assets", scene["audio_id"])))]
            filters.append(
                f"[{index}:a:0]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=mono,apad,atrim=end_sample={samples},asetpts=PTS-STARTPTS[a{index}]"
            )
        filters.append(
            "".join(f"[a{i}]" for i in range(len(scenes))) + f"concat=n={len(scenes)}:v=0:a=1[out]"
        )
        command += ["-filter_complex", ";".join(filters), "-map", "[out]"]
    command += ["-c:a", "pcm_s16le", "-ar", "48000", "-ac", "1", str(output)]
    subprocess.run(command, capture_output=True, check=True, timeout=120)
    return sum(counts)


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
    total_frames = sum(frames_for(s["duration"]) for s in job["snapshot"]["scenes"])
    completed = 0
    last_qc_check = 0.0

    def report(frame: int) -> None:
        if store.get("jobs", job["id"])["state"] == "cancelled":
            raise Cancelled()
        if shutil.disk_usage(store.root).free < 256 * 1024**2:
            raise RuntimeError("Đĩa không còn đủ trống.")
        store.update_job(job["id"], progress=min(0.95, (completed + frame) / total_frames * 0.95))

    def qc_check() -> None:
        nonlocal last_qc_check
        if time.monotonic() - last_qc_check >= 0.25:
            report(0)
            last_qc_check = time.monotonic()

    try:
        segments = []
        previous_visual = None
        for index, scene in enumerate(job["snapshot"]["scenes"]):
            report(0)
            segment = root / f"scene-{index}.mp4"
            previous_visual = encode_scene(
                store,
                scene,
                segment,
                width,
                height,
                job["options"]["silent"],
                job["options"]["captions"],
                report,
                previous_visual,
            )
            segments.append(segment)
            completed += frames_for(scene["duration"])
        concat = root / "concat.txt"
        concat.write_text(
            "\n".join("file '" + str(p).replace("'", "'\\''") + "'" for p in segments)
        )
        pending = root / "final.mp4"
        audio = root / "narration.wav"
        narration_track(store, job, audio)
        provenance = provenance_for(store, job, qc_check)
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
                "-i",
                str(audio),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-ar",
                "48000",
                "-ac",
                "1",
                "-threads",
                "2",
                "-filter_threads",
                "1",
                "-af",
                "anull" if job["options"]["silent"] else "loudnorm=I=-16:TP=-2.0:LRA=11",
                "-movflags",
                "+faststart",
                "-metadata",
                f"comment=Auto-Tool-Video;export_id={job['id']};origin={provenance['origin']};signature=none;provenance=local-sidecar",
                str(pending),
            ],
            capture_output=True,
            check=True,
            timeout=120,
        )
        quality = inspect_video(pending, job["snapshot"], job["options"], provenance, qc_check)
        store.update_job(job["id"], quality_report=quality)
        if quality["technical"]["status"] != "passed":
            raise RuntimeError("Video chưa đạt cổng QC kỹ thuật. Xem báo cáo trước khi xuất lại.")
        info = probe(pending)
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
            "sha256": quality["artifact"]["sha256"],
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
        try:
            store.update_job(
                job["id"],
                state="failed",
                error="Xuất video thất bại. Kiểm tra tệp đầu vào, dung lượng và FFmpeg rồi thử lại.",
            )
        except Exception:
            logging.getLogger(__name__).exception("Could not persist render failure for job %s", job["id"])
        raise
    finally:
        shutil.rmtree(root)
