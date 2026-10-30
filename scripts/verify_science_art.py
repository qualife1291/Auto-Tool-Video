"""Verify actual Blender wet/dry cutouts and sample science motion.

Run AFTER producing original RGBA art via blender_review_art.py. Unlike
synthetic unit fixtures this checks the real renderer and records visual
contact sheets. Perceptual/physics suitability still requires creator review.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageStat
from science_story import Art


def validate_assets(root: Path) -> dict:
    arrays = {}
    records = {}
    for name in ("wet", "dry"):
        path = root / f"{name}.png"
        with Image.open(path) as img:
            if img.mode != "RGBA" or img.size[0] < 320 or img.size[1] < 320:
                raise ValueError(f"{name} is not a supported RGBA Blender cutout")
            pixels = np.asarray(img).copy()
        alpha = pixels[:, :, 3]
        if int(alpha.min()) != 0 or int(alpha.max()) < 240:
            raise ValueError(f"{name}: invalid transparent alpha")
        visible = alpha > 128
        if not np.any(visible) or np.all(visible):
            raise ValueError(f"{name}: missing isolated silhouette")
        ys, xs = np.where(visible)
        records[name] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "width": pixels.shape[1],
            "height": pixels.shape[0],
            "opaque_pixels": int(visible.sum()),
            "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            "centroid": [round(float(xs.mean()), 2), round(float(ys.mean()), 2)],
        }
        arrays[name] = (pixels, visible)
    if arrays["wet"][0].shape != arrays["dry"][0].shape:
        raise ValueError("wet/dry source dimensions differ")
    overlap = np.count_nonzero(arrays["wet"][1] & arrays["dry"][1])
    union = np.count_nonzero(arrays["wet"][1] | arrays["dry"][1])
    iou = overlap / union
    if iou < 0.94:
        raise ValueError(
            f"wet/dry silhouette alpha mismatch: intersection/union={iou:.3f}"
        )
    a = records["wet"]["centroid"]
    b = records["dry"]["centroid"]
    if abs(a[0] - b[0]) > 3 or abs(a[1] - b[1]) > 3:
        raise ValueError("wet/dry peg/garment centroid moved")
    records["alpha_iou"] = round(iou, 5)
    return records


def contact_sheet(root: Path, output_dir: Path, width: int, height: int) -> dict:
    kinds = ["shirt", "warm", "wind", "spread", "dry"]
    sheet = Image.new("RGB", (width * 3, height * len(kinds)), "#FFF8EB")
    result = {}
    for row, kind in enumerate(kinds):
        art = Art(width, height, root, kind, supersample=1)
        frames = [art.frame(t, 4) for t in (0, 2, 4)]
        for col, frame in enumerate(frames):
            if frame.size != (width, height):
                raise AssertionError("Motion frame dimensions changed")
            sheet.paste(frame, (col * width, row * height))
        changes = [
            float(
                np.mean(
                    np.abs(
                        np.asarray(a, dtype=np.int16) - np.asarray(b, dtype=np.int16)
                    )
                )
            )
            for a, b in itertools.pairwise(frames)
        ]
        if any(change <= 0.02 for change in changes):
            raise AssertionError(
                f"{kind} appears frozen at {width}x{height}: {changes}"
            )
        result[kind] = [round(change, 4) for change in changes]
    label = "portrait" if height > width else "landscape"
    target = output_dir / f"a02-{label}-real-blender-contact-sheet.png"
    sheet.save(target)
    return {"sheet": target.name, "mean_pixel_delta": result}


def fullhd_spread_evidence(root: Path, output_dir: Path) -> dict:
    """Render Blender-backed actual Full HD frames around a 30 FPS transition.

    Static contact sheets at 270x480 cannot establish full-resolution cropping
    or the absence of single-frame teleporting. Save the full frames for T01,
    but never treat these five samples as creator perceptual sign-off.
    """
    result = {}
    times = [
        ("start", 0.0),
        ("before", 2 - 1 / 30),
        ("middle", 2.0),
        ("after", 2 + 1 / 30),
        ("finish", 4.0),
    ]
    for width, height in ((1080, 1920), (1920, 1080)):
        art = Art(width, height, root, "spread", supersample=1)
        label = "portrait" if height > width else "landscape"
        previous = None
        records = []
        for name, seconds in times:
            # Check the *actual* Blender alpha silhouette before compositing;
            # the final RGB scene can hide missing fabric outside the crop.
            isolated = Image.new("RGBA", art.size, (0, 0, 0, 0))
            art.shirt(isolated, seconds, 4, mini=True)
            visible = np.asarray(isolated.getchannel("A")) > 180
            ys, xs = np.where(visible)
            if xs.size < 100:
                raise AssertionError(
                    f"A02 lost unfolded Blender garment: {label} {name}"
                )
            margin_x = round(width * 0.05)
            margin_y = round(height * 0.05)
            if (
                xs.min() <= margin_x
                or xs.max() >= width - margin_x
                or ys.min() <= margin_y
                or ys.max() >= height - margin_y
            ):
                raise AssertionError(
                    f"A02 Blender garment crosses Full HD safe zone: {label} {name}"
                )
            bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
            image = art.frame(seconds, 4)
            if image.size != (width, height):
                raise AssertionError("A02 Full HD native frame dimensions changed")
            target = output_dir / f"a02-{label}-spread-{name}-fullhd.png"
            image.save(target)
            pixels = np.asarray(image, dtype=np.int16)
            if previous is not None:
                delta = float(np.mean(np.abs(pixels - previous)))
                if not 0.0001 < delta < 12:
                    raise AssertionError(
                        f"A02 Full HD spread frame discontinuity: {label} {name} {delta}"
                    )
            else:
                delta = None
            records.append(
                {
                    "name": name,
                    "seconds": seconds,
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                    "file": target.name,
                    "silhouette_bbox": bbox,
                    "mean_pixel_delta_from_previous": delta,
                }
            )
            previous = pixels
        result[label] = {
            "resolution": [width, height],
            "frames": records,
            "source": "Blender cutout / actual native Full HD Art renderer",
            "creator_review": "PENDING",
        }
    return result



def temporal_window(
    center_frame: int = 60,
    radius_frames: int = 3,
    *,
    fps: int = 30,
    duration_seconds: float = 4.0,
) -> list[int]:
    """Choose a bounded, consecutive CFR interval without floating-point stepping."""
    if fps != 30 or not np.isfinite(duration_seconds) or duration_seconds <= 0:
        raise ValueError("temporal evidence requires positive duration and 30 fps")
    if radius_frames < 0:
        raise ValueError("radius_frames must be nonnegative")
    frame_count = int(np.ceil(duration_seconds * fps))
    if not 0 <= center_frame < frame_count:
        raise ValueError("center_frame outside scene")
    return list(
        range(
            max(0, center_frame - radius_frames),
            min(frame_count - 1, center_frame + radius_frames) + 1,
        )
    )


def mask_geometry(
    isolated: Image.Image,
    *,
    margin_fraction: float = 0.05,
    strict_safe_zone: bool = False,
    peg_row: int | None = None,
) -> dict:
    """Inspect actual isolated garment alpha, never composited background RGB."""
    if isolated.mode != "RGBA":
        raise ValueError("garment evidence requires RGBA")
    if not 0 <= margin_fraction < 0.5:
        raise ValueError("invalid safe-zone fraction")
    width, height = isolated.size
    alpha = np.asarray(isolated.getchannel("A"))
    visible = alpha > 180
    count = int(np.count_nonzero(visible))
    if count == 0:
        raise ValueError("garment alpha has no visible pixels")
    columns = visible.sum(axis=0)
    rows = visible.sum(axis=1)
    xs = np.flatnonzero(columns)
    ys = np.flatnonzero(rows)
    left, right = int(xs[0]), int(xs[-1])
    top, bottom = int(ys[0]), int(ys[-1])
    if left == 0 or top == 0 or right == width - 1 or bottom == height - 1:
        raise ValueError("garment alpha cropped at frame edge")
    mx, my = round(width * margin_fraction), round(height * margin_fraction)
    safe = left > mx and right < width - mx and top > my and bottom < height - my
    if strict_safe_zone and not safe:
        raise ValueError("garment alpha crosses required safe zone")
    peg_center = None
    peg_pixels = 0
    if peg_row is not None:
        if not 0 <= peg_row < height:
            raise ValueError("peg row outside frame")
        peg_xs = np.flatnonzero(visible[peg_row])
        peg_pixels = int(peg_xs.size)
        if peg_pixels:
            peg_center = round(float(peg_xs.mean()), 3)
    return {
        "bbox": [left, top, right, bottom],
        "centroid": [
            round(float(np.dot(np.arange(width), columns) / count), 3),
            round(float(np.dot(np.arange(height), rows) / count), 3),
        ],
        "opaque_pixels": count,
        "safe_zone_ok": bool(safe),
        "peg_row": peg_row,
        "peg_centroid_x": peg_center,
        "peg_pixels": peg_pixels,
    }


def record_temporal_sequence(
    samples,
    *,
    fps: int = 30,
    strict_safe_zone: bool = False,
    peg_row: int | None = None,
    output_dir: Path | None = None,
    sample_indices: frozenset[int] = frozenset(),
    sample_prefix: str = "a02",
    on_frame=None,
) -> dict:
    """Stream frame digests/geometry; retain only previous frame and selected PNGs."""
    if fps != 30:
        raise ValueError("temporal sequence must use 30 fps")
    started = time.perf_counter()
    records = []
    previous_frame = None
    previous_mask = None
    previous_index = None
    first_peg = None
    resolution = None
    stored_bytes = 0
    for index, frame, isolated in samples:
        if frame.mode != "RGB" or isolated.mode != "RGBA" or frame.size != isolated.size:
            raise ValueError("RGB/isolated RGBA frames must share dimensions")
        if resolution is not None and frame.size != resolution:
            raise ValueError("temporal frame dimensions changed")
        if previous_index is not None and index != previous_index + 1:
            raise ValueError("temporal frame indices must be consecutive")
        if index < 0:
            raise ValueError("negative frame index")
        resolution = frame.size
        geometry = mask_geometry(
            isolated, strict_safe_zone=strict_safe_zone, peg_row=peg_row
        )
        mask = np.asarray(isolated.getchannel("A")) > 180
        if previous_mask is None:
            alpha_iou = None
            delta = None
        else:
            union = int(np.count_nonzero(mask | previous_mask))
            alpha_iou = round(
                float(np.count_nonzero(mask & previous_mask) / union), 6
            )
            delta = round(
                float(
                    sum(ImageStat.Stat(ImageChops.difference(frame, previous_frame)).mean)
                    / 3
                ),
                6,
            )
        peg_center = geometry["peg_centroid_x"]
        if first_peg is None and peg_center is not None:
            first_peg = peg_center
        peg_shift = (
            round(peg_center - first_peg, 3)
            if peg_center is not None and first_peg is not None
            else None
        )
        record = {
            "frame_index": index,
            "seconds": round(index / fps, 6),
            "sha256_rgb_pixels": hashlib.sha256(frame.tobytes()).hexdigest(),
            "sha256_alpha_pixels": hashlib.sha256(
                isolated.getchannel("A").tobytes()
            ).hexdigest(),
            "geometry": geometry,
            "alpha_iou_from_previous": alpha_iou,
            "mean_rgb_delta_from_previous": delta,
            "peg_shift_from_first_px": peg_shift,
        }
        if output_dir is not None and index in sample_indices:
            target = output_dir / f"{sample_prefix}-f{index:03d}.png"
            frame.save(target)
            stored_bytes += target.stat().st_size
            record["sample_file"] = target.name
            record["sample_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        if on_frame is not None:
            on_frame(index, frame)
        records.append(record)
        previous_frame, previous_mask, previous_index = frame, mask, index
    if not records:
        raise ValueError("no temporal frames")
    return {
        "fps": fps,
        "resolution": list(resolution),
        "frames": records,
        "safe_zone_warnings": sum(
            not record["geometry"]["safe_zone_ok"] for record in records
        ),
        "max_adjacent_rgb_delta": max(
            (record["mean_rgb_delta_from_previous"] or 0) for record in records
        ),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "stored_sample_bytes": stored_bytes,
        "estimated_raw_rgb_bytes": resolution[0] * resolution[1] * 3 * len(records),
    }


def _garment_samples(art: Art, indices: list[int], kind: str):
    for index in indices:
        seconds = index / 30
        isolated = Image.new("RGBA", art.size, (0, 0, 0, 0))
        art.shirt(isolated, seconds, 4, mini=kind == "spread")
        yield index, art.frame(seconds, 4), isolated


def _peg_row(art: Art) -> int:
    y = -25 if art.landscape else 170
    return round(y * art.unit + art.shirts[0].height * 68 / 320)


def temporal_evidence(
    root: Path,
    output_dir: Path,
    *,
    radius_frames: int = 3,
    native_fullhd: bool = True,
) -> dict:
    """Record 30fps garment continuity for two aspects; bounded by 7 frames by default."""
    if not 0 <= radius_frames <= 6:
        raise ValueError("radius_frames must stay within bounded QA budget")
    output_dir.mkdir(parents=True, exist_ok=True)
    indices = temporal_window(radius_frames=radius_frames)
    kinds = ("shirt", "warm", "wind", "spread", "dry")
    preview = {}
    for width, height in ((270, 480), (480, 270)):
        label = "portrait" if height > width else "landscape"
        sheet = Image.new("RGB", (width * len(indices), height * len(kinds)), "#FFF8EB")
        kind_records = {}
        for row, kind in enumerate(kinds):
            art = Art(width, height, root, kind, supersample=1)

            def paste(index, frame, row=row, canvas=sheet, step_x=width, step_y=height):
                canvas.paste(frame, ((index - indices[0]) * step_x, row * step_y))

            kind_records[kind] = record_temporal_sequence(
                _garment_samples(art, indices, kind),
                peg_row=None if kind == "spread" else _peg_row(art),
                on_frame=paste,
            )
        sheet_path = output_dir / f"a02-{label}-30fps-temporal-contact-sheet.png"
        sheet.save(sheet_path)
        preview[label] = {
            "sheet": sheet_path.name,
            "sheet_sha256": hashlib.sha256(sheet_path.read_bytes()).hexdigest(),
            "sheet_bytes": sheet_path.stat().st_size,
            "kinds": kind_records,
        }
    native = {}
    if native_fullhd:
        for width, height in ((1080, 1920), (1920, 1080)):
            label = "portrait" if height > width else "landscape"
            art = Art(width, height, root, "spread", supersample=1)
            native[label] = record_temporal_sequence(
                _garment_samples(art, indices, "spread"),
                strict_safe_zone=True,
                output_dir=output_dir,
                sample_indices=frozenset((indices[0], indices[len(indices) // 2], indices[-1])),
                sample_prefix=f"a02-{label}-spread-temporal",
            )
    return {
        "coverage": "COVERAGE ADDED; NO DEFECT REPRODUCED",
        "source": "actual isolated Blender RGBA through Art.shirt + RGB Art.frame",
        "frame_indices": indices,
        "window_seconds": [round(indices[0] / 30, 6), round(indices[-1] / 30, 6)],
        "preview": preview,
        "native_fullhd_spread": native,
        "creator_g10": "PENDING",
        "limitations": "Machine metrics are not a physical motion or audio approval",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--art-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "source": "REAL Blender Cycles RGBA assets",
        "assets": validate_assets(args.art_dir),
    }
    for width, height in [(270, 480), (480, 270)]:
        report[f"{width}x{height}"] = contact_sheet(
            args.art_dir, args.output_dir, width, height
        )
    report["native_fullhd_spread"] = fullhd_spread_evidence(
        args.art_dir, args.output_dir
    )
    report["temporal_30fps"] = temporal_evidence(args.art_dir, args.output_dir)
    (args.output_dir / "a02-real-art-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
