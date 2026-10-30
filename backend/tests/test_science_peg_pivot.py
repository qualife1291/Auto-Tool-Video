"""C01 A02 peg pivot: behavioral affine regression on the real Art.shirt path.

Synthetic RGBA fixtures test geometry only. Real Blender and creator perception
require separate independent QA; a matrix check is not a visual sign-off.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "science_story_peg_pivot", ROOT / "scripts/science_story.py"
)
assert spec and spec.loader
science = importlib.util.module_from_spec(spec)
spec.loader.exec_module(science)


@pytest.fixture
def shirt_assets(tmp_path: Path) -> Path:
    # One 320x320 cutout in both states; the real illustrated hanger row is
    # approximately y=68 in this source coordinate system.
    polygon = [
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
    for name, color in (("wet", (35, 75, 135, 255)), ("dry", (145, 185, 220, 255))):
        image = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
        ImageDraw.Draw(image).polygon(polygon, fill=color)
        image.save(tmp_path / f"{name}.png")
    return tmp_path


def _render_affine(art, seconds: float, monkeypatch) -> tuple[tuple[float, ...], np.ndarray]:
    matrices = []
    original = Image.Image.transform

    def record_transform(image, *args, **kwargs):
        if len(args) > 2 and args[1] == Image.Transform.AFFINE and not matrices:
            # Pillow may delegate to transform() internally; capture once.
            matrices.append(tuple(args[2]))
        return original(image, *args, **kwargs)

    canvas = Image.new("RGBA", art.size, (0, 0, 0, 0))
    with monkeypatch.context() as patcher:
        patcher.setattr(Image.Image, "transform", record_transform)
        art.shirt(canvas, seconds, 4.0)
    assert len(matrices) == 1, "Expected the actual cloth affine transform"
    return matrices[0], np.asarray(canvas)


@pytest.mark.parametrize("size", [(270, 480), (480, 270)])
@pytest.mark.parametrize("supersample", [1, 2])
@pytest.mark.parametrize("template,frequency", [("wind", 2.4), ("warm", 1.7)])
def test_real_shirt_affine_keeps_peg_row_stationary(
    shirt_assets: Path,
    size: tuple[int, int],
    supersample: int,
    template: str,
    frequency: float,
    monkeypatch,
) -> None:
    art = science.Art(*size, shirt_assets, template, supersample=supersample)
    baseline, initial = _render_affine(art, 0.0, monkeypatch)
    peak, swaying = _render_affine(art, math.pi / (2 * frequency), monkeypatch)
    peg_y = art.shirts[0].height * 68 / 320
    hem_y = art.shirts[0].height * 230 / 320

    # Pillow's affine matrix maps destination coordinates back to the source.
    # x_src = a*x_dest + b*y_dest + c. For a fixed physical peg at source
    # y=peg_y, displacement is -(b*peg_y+c); no camera/frame re-centering.
    assert baseline == pytest.approx((1, 0, 0, 0, 1, 0), abs=1e-12)
    assert peak[0] == pytest.approx(1)
    assert peak[3:] == pytest.approx((0, 1, 0))
    peg_dx = -(peak[1] * peg_y + peak[2])
    hem_dx = -(peak[1] * hem_y + peak[2])
    assert abs(peg_dx) < 1e-7, (
        f"{size=} {supersample=} {template=} peg shift={peg_dx:.4f}px at source y={peg_y:.3f}px"
    )
    assert abs(hem_dx) > 0.15, "Pivot must not freeze lower-cloth sway"
    assert abs(hem_dx) > abs(peg_dx) + 0.15

    # Verify the rendered path still produces one coherent garment, with no
    # unexpected loss of silhouette/alpha from the new sampling offset.
    alpha_start = initial[:, :, 3] > 128
    alpha_peak = swaying[:, :, 3] > 128
    start_area = int(np.count_nonzero(alpha_start))
    peak_area = int(np.count_nonzero(alpha_peak))
    assert start_area > 100 and peak_area > 100
    assert abs(peak_area - start_area) / start_area < 0.04
