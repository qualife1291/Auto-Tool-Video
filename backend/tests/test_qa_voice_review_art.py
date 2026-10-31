"""Regression: A04 scene actions must not collapse into color-shifted identical shapes."""

from __future__ import annotations

import hashlib
import inspect
import io
import sys
from itertools import combinations
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from qa_voice_review_art import VISUAL_INTENTS, render_cue_art  # noqa: E402
from voice_wav_acceptance import CUES, render_aspect  # noqa: E402


def test_cue_specific_art_is_bound_to_real_a04_story():
    titles = tuple(title for title, _ in CUES)
    assert titles == tuple(VISUAL_INTENTS)
    assert all(len(objects) >= 2 for objects in VISUAL_INTENTS.values())
    source = inspect.getsource(render_aspect)
    assert "render_cue_art(title)" in source
    assert "illustration_records" in source
    assert "draw.rectangle(" not in source


def test_every_cue_outputs_real_png_with_unique_art():
    digests = set()
    for title, _ in CUES:
        data = render_cue_art(title)
        digests.add(hashlib.sha256(data).hexdigest())
        with Image.open(io.BytesIO(data)) as image:
            assert image.format == "PNG"
            assert image.size == (1400, 1000)
            assert image.getbbox() is not None
    assert len(digests) == len(CUES)


def test_context_geometry_changes_not_merely_palette():
    edges = []
    for title, _ in CUES:
        frame = Image.open(io.BytesIO(render_cue_art(title))).convert("L")
        edges.append(frame.crop((900, 270, 1250, 785)).filter(ImageFilter.FIND_EDGES))
    # Edge images are insensitive to palette-only changes in filled areas;
    # the previous A04 ellipse/rectangle fixture would fail this contract.
    for (i, left), (j, right) in combinations(enumerate(edges), 2):
        difference = ImageChops.difference(left, right)
        assert ImageStat.Stat(difference).mean[0] > 1.0, (
            CUES[i][0],
            CUES[j][0],
        )


def test_intentional_shirt_continuity_with_distinct_wet_dry_stages():
    wet = Image.open(io.BytesIO(render_cue_art("Câu hỏi"))).convert("RGB")
    dry = Image.open(io.BytesIO(render_cue_art("Tổng kết"))).convert("RGB")
    assert wet.size == dry.size
    assert wet.getpixel((500, 650)) != dry.getpixel((500, 650))
    assert ImageChops.difference(wet, dry).getbbox() is not None


def test_unknown_story_cue_fails_closed():
    with pytest.raises(ValueError, match="No authored visual semantics"):
        render_cue_art("Không có trong kịch bản")
