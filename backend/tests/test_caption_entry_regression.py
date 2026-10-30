"""Focused A03 acceptance: subtitles move briefly on entry, then stay still."""

import numpy as np
import pytest
from PIL import Image

from auto_tool_video.render import ScenePainter


@pytest.mark.parametrize("size", [(360, 640), (640, 360)])
@pytest.mark.parametrize("caption_style", ["card", "contrast", "accent"])
def test_caption_bounce_only_on_entry_and_then_remains_pixel_stable(tmp_path, size, caption_style):
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


@pytest.mark.parametrize("size", [(360, 640), (640, 360)])
@pytest.mark.parametrize("caption_style", ["card", "contrast", "accent"])
def test_each_caption_page_bounces_on_entry_then_stays_still(tmp_path, size, caption_style):
    """A cue-page change is not a continuous pulse throughout the scene."""
    source = tmp_path / "blank.png"
    Image.new("RGB", (64, 64), "#FFF8EB").save(source)
    scene = {
        "title": "Nước bay hơi",
        "narration": (
            "Áo ướt còn nhiều nước, nước bay hơi và đi vào không khí. "
            "Gió làm áo khô dần nhưng không làm nước biến mất. "
            "Chúng mình quan sát xem áo thay đổi ra sao nhé."
        ),
        "duration": 12,
        "style": "motion",
        "caption_style": caption_style,
        "caption_emphasis": "bay hơi",
    }
    painter = ScenePainter(source, scene, *size, True)
    try:
        assert len(painter.pages) >= 2
        page_seconds = scene["duration"] / len(painter.pages)
        assert page_seconds > 0.75

        def overlay_at(seconds):
            image = painter.base.copy()
            painter.draw_caption(image, seconds / scene["duration"])
            return np.asarray(image)

        # The second page animates afresh at its own cue, not only at scene start.
        assert not np.array_equal(overlay_at(page_seconds + 0.01), overlay_at(page_seconds + 0.12))
        # Once the 0.26s entry ends, the entire card and Vietnamese glyphs are stable.
        hold = overlay_at(page_seconds + 0.35)
        assert np.array_equal(hold, overlay_at(page_seconds + 0.65))
    finally:
        painter.close()
