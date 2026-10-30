"""A02 deterministic motion regression; synthetic silhouettes are NOT Blender acceptance.

These tests exercise the real Science Story Art renderer with two *controlled*
transparent RGBA cutouts. Real Blender output is verified by verify_science_art.py
in the separate A02 workflow; creator perceptual review remains outstanding.
"""

from __future__ import annotations

import importlib.util
import itertools
import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("science_story_a02", ROOT / "scripts/science_story.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Art = module.Art


@pytest.fixture
def shirts(tmp_path):
    # Identical transparent silhouette and peg geometry; colors change between states.
    points = [
        (110, 35),
        (210, 35),
        (235, 65),
        (265, 100),
        (232, 140),
        (216, 119),
        (216, 258),
        (104, 258),
        (104, 119),
        (88, 140),
        (55, 100),
        (85, 65),
    ]
    for filename, color in [
        ("wet.png", (35, 75, 135, 255)),
        ("dry.png", (145, 185, 220, 255)),
    ]:
        cutout = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
        ImageDraw.Draw(cutout).polygon(points, fill=color)
        cutout.save(tmp_path / filename)
    return tmp_path


def rendered_shirt(art, time, *, duration=4, mini=False):
    canvas = Image.new("RGBA", art.size, (0, 0, 0, 0))
    art.shirt(canvas, time, duration, mini=mini)
    return np.asarray(canvas)


def opaque_red_pixels(pixels):
    return pixels[:, :, 0][pixels[:, :, 3] >= 250]


@pytest.mark.parametrize("size", [(270, 480), (480, 270)])
@pytest.mark.parametrize("template", ["warm", "wind", "dry"])
def test_wet_dry_blending_is_monotonic_and_preserves_same_silhouette(
    shirts, size, template
):
    art = Art(*size, shirts, template, supersample=1)
    states = [rendered_shirt(art, time) for time in (0, 2, 4)]
    coverages = [int(np.count_nonzero(state[:, :, 3] > 128)) for state in states]
    assert all(coverage > 100 for coverage in coverages)
    # Sway must not create/disappear an entire second shirt during drying.
    assert max(coverages) / min(coverages) < 1.035
    means = [float(opaque_red_pixels(state).mean()) for state in states]
    assert means[0] + 10 < means[1] < means[2] - 10
    # Outside the garment no stray colored or nontransparent pixels may appear.
    assert all(np.all(state[state[:, :, 3] == 0, 3] == 0) for state in states)


def row_centroid(state, row):
    xs = np.flatnonzero(state[row, :, 3] > 180)
    assert len(xs) > 20, (row, len(xs))
    return float(xs.mean())


@pytest.mark.parametrize("size", [(270, 480), (480, 270)])
def test_wind_sway_keeps_shoulders_stable_while_hem_moves(shirts, size):
    art = Art(*size, shirts, "wind", supersample=1)
    start = rendered_shirt(art, 0)
    peak = rendered_shirt(art, math.pi / (2 * 2.4))
    scale = art.shirts[0].width / 320
    original_y = (-25 if art.landscape else 170) * art.unit
    shoulder_row = round(original_y + 68 * scale)
    hem_row = round(original_y + 230 * scale)
    top_shift = row_centroid(peak, shoulder_row) - row_centroid(start, shoulder_row)
    hem_shift = row_centroid(peak, hem_row) - row_centroid(start, hem_row)
    assert abs(top_shift) < 1.5, (size, top_shift)
    assert abs(hem_shift) > abs(top_shift) + 0.45, (size, top_shift, hem_shift)
    assert abs(hem_shift) < 5, (size, hem_shift)


@pytest.mark.parametrize("size", [(270, 480), (480, 270)])
def test_spread_comparison_grows_the_same_open_cutout_smoothly(shirts, size):
    art = Art(*size, shirts, "spread", supersample=1)
    coverage = [
        int(np.count_nonzero(rendered_shirt(art, time, mini=True)[:, :, 3] > 128))
        for time in np.linspace(0, 4, 9)
    ]
    assert all(left <= right for left, right in itertools.pairwise(coverage))
    assert coverage[-1] > 1.8 * coverage[0]
    # This is the right-hand comparative cutout only, NOT cloth physics or a
    # proven one-object folding transition. The left folded stack is separate.


@pytest.mark.parametrize("size", [(270, 480), (480, 270)])
@pytest.mark.parametrize(
    "template",
    ["shirt", "dry", "warm", "wind", "spread", "molecules", "invisible", "humidity"],
)
def test_first_middle_last_rendered_frames_change_without_dimension_jumps(
    shirts, size, template
):
    art = Art(*size, shirts, template, supersample=1)
    first, middle, final = [np.asarray(art.frame(time, 4)) for time in (0, 2, 4)]
    assert first.shape == middle.shape == final.shape == (size[1], size[0], 3)
    assert first.dtype == middle.dtype == final.dtype == np.uint8
    assert np.any(first != middle), (size, template)
    assert np.any(middle != final), (size, template)


def test_alpha_fixture_fails_closed_when_one_blender_asset_loses_transparency(shirts):
    Image.new("RGB", (320, 320), "blue").save(shirts / "dry.png")
    with pytest.raises(ValueError, match="transparent Blender renders"):
        Art(270, 480, shirts, "wind", supersample=1)
