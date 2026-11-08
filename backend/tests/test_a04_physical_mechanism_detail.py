"""P0: physical mechanism closeups replace generic inset icons in A04 source art.

A04 is an engineering image fixture, not approved Comfy imagery or creator G10.
These pixel assertions protect scene differentiation, color/depth and final PNG use.
"""

from __future__ import annotations

import hashlib
import io
import sys
from itertools import combinations
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageFilter, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))


MECHANISM_TITLES = (
    "Nước bay hơi",
    "Không khí",
    "Gió",
    "Ánh nắng",
    "Bóng râm",
    "Quan sát",
)


def test_all_six_mechanisms_are_specific_original_drawings():
    from qa_physical_mechanisms import MECHANISM_CUES, render_mechanism_detail

    assert tuple(MECHANISM_CUES) == MECHANISM_TITLES
    hashes: set[str] = set()
    rendered = []
    for title in MECHANISM_TITLES:
        image = render_mechanism_detail(title)
        assert image.mode == "RGB" and image.size == (310, 265)
        assert ImageStat.Stat(image.convert("L")).stddev[0] > 15
        # Must have fine pictorial strokes, not an empty color-only card.
        edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
        assert ImageStat.Stat(edges).mean[0] > 5
        hashes.add(hashlib.sha256(image.tobytes()).hexdigest())
        rendered.append(image)
    assert len(hashes) == len(MECHANISM_TITLES)
    for a, b in combinations(rendered, 2):
        assert ImageStat.Stat(ImageChops.difference(a, b)).mean[0] > 5


def test_unknown_mechanism_cannot_be_passed_off_as_original_art():
    from qa_physical_mechanisms import render_mechanism_detail

    with pytest.raises(ValueError, match="No authored physical detail"):
        render_mechanism_detail("Không có cảnh này")


@pytest.mark.parametrize("title", MECHANISM_TITLES)
def test_portrait_source_uses_mechanism_closeup_not_old_icon_crop(title):
    from qa_physical_mechanisms import render_mechanism_detail
    from qa_voice_review_art import render_portrait_cue_art

    image = Image.open(io.BytesIO(render_portrait_cue_art(title))).convert("RGB")
    # Larger macro note must be legible at the actual 360px phone output;
    # other cues keep their old note box and the creator caption is unaffected.
    original_detail = render_mechanism_detail(title).resize((395, 337), Image.Resampling.LANCZOS)
    actual = image.crop((492, 941, 887, 1278))
    assert ImageChops.difference(actual, original_detail).getbbox() is None
    phone_width = original_detail.width * (1376 / 1600) * (360 / 1080)
    assert phone_width >= 110
    # Existing shirt/physical stage stays safely in-frame.
    assert ImageStat.Stat(image.crop((290, 410, 780, 855))).stddev[0] > 20
