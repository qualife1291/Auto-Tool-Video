"""Regression: whiteboard painted phase must not expose a bright seam."""

import numpy as np
import pytest
from PIL import Image, ImageDraw

from auto_tool_video.paper import PAPER_RGB, normalize_paper
from auto_tool_video.render import ScenePainter


@pytest.mark.parametrize("background", [(255, 253, 245), (255, 255, 255)])
@pytest.mark.parametrize("fit", ["cover", "contain"])
def test_bright_image_border_matches_paper_at_final_frame(tmp_path, background, fit):
    source = Image.new("RGB", (400, 320), background)
    ImageDraw.Draw(source).rectangle((145, 105, 255, 215), fill=(183, 221, 224))
    path = tmp_path / "diagram.png"
    source.save(path)
    painter = ScenePainter(
        path,
        {
            "title": "Một cảnh",
            "narration": "",
            "duration": 1,
            "layout": "full_frame",
            "visual_fit": fit,
            "style": "whiteboard",
        },
        360,
        640,
        False,
    )
    try:
        frame = painter.frame(1.0, overlays=False)
        for x, y in [(5, 5), (355, 635)]:
            assert max(abs(a - b) for a, b in zip(frame.getpixel((x, y)), PAPER_RGB)) <= 2
    finally:
        painter.close()


def test_subject_color_remains_perceptually_unchanged():
    source = Image.new("RGB", (240, 180), (255, 253, 245))
    ImageDraw.Draw(source).rectangle((50, 40, 190, 140), fill=(183, 221, 224))
    result = normalize_paper(source)
    assert result.getpixel((0, 0)) == PAPER_RGB
    assert max(abs(a - b) for a, b in zip(result.getpixel((100, 90)), (183, 221, 224))) <= 8


def test_non_whiteboard_photographic_and_dark_borders_are_untouched():
    dark = Image.new("RGB", (100, 100), (20, 20, 30))
    noisy = Image.fromarray(
        np.random.default_rng(42).integers(0, 255, (100, 100, 3), dtype=np.uint8)
    )
    for source in (dark, noisy):
        assert np.array_equal(np.asarray(normalize_paper(source)), np.asarray(source))


def test_clip_frames_do_not_get_paper_recolor(monkeypatch, tmp_path):
    import cv2

    class Capture:
        def read(self):
            return True, np.full((100, 100, 3), 255, dtype=np.uint8)

        def get(self, _key):
            return 30

        def release(self):
            pass

    monkeypatch.setattr(cv2, "VideoCapture", lambda _path: Capture())
    painter = ScenePainter(
        tmp_path / "video.mp4",
        {"title": "Clip", "narration": "", "duration": 1},
        360,
        640,
        False,
        is_clip=True,
    )
    try:
        assert painter.source_image.getpixel((0, 0)) == (255, 255, 255)
    finally:
        painter.close()
