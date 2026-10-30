"""Focused A03 acceptance: subtitles move briefly on entry, then stay still."""

import numpy as np
import pytest
from PIL import Image

from auto_tool_video.render import ScenePainter


@pytest.mark.parametrize("size", [(360, 640), (640, 360)])
@pytest.mark.parametrize("caption_style", ["card", "contrast", "accent"])
def test_caption_bounce_only_on_entry_and_then_remains_pixel_stable(
    tmp_path, size, caption_style
):
    source = tmp_path / "plain.png"
    Image.new("RGB", (64, 64), "#FFF8EB").save(source)
    scene = {
        "title": "Bay hơi",
        "narration": "Nước bay hơi.",
        "duration": 4,
        "style": "motion",
        "caption_style": caption_style,
        "caption_emphasis": "bay hơi",
    }
    painter = ScenePainter(source, scene, *size, True)
    try:
        assert len(painter.pages) == 1

        def overlay_at(seconds):
            image = painter.base.copy()
            painter.draw_caption(image, seconds / scene["duration"])
            return np.asarray(image)

        # Caption card and all glyphs translate together during the initial bounce.
        assert not np.array_equal(overlay_at(0), overlay_at(0.12))
        # After 0.26 s nothing in this caption page moves or flickers.
        hold = overlay_at(0.35)
        assert np.array_equal(hold, overlay_at(0.65))
        assert np.array_equal(hold, overlay_at(1.2))
    finally:
        painter.close()
