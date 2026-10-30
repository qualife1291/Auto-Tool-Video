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
from pathlib import Path

import numpy as np
from PIL import Image
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
                raise AssertionError(f"A02 lost unfolded Blender garment: {label} {name}")
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
    (args.output_dir / "a02-real-art-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
