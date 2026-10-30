"""C01 A02 30fps evidence contract: synthetic fixtures, not creator G10 approval."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def qa(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "science_art_temporal_qa", ROOT / "scripts/verify_science_art.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def isolated(size=(80, 80), bbox=(20, 20, 60, 60)):
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle(bbox, fill=(30, 120, 200, 255))
    return image


def cutouts(root: Path, *, shifted=False):
    for name, color in (("wet", (20, 70, 130, 255)), ("dry", (120, 180, 220, 255))):
        image = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
        left = 85 if shifted and name == "dry" else 60
        ImageDraw.Draw(image).rectangle((left, 40, left + 190, 270), fill=color)
        image.save(root / f"{name}.png")


def test_window_is_30fps_bounded_and_includes_both_transition_sides(qa):
    assert qa.temporal_window() == list(range(57, 64))
    assert qa.temporal_window(center_frame=0) == [0, 1, 2, 3]
    assert qa.temporal_window(center_frame=119) == [116, 117, 118, 119]
    assert [round(i / 30, 6) for i in qa.temporal_window()][3] == 2.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"fps": 24},
        {"duration_seconds": 0},
        {"duration_seconds": float("nan")},
        {"center_frame": -1},
        {"center_frame": 120},
        {"radius_frames": -1},
    ],
)
def test_window_rejects_invalid_fps_or_out_of_range_frames(qa, kwargs):
    with pytest.raises(ValueError):
        qa.temporal_window(**kwargs)


def test_missing_corrupt_or_different_real_asset_alpha_fails_closed(qa, tmp_path):
    with pytest.raises(FileNotFoundError):
        qa.validate_assets(tmp_path)
    cutouts(tmp_path)
    assert qa.validate_assets(tmp_path)["alpha_iou"] == 1.0
    Image.new("RGB", (320, 320), "blue").save(tmp_path / "dry.png")
    with pytest.raises(ValueError, match="RGBA"):
        qa.validate_assets(tmp_path)
    cutouts(tmp_path, shifted=True)
    with pytest.raises(ValueError, match="alpha mismatch"):
        qa.validate_assets(tmp_path)


def test_mask_geometry_catches_empty_crop_and_safe_zone(qa):
    with pytest.raises(ValueError, match="RGBA"):
        qa.mask_geometry(Image.new("RGB", (80, 80)))
    with pytest.raises(ValueError, match="no visible"):
        qa.mask_geometry(Image.new("RGBA", (80, 80)))
    with pytest.raises(ValueError, match="cropped"):
        qa.mask_geometry(isolated(bbox=(0, 20, 40, 60)))
    with pytest.raises(ValueError, match="safe zone"):
        qa.mask_geometry(
            isolated(bbox=(3, 20, 40, 60)),
            margin_fraction=0.1,
            strict_safe_zone=True,
        )
    metrics = qa.mask_geometry(isolated(), strict_safe_zone=True, peg_row=25)
    assert metrics["bbox"] == [20, 20, 60, 60]
    assert metrics["peg_pixels"] > 0
    assert metrics["safe_zone_ok"]


def test_held_frame_is_not_a_false_discontinuity_and_digests_are_stable(qa):
    rgb = Image.new("RGB", (80, 80), "white")
    mask = isolated()
    result = qa.record_temporal_sequence(
        [(59, rgb, mask), (60, rgb.copy(), mask.copy())], peg_row=25
    )
    assert result["fps"] == 30
    assert result["resolution"] == [80, 80]
    assert result["frames"][1]["mean_rgb_delta_from_previous"] == 0
    assert result["frames"][1]["alpha_iou_from_previous"] == 1
    assert result["frames"][0]["sha256_rgb_pixels"] == result["frames"][1]["sha256_rgb_pixels"]
    assert result["frames"][1]["peg_shift_from_first_px"] == 0


def test_sequence_rejects_zero_frames_bad_dimensions_and_skipped_indices(qa):
    with pytest.raises(ValueError, match="no temporal frames"):
        qa.record_temporal_sequence([])
    rgb = Image.new("RGB", (80, 80), "white")
    mask = isolated()
    with pytest.raises(ValueError, match="dimensions"):
        qa.record_temporal_sequence([(0, rgb, isolated(size=(81, 80)))])
    with pytest.raises(ValueError, match="consecutive"):
        qa.record_temporal_sequence([(0, rgb, mask), (2, rgb, mask)])
    with pytest.raises(ValueError, match="30 fps"):
        qa.record_temporal_sequence([(0, rgb, mask)], fps=25)


@pytest.mark.parametrize("size", [(1080, 1920), (1920, 1080)])
def test_fullhd_frame_metrics_preserve_actual_aspect_and_sample_hash(qa, tmp_path, size):
    width, height = size
    frame = Image.new("RGB", size, "white")
    alpha = isolated(size, (width // 4, height // 4, width // 2, height // 2))
    result = qa.record_temporal_sequence(
        [(60, frame, alpha)],
        strict_safe_zone=True,
        output_dir=tmp_path,
        sample_indices=frozenset({60}),
        sample_prefix="fullhd",
    )
    record = result["frames"][0]
    assert result["resolution"] == [width, height]
    assert record["seconds"] == 2.0
    assert len(record["sha256_rgb_pixels"]) == 64
    assert len(record["sha256_alpha_pixels"]) == 64
    assert (tmp_path / record["sample_file"]).exists()
    assert record["sample_sha256"]
    assert result["stored_sample_bytes"] > 0


def test_preview_end_to_end_keeps_five_templates_and_two_aspects(qa, tmp_path):
    art_dir = tmp_path / "assets"
    art_dir.mkdir()
    cutouts(art_dir)
    report = qa.temporal_evidence(
        art_dir, tmp_path / "output", radius_frames=1, native_fullhd=False
    )
    assert report["frame_indices"] == [59, 60, 61]
    assert report["creator_g10"] == "PENDING"
    assert report["native_fullhd_spread"] == {}
    for label, resolution in (("portrait", [270, 480]), ("landscape", [480, 270])):
        group = report["preview"][label]
        assert (tmp_path / "output" / group["sheet"]).exists()
        assert set(group["kinds"]) == {"shirt", "warm", "wind", "spread", "dry"}
        for kind in group["kinds"].values():
            assert kind["resolution"] == resolution
            assert [frame["frame_index"] for frame in kind["frames"]] == [59, 60, 61]
            assert all(frame["geometry"]["opaque_pixels"] > 0 for frame in kind["frames"])


def test_budget_rejects_unbounded_frame_windows(qa, tmp_path):
    with pytest.raises(ValueError, match="bounded"):
        qa.temporal_evidence(tmp_path, tmp_path, radius_frames=300)
