"""Regression: A04 scene actions must not collapse into color-shifted identical shapes."""

from __future__ import annotations

import hashlib
import inspect
import io
import sys
from itertools import combinations
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from qa_voice_review_art import VISUAL_INTENTS, render_cue_art, render_portrait_cue_art
from voice_wav_acceptance import CUES, make_review_scene, render_aspect


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


def test_a04_portrait_fit_preserves_full_subject_and_context():
    # RED from actual PR #115 MP4: source landscape art covered 9:16,
    # cropping half the shirt and eliminating distinct context in the export.
    source = inspect.getsource(render_aspect)
    assert "make_review_scene(s).model_dump()" in source
    sample = {"title": "Áo ướt", "narration": "Nước bay hơi.", "duration": 2}
    assert make_review_scene(sample).visual_fit == "contain"
    assert "render_portrait_cue_art(title)" in source
    assert 'if aspect == "portrait"' in source
    portrait_hashes = set()
    for title, _ in CUES:
        with Image.open(io.BytesIO(render_portrait_cue_art(title))) as portrait:
            assert portrait.size == (1000, 1600)
            assert portrait.format == "PNG"
            portrait_hashes.add(hashlib.sha256(portrait.tobytes()).hexdigest())
            # Both cards retain drawn pixels and remain inside the final 9:16
            # safe region, leaving Studio heading and caption locations free.
            assert ImageStat.Stat(portrait.crop((170, 275, 830, 745))).stddev[0] > 15
            assert ImageStat.Stat(portrait.crop((175, 800, 825, 1110))).stddev[0] > 7
    assert len(portrait_hashes) == len(CUES)


def test_a04_source_art_has_cohesive_yard_depth_and_fabric_stitching():
    # The actual previous A04 MP4 showed tiny two-card pictograms surrounded
    # by blank cream. Require a physical yard, clothing texture and cue context.
    landscape = Image.open(io.BytesIO(render_cue_art("Nước bay hơi"))).convert("RGB")
    portrait = Image.open(io.BytesIO(render_portrait_cue_art("Nước bay hơi"))).convert("RGB")
    from qa_rich_context_art import garment_detail

    assert landscape.getpixel((245, 485)) != landscape.getpixel((70, 485))
    assert portrait.getpixel((125, 650)) != portrait.getpixel((35, 650))
    # New native portrait art reaches beyond the old top-card and bottom-card
    # with visible yard/fence detail, rather than leaving 70% cream.
    top = portrait.crop((120, 275, 880, 810))
    lower = portrait.crop((120, 880, 880, 1310))
    assert ImageStat.Stat(top).stddev[0] > 18
    assert ImageStat.Stat(lower).stddev[0] > 16

    plain = Image.new("RGB", (1400, 1000), "#FFF9ED")
    detailed = plain.copy()
    from qa_voice_review_art import _shirt

    _shirt(ImageDraw.Draw(plain), wet=3)
    pen = ImageDraw.Draw(detailed)
    _shirt(pen, wet=3)
    garment_detail(pen, origin=(325, 275), scale=1, wet=3, spread=False)
    difference = ImageChops.difference(plain, detailed)
    assert ImageStat.Stat(difference.crop((425, 380, 755, 788))).mean[0] > 1.0
