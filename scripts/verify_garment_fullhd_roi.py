"""Bounded native FullHD evidence: fabric-blue candidate versus complete Blender alpha.

No fabric-only Blender object ID passes through the current wet/dry PNG pipeline.
A color-derived candidate is NOT semantic ground truth; negative visual findings
must remain INCONCLUSIVE until garment-only native imagery is independently read.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from science_story import Art
from verify_science_art import validate_assets

GARMENT_KINDS = ("shirt", "warm", "wind", "dry")
FULLHD_SIZES = ((1080, 1920), (1920, 1080))
FPS = 30
DURATION_SECONDS = 4
MAX_RADIUS = 2


def frame_window(center: int = 60, radius: int = 1, *, fps: int = FPS) -> list[int]:
    """Bound the native 30 FPS interval to <= 5 consecutive frames per scene."""
    if (
        fps != FPS
        or not 0 <= radius <= MAX_RADIUS
        or not 0 <= center < FPS * DURATION_SECONDS
    ):
        raise ValueError("native ROI window must be bounded within 4 seconds at 30 fps")
    return list(
        range(
            max(0, center - radius),
            min(FPS * DURATION_SECONDS - 1, center + radius) + 1,
        )
    )


def ensure_native_size(size: tuple[int, int]) -> str:
    if size not in FULLHD_SIZES:
        raise ValueError("native garment evidence requires 1080x1920 or 1920x1080")
    return "portrait" if size[1] > size[0] else "landscape"


def geometry(mask: np.ndarray, margin_fraction: float = 0.05) -> dict:
    """Return honest mask bounds without treating a clothesline as fabric."""
    if mask.ndim != 2 or mask.dtype != np.bool_ or not 0 <= margin_fraction < 0.5:
        raise ValueError("invalid binary mask or margin")
    height, width = mask.shape
    ys, xs = np.nonzero(mask)
    if not xs.size:
        return {
            "bbox": None,
            "opaque_pixels": 0,
            "touches_frame_edge": None,
            "outside_safe_zone": None,
        }
    left, right, top, bottom = (
        int(xs.min()),
        int(xs.max()),
        int(ys.min()),
        int(ys.max()),
    )
    edge = left == 0 or right == width - 1 or top == 0 or bottom == height - 1
    mx, my = round(width * margin_fraction), round(height * margin_fraction)
    margin = left <= mx or right >= width - mx or top <= my or bottom >= height - my
    return {
        "bbox": [left, top, right, bottom],
        "opaque_pixels": int(xs.size),
        "touches_frame_edge": edge,
        "outside_safe_zone": margin,
    }


def analyze_isolated(isolated: Image.Image, *, margin_fraction: float = 0.05) -> dict:
    """Compare complete alpha to probable blue cloth; never issue a cloth PASS.

    The original Blender render uses blue cotton and brown line/wooden pegs.
    Shading, seam, water droplets and occlusion prevent color from proving the
    identity or full extent of the fabric, so this is an advisory candidate.
    """
    if isolated.mode != "RGBA":
        raise ValueError("isolated Blender source must be RGBA")
    pixels = np.asarray(isolated, dtype=np.uint8)
    alpha = pixels[:, :, 3] > 180
    if not np.any(alpha):
        raise ValueError("isolated Blender source has no visible alpha")
    red = pixels[:, :, 0].astype(np.uint16)
    green = pixels[:, :, 1].astype(np.uint16)
    blue = pixels[:, :, 2].astype(np.uint16)
    candidate = alpha & (blue * 100 >= green * 105) & (green * 100 >= red * 118)
    candidate &= blue * 100 >= red * 130
    full = geometry(alpha, margin_fraction)
    cloth = geometry(candidate, margin_fraction)
    fraction = round(float(candidate.sum() / alpha.sum()), 6)
    return {
        "composite_alpha": full,
        "blue_cloth_candidate": cloth,
        "candidate_fraction_of_composite": fraction,
        "candidate_method": (
            "Blender blue-cotton RGB heuristic; NOT object-ID segmentation"
        ),
        "verdict": "INCONCLUSIVE_SEMANTIC_CLOTH_CROP",
        "reason": (
            "Color and alpha cannot prove the garment-only silhouette; "
            "seams, droplets, pegs and clothesline can alter this mask."
        ),
    }


def record_frames(samples, *, size: tuple[int, int], fps: int = FPS) -> dict:
    """Accept actual isolated native RGBA and RGB frames in chronological order."""
    aspect = ensure_native_size(size)
    if fps != FPS:
        raise ValueError("native garment sampling must be 30 fps")
    previous_index = None
    previous_alpha = None
    records = []
    for index, isolated, rendered in samples:
        if isolated.size != size or isolated.mode != "RGBA":
            raise ValueError("invalid native isolated RGBA size or mode")
        if rendered.size != size or rendered.mode != "RGB":
            raise ValueError("invalid native rendered RGB size or mode")
        if not 0 <= index < FPS * DURATION_SECONDS:
            raise ValueError("frame index outside 4 second scene")
        if previous_index is not None and index != previous_index + 1:
            raise ValueError("native frame indices must be consecutive")
        analysis = analyze_isolated(isolated)
        alpha = np.asarray(isolated.getchannel("A")) > 180
        if previous_alpha is None:
            iou = None
        else:
            union = int(np.count_nonzero(alpha | previous_alpha))
            iou = round(float(np.count_nonzero(alpha & previous_alpha) / union), 6)
        records.append(
            {
                "frame_index": index,
                "seconds": round(index / fps, 6),
                "sha256_rgba_pixels": hashlib.sha256(isolated.tobytes()).hexdigest(),
                "sha256_rgb_pixels": hashlib.sha256(rendered.tobytes()).hexdigest(),
                "composite_alpha_iou_from_previous": iou,
                **analysis,
            }
        )
        previous_index, previous_alpha = index, alpha
        if len(records) > 2 * MAX_RADIUS + 1:
            raise ValueError("native sample budget exceeded")
    if not records:
        raise ValueError("no native garment samples")
    return {"aspect": aspect, "resolution": list(size), "fps": fps, "frames": records}


def _draw_box(draw: ImageDraw.ImageDraw, bbox, size, origin, tile, color) -> None:
    if bbox is None:
        return
    sx, sy = tile[0] / size[0], tile[1] / size[1]
    left, top, right, bottom = bbox
    draw.rectangle(
        (
            origin[0] + round(left * sx),
            origin[1] + round(top * sy),
            origin[0] + round(right * sx),
            origin[1] + round(bottom * sy),
        ),
        outline=color,
        width=2,
    )


def _composite_sample(art: Art, index: int) -> tuple[Image.Image, Image.Image]:
    seconds = index / FPS
    isolated = Image.new("RGBA", art.size, (0, 0, 0, 0))
    art.shirt(isolated, seconds, DURATION_SECONDS)
    return isolated, art.frame(seconds, DURATION_SECONDS)


def native_evidence(
    art_dir: Path,
    output_dir: Path,
    *,
    center: int = 60,
    radius: int = 1,
    write_native_png: bool = True,
) -> dict:
    """Render <= 40 full-size samples; save one actual native RGB PNG per kind/aspect.

    Only one Art/scene and one previous alpha buffer are held at any time.
    This script is opt-in because adding it to the shared A02 workflow requires
    separately approved workflow ownership; no existing QA gate is modified.
    """
    started = time.perf_counter()
    indices = frame_window(center, radius)
    sources = validate_assets(art_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    storage = 0
    tile = (240, 426)
    for size in FULLHD_SIZES:
        aspect = ensure_native_size(size)
        sheet = Image.new(
            "RGB", (tile[0] * len(indices), tile[1] * len(GARMENT_KINDS)), "#fff8eb"
        )
        draw = ImageDraw.Draw(sheet)
        kinds = {}
        for row, kind in enumerate(GARMENT_KINDS):
            art = Art(*size, art_dir, kind, supersample=1)
            previous = None
            records = []
            for column, index in enumerate(indices):
                isolated, frame = _composite_sample(art, index)
                metrics = analyze_isolated(isolated)
                alpha = np.asarray(isolated.getchannel("A")) > 180
                overlap = None
                if previous is not None:
                    union = int(np.count_nonzero(alpha | previous))
                    overlap = round(
                        float(np.count_nonzero(alpha & previous) / union), 6
                    )
                record = {
                    "frame_index": index,
                    "seconds": round(index / FPS, 6),
                    "sha256_rgba_pixels": hashlib.sha256(
                        isolated.tobytes()
                    ).hexdigest(),
                    "sha256_rgb_pixels": hashlib.sha256(frame.tobytes()).hexdigest(),
                    "composite_alpha_iou_from_previous": overlap,
                    **metrics,
                }
                origin = (column * tile[0], row * tile[1])
                sheet.paste(frame.resize(tile, Image.Resampling.LANCZOS), origin)
                _draw_box(
                    draw,
                    metrics["composite_alpha"]["bbox"],
                    size,
                    origin,
                    tile,
                    "#e45243",
                )
                _draw_box(
                    draw,
                    metrics["blue_cloth_candidate"]["bbox"],
                    size,
                    origin,
                    tile,
                    "#1683d4",
                )
                if write_native_png and index == indices[len(indices) // 2]:
                    dest = output_dir / f"c01-{aspect}-{kind}-f{index:03d}-fullhd.png"
                    frame.save(dest)
                    record["native_sample_file"] = dest.name
                    record["native_sample_sha256"] = hashlib.sha256(
                        dest.read_bytes()
                    ).hexdigest()
                    storage += dest.stat().st_size
                records.append(record)
                previous = alpha
            kinds[kind] = {"frames": records}
        dest = output_dir / f"c01-{aspect}-cloth-roi-contact-sheet.png"
        sheet.save(dest)
        storage += dest.stat().st_size
        result[aspect] = {
            "resolution": list(size),
            "contact_sheet": dest.name,
            "contact_sheet_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
            "kinds": kinds,
        }
    report = {
        "status": "COVERAGE_ADDED; FABRIC_ONLY_CROP_INCONCLUSIVE",
        "source": "real Blender wet/dry RGBA + existing native Art.shirt and Art.frame",
        "sources": sources,
        "fps": FPS,
        "frame_indices": indices,
        "window_seconds": [round(indices[0] / FPS, 6), round(indices[-1] / FPS, 6)],
        "aspect_evidence": result,
        "measured_elapsed_seconds": round(time.perf_counter() - started, 3),
        "stored_sample_bytes": storage,
        "max_native_frames": len(FULLHD_SIZES) * len(GARMENT_KINDS) * len(indices),
        "visual_risk": "Historical 28/28 composite-alpha warnings not waived",
        "creator_g10": "PENDING",
        "limitations": (
            "Blue-cotton pixel candidate is not a cloth object-ID mask; "
            "full human native FullHD video, original voice and rights NOT RUN."
        ),
    }
    out = output_dir / "c01-native-garment-roi-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    report["report_file"] = out.name
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--art-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--center-frame", type=int, default=60)
    parser.add_argument("--radius-frames", type=int, default=1)
    parser.add_argument("--no-native-png", action="store_true")
    args = parser.parse_args()
    report = native_evidence(
        args.art_dir,
        args.output_dir,
        center=args.center_frame,
        radius=args.radius_frames,
        write_native_png=not args.no_native_png,
    )
    print(json.dumps({"report": report["report_file"], "status": report["status"]}))


if __name__ == "__main__":
    main()
