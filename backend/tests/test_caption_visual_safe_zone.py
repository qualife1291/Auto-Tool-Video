"""Regression for captions covering imported illustration content (#103)."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image, ImageDraw

from auto_tool_video.render import ScenePainter


@pytest.mark.parametrize("size", [(360, 640), (640, 360), (1080, 1920), (1920, 1080)])
def test_contained_full_frame_art_reserves_caption_band(tmp_path, size):
    path = tmp_path / "illustration.png"
    source = Image.new("RGB", (1400, 1000), "#FFF8EB")
    ImageDraw.Draw(source).rectangle((20, 700, 1380, 999), fill="#0A4F99")
    source.save(path)
    scene = {
        "title": "Nước bay hơi",
        "narration": "Hơi nước tạo thành mây.",
        "duration": 3,
        "style": "motion",
        "layout": "full_frame",
        "visual_fit": "contain",
        "caption_style": "contrast",
    }
    painter = ScenePainter(path, scene, *size, True)
    try:
        _x, y, _w, h = painter.image_box
        _cx, caption_y, _cw, caption_h = painter.caption_box
        assert y + h <= caption_y - 24
        frame = np.asarray(painter.frame(1.0, overlays=False))
        top = round(caption_y * painter.scale)
        bottom = round((caption_y + caption_h) * painter.scale)
        assert np.all(frame[top:bottom] == (255, 248, 235))
    finally:
        painter.close()


@pytest.mark.parametrize(
    "fit,captions,narration",
    [
        ("cover", True, "Lời đọc"),
        ("contain", False, "Lời đọc"),
        ("contain", True, ""),
    ],
)
def test_full_frame_unrestricted_when_no_contained_caption(fit, captions, narration, tmp_path):
    path = tmp_path / "illustration.png"
    Image.new("RGB", (400, 400), "#0A4F99").save(path)
    scene = {
        "title": "Hình toàn khung",
        "narration": narration,
        "duration": 3,
        "style": "motion",
        "layout": "full_frame",
        "visual_fit": fit,
    }
    painter = ScenePainter(path, scene, 640, 360, captions)
    try:
        assert painter.image_box == (0, 0, 1920, 1080)
    finally:
        painter.close()
