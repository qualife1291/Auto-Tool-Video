"""C01 #88: bounded FullHD cloth ROI evidence, never creator G10 acceptance."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def roi(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "garment_fullhd_roi", ROOT / "scripts/verify_garment_fullhd_roi.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def picture(size=(80, 100), *, cloth=True, rope=True, edge=False):
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if cloth:
        draw.rectangle((20, 30, 60, 75), fill=(32, 115, 170, 255))
    if rope:
        draw.line((0 if edge else 8, 12, 70, 12), fill=(142, 83, 43, 255), width=2)
    return image


@pytest.mark.parametrize(
    "kwargs",
    [
        {"radius": -1},
        {"radius": 3},
        {"fps": 24},
        {"center": -1},
        {"center": 120},
    ],
)
def test_window_is_strictly_bounded_30fps(roi, kwargs):
    with pytest.raises(ValueError, match="bounded"):
        roi.frame_window(**kwargs)
    assert roi.frame_window() == [59, 60, 61]
    assert roi.frame_window(center=0) == [0, 1]
    assert roi.frame_window(center=119) == [118, 119]


@pytest.mark.parametrize("size", [(1080, 1920), (1920, 1080)])
def test_native_fullhd_aspects_only(roi, size):
    assert roi.ensure_native_size(size) in ("portrait", "landscape")
    with pytest.raises(ValueError, match="1080x1920"):
        roi.ensure_native_size((270, 480))


def test_composite_line_touch_does_not_prove_cloth_crop(roi):
    image = picture(edge=True)
    result = roi.analyze_isolated(image)
    assert result["composite_alpha"]["touches_frame_edge"] is True
    assert result["blue_cloth_candidate"]["touches_frame_edge"] is False
    assert result["blue_cloth_candidate"]["bbox"] == [20, 30, 60, 75]
    assert result["verdict"].startswith("INCONCLUSIVE")
    assert 0 < result["candidate_fraction_of_composite"] < 1


def test_candidate_cloth_edge_is_flagged_but_not_waived(roi):
    image = picture()
    ImageDraw.Draw(image).rectangle((0, 40, 20, 50), fill=(30, 120, 190, 255))
    result = roi.analyze_isolated(image)
    assert result["blue_cloth_candidate"]["touches_frame_edge"] is True
    assert result["blue_cloth_candidate"]["outside_safe_zone"] is True
    assert result["verdict"].startswith("INCONCLUSIVE")


def test_empty_cloth_candidate_is_explicitly_inconclusive(roi):
    result = roi.analyze_isolated(picture(cloth=False))
    assert result["blue_cloth_candidate"]["opaque_pixels"] == 0
    assert result["blue_cloth_candidate"]["bbox"] is None
    assert result["verdict"].startswith("INCONCLUSIVE")


def test_bad_alpha_or_missing_asset_fails_closed(roi, tmp_path):
    with pytest.raises(ValueError, match="RGBA"):
        roi.analyze_isolated(Image.new("RGB", (80, 100)))
    with pytest.raises(ValueError, match="no visible alpha"):
        roi.analyze_isolated(Image.new("RGBA", (80, 100)))
    with pytest.raises(FileNotFoundError):
        roi.native_evidence(tmp_path, tmp_path / "out", radius=0)
    with pytest.raises(ValueError, match="bounded"):
        roi.native_evidence(tmp_path, tmp_path / "out", radius=9)


def test_geometry_validates_binary_mask_and_safe_margin(roi):
    with pytest.raises(ValueError, match="binary mask"):
        roi.geometry(np.zeros((5, 5), dtype=np.uint8))
    with pytest.raises(ValueError, match="margin"):
        roi.geometry(np.zeros((5, 5), dtype=bool), margin_fraction=0.9)
    mask = np.zeros((100, 80), dtype=bool)
    mask[30:76, 20:61] = True
    geo = roi.geometry(mask)
    assert geo["bbox"] == [20, 30, 60, 75]
    assert geo["outside_safe_zone"] is False


def test_record_stream_keeps_held_frame_and_strict_sequential_indices(roi):
    size = (1080, 1920)
    isolated = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(isolated).rectangle((300, 400, 700, 1200), fill=(32, 115, 170, 255))
    frame = Image.new("RGB", size, "#fff8eb")
    result = roi.record_frames(
        [(59, isolated, frame), (60, isolated.copy(), frame.copy())], size=size
    )
    assert result["resolution"] == [1080, 1920]
    assert result["frames"][1]["composite_alpha_iou_from_previous"] == 1
    assert (
        result["frames"][0]["sha256_rgb_pixels"]
        == result["frames"][1]["sha256_rgb_pixels"]
    )
    with pytest.raises(ValueError, match="consecutive"):
        roi.record_frames([(59, isolated, frame), (61, isolated, frame)], size=size)
    with pytest.raises(ValueError, match="RGBA"):
        roi.record_frames([(60, frame, frame)], size=size)
    with pytest.raises(ValueError, match="RGB"):
        roi.record_frames([(60, isolated, isolated)], size=size)
    with pytest.raises(ValueError, match="no native garment"):
        roi.record_frames([], size=size)
    with pytest.raises(ValueError, match="30 fps"):
        roi.record_frames([(60, isolated, frame)], size=size, fps=29)
