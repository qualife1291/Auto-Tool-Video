"""Regression for actual A04 portrait framing and draw-in dwell time.

This guards layout geometry and source pixels, NOT AI image quality or creator G10.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from auto_tool_video.layout import boxes

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from qa_voice_review_art import render_portrait_cue_art
from voice_wav_acceptance import make_review_scene


@pytest.mark.parametrize("width,height", [(360, 640), (1080, 1920)])
def test_portrait_full_frame_uses_canvas_without_relocating_board_caption(width, height):
    full = boxes(width, height, "full_frame")
    board = boxes(width, height, "board")
    cy = full["caption"][1]
    assert cy >= round(height * 0.82)
    assert cy + full["caption"][3] <= height - round(height * 0.04)
    assert board["caption"][1] == round(1335 * width / 1080)
    assert board["image"][1] == round(420 * width / 1080)


def test_portrait_foreground_yard_fills_lower_source_without_plain_blank_strip():
    image = Image.open(io.BytesIO(render_portrait_cue_art("Nước bay hơi"))).convert("RGB")
    assert image.size == (1000, 1600)
    lower = np.asarray(image.crop((130, 1390, 870, 1550)), dtype=np.int16)
    base = np.array((255, 249, 237))
    close_to_blank = np.max(np.abs(lower - base), axis=2) <= 10
    assert float(close_to_blank.mean()) < 0.35
    # Distinct foreground detail, not an opaque flat rectangle merely hiding blank space.
    assert float(lower.std(axis=(0, 1)).mean()) > 11


def test_short_a04_cue_finishes_reveal_early_to_show_completed_image():
    scene = make_review_scene(
        {"title": "Nước bay hơi", "narration": "Nước trong vải bay hơi.", "duration": 2.0}
    )
    assert 0.30 <= scene.draw_fraction <= 0.36
    assert scene.duration * (1 - scene.draw_fraction - 0.12) >= 1.0
