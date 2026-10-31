"""Full-frame contain motion must preserve source edges at every export aspect.

A 2.5% end-of-scene zoom used to crop the outermost illustration pixels even
when visual_fit='contain' explicitly promised to retain the complete artwork.
"""

from __future__ import annotations

import pytest
from PIL import Image, ImageDraw

from auto_tool_video.render import ScenePainter


@pytest.mark.parametrize("size", [(360, 640), (640, 360)])
@pytest.mark.parametrize("fit,edge_visible", [("contain", True), ("cover", False)])
def test_full_frame_motion_preserves_contain_edges_but_keeps_cover_zoom(
    tmp_path, size, fit, edge_visible
):
    width, height = size
    border = (5, 15, 25)
    source = Image.new("RGB", size, "#CC9933")
    ImageDraw.Draw(source).rectangle(
        (0, 0, width - 1, height - 1), outline=border, width=4
    )
    path = tmp_path / "edge-markers.png"
    source.save(path)
    scene = {
        "title": "Hình minh họa đủ bốn cạnh",
        "narration": "",
        "duration": 3,
        "style": "motion",
        "layout": "full_frame",
        "visual_fit": fit,
    }
    painter = ScenePainter(path, scene, width, height, captions=False)
    try:
        final = painter.frame(1.0, overlays=False)
        samples = [
            final.getpixel((0, height // 2)),
            final.getpixel((width - 1, height // 2)),
            final.getpixel((width // 2, 0)),
            final.getpixel((width // 2, height - 1)),
        ]
        assert all((pixel == border) == edge_visible for pixel in samples)
    finally:
        painter.close()
