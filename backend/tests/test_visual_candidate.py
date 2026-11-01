"""Candidate visuals: real pixel evidence and advisory-only review gates."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image, ImageDraw

from auto_tool_video.domain import CreativeBrief
from auto_tool_video.visual_candidate import POLICY, inspect_candidate_visual


def test_blank_candidate_is_not_mistaken_for_a_descriptive_image():
    result = inspect_candidate_visual(Image.new("RGB", (768, 1344), "white"))
    assert result["policy"] == POLICY
    assert result["width"] == 768 and result["height"] == 1344
    assert [w["code"] for w in result["warnings"]] == ["nearly_no_structure"]
    assert result["edge_fraction"] == 0
    assert result["semantic_review"] == result["aesthetic_review"] == "not_performed"
    assert result["human_approval"] == "pending"


def test_small_primitive_with_empty_background_requests_visual_review():
    image = Image.new("RGB", (1400, 1000), "#fff9ed")
    draw = ImageDraw.Draw(image)
    draw.ellipse((655, 455, 745, 545), fill="#478eaa", outline="black", width=4)
    result = inspect_candidate_visual(image)
    assert result["warnings"]
    assert result["warnings"][0]["code"] in ("sparse_simple_art", "nearly_no_structure")
    assert result["occupied_tile_fraction"] < 0.24


def test_rich_full_canvas_context_does_not_raise_sparse_art_warning():
    rng = np.random.default_rng(20261101)
    values = rng.integers(0, 256, size=(192, 192, 3), dtype=np.uint8)
    image = Image.fromarray(values, mode="RGB")
    result = inspect_candidate_visual(image)
    assert result["edge_fraction"] > 0.004
    assert result["occupied_tile_fraction"] > 0.24
    assert result["warnings"] == []
    # This is only a structural test, NOT a claim random noise is good illustration.
    assert result["aesthetic_review"] == "not_performed"


def test_deterministic_analysis_and_no_mutation():
    image = Image.new("RGB", (1024, 1792), "#ddeeff")
    draw = ImageDraw.Draw(image)
    for index in range(20):
        draw.line((25, index * 65 + 30, 995, index * 65 + 130), fill="navy", width=4)
    raw = image.tobytes()
    a = inspect_candidate_visual(image)
    b = inspect_candidate_visual(image)
    assert a == b
    assert image.tobytes() == raw


@pytest.mark.parametrize("size", [(0, 100), (100, 0)])
def test_empty_image_rejected(size):
    with pytest.raises(ValueError):
        inspect_candidate_visual(Image.new("RGB", size))



def test_new_story_uses_layered_art_direction_without_overwriting_legacy_projects():
    style = CreativeBrief().style_bible
    assert "nhiều lớp" in style
    assert "chủ thể chính lớn" in style
    assert "chất liệu" in style
    assert "không chữ/logo" in style
    old = CreativeBrief(style_bible="Nét đen sạch, ít màu, nền kem")
    assert old.style_bible == "Nét đen sạch, ít màu, nền kem"
