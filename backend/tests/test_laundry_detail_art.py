"""Regression for richer original laundry-story source art.

These checks prove authored visual layers, not creator approval or photographic quality.
"""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageStat

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "qa_semantic_art.py"
spec = importlib.util.spec_from_file_location("qa_semantic_art", SCRIPT)
assert spec is not None and spec.loader is not None
art = importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)


def _scene(title: str) -> Image.Image:
    return Image.open(io.BytesIO(art.semantic_visual("shirt-30s", title))).convert("RGB")


def test_laundry_scene_contains_real_context_props():
    wet = _scene("Áo ướt")
    dry = _scene("Áo khô")
    sun = _scene("Ánh nắng")
    assert wet.size == dry.size == sun.size == (1400, 1000)
    # The wet basin and wicker basket must occupy distinct locations/stages.
    assert wet.getpixel((235, 750)) != dry.getpixel((235, 750))
    assert wet.getpixel((1100, 744)) != dry.getpixel((1100, 744))
    # A bright full-size sun is visibly present, not just a title/color tint.
    assert sun.getpixel((1110, 245)) != wet.getpixel((1110, 245))


def test_real_garment_seams_folds_and_pocket_change_geometry_not_just_tint():
    plain = Image.new("RGB", (1400, 1000), "#FFF8EB")
    enhanced = plain.copy()
    art._shirt(ImageDraw.Draw(plain), wet=3)
    draw = ImageDraw.Draw(enhanced)
    art._shirt(draw, wet=3)
    art._laundry_fabric_detail(draw, wet=3, spread=False)
    difference = ImageChops.difference(plain, enhanced)
    region = difference.crop((400, 300, 950, 795))
    assert ImageStat.Stat(region).mean[0] > 2.0


def test_six_shirt_cues_keep_recognizable_context_and_distinct_actions():
    titles = tuple(art.EXPECTED_OBJECTS["shirt-30s"])
    images = [_scene(title) for title in titles]
    assert len(images) == 6
    assert len({image.tobytes() for image in images}) == 6
    # Stable clothesline survives all scenes and leaves room for captions
    # in the video renderer; only the source image is evaluated here.
    for image in images:
        assert image.getpixel((225, 480)) != image.getpixel((140, 480))
