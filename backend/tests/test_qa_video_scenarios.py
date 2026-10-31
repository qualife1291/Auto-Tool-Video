"""Fast contracts for varied Vietnamese video scenarios; no fake render pass."""

from __future__ import annotations

import importlib.util
import io
import sys
from itertools import pairwise
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageStat
from pydantic import ValidationError

from auto_tool_video.domain import Scene
from auto_tool_video.timing import frames_for

ROOT = Path(__file__).resolve().parents[2]
# Importlib does not automatically put the directly executable scripts directory on sys.path.
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "qa_video_scenarios", ROOT / "scripts/qa_video_scenarios.py"
)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


@pytest.mark.parametrize(
    "key,count,seconds",
    [
        ("water-12s", 4, 12),
        ("shirt-30s", 6, 30),
        ("traffic-45s", 9, 45),
        ("energy-60s", 12, 60),
    ],
)
def test_four_narrative_cases_have_valid_distinct_cues(key, count, seconds):
    case = module.SCENARIOS[key]
    module.validate_scenario(case)
    assert len(case.cues) == count
    assert case.seconds == seconds
    assert len({spoken for _, spoken in case.cues}) == count
    assert sum(frames_for(case.scene_seconds) for _ in case.cues) == seconds * 30
    for title, spoken in case.cues:
        beat_list = module.beats(case.scene_seconds, spoken)
        scene = Scene(
            title=title,
            narration=spoken,
            duration=case.scene_seconds,
            second_by_second=beat_list,
            beat_plan_status="authored",
        )
        assert scene.beat_plan_status == "authored"
        assert beat_list[-1]["second"] == case.scene_seconds - 1


def test_content_covers_diacritics_and_multiple_topics():
    cases = module.SCENARIOS
    assert len({case.title for case in cases.values()}) == len(cases)
    assert "ướt" in cases["shirt-30s"].title
    assert "đường" in cases["traffic-45s"].title
    assert "năng lượng" in cases["energy-60s"].title


@pytest.mark.parametrize(
    "count,scene_seconds",
    [(3, 21), (13, 5), (20, 4), (21, 1), (1, 0), (1, -1)],
)
def test_invalid_story_and_scene_boundaries_fail_closed(count, scene_seconds):
    template = module.SCENARIOS["energy-60s"]
    case = module.Scenario(
        "invalid",
        "Wrong contract",
        scene_seconds,
        (template.cues * 2)[:count],
    )
    with pytest.raises(ValueError):
        module.validate_scenario(case)


@pytest.mark.parametrize("seconds", [0, -1, 21])
def test_studio_model_rejects_invalid_scene_duration(seconds):
    with pytest.raises(ValidationError):
        Scene(title="Scene invalid", duration=seconds)


def test_60s_accepted_but_61s_rejected():
    permitted = module.SCENARIOS["energy-60s"]
    module.validate_scenario(permitted)
    over = module.Scenario(
        "over-limit",
        "65 seconds",
        5,
        permitted.cues + permitted.cues[:1],
    )
    with pytest.raises(ValueError):
        module.validate_scenario(over)


def test_original_visual_assets_differ_scene_by_scene():
    case = module.SCENARIOS["water-12s"]
    a = module.visual(0, case)
    b = module.visual(1, case)
    assert a.startswith(bytes.fromhex("89504e47"))
    assert b.startswith(bytes.fromhex("89504e47"))
    assert a != b

@pytest.mark.parametrize("key", sorted(module.SCENARIOS))
def test_every_cue_has_intentional_scene_specific_art(key):
    case = module.SCENARIOS[key]
    expected = module.EXPECTED_OBJECTS[key]
    assert set(expected) == {title for title, _narration in case.cues}
    images = []
    for i, (title, _narration) in enumerate(case.cues):
        assert expected[title], f"{key}/{title} has no object intent"
        source = module.visual(i, case)
        with Image.open(io.BytesIO(source)) as image:
            assert image.format == "PNG"
            assert image.size == (1400, 1000)
            images.append(image.convert("L").resize((140, 100)))
    # The existing negative fixtures reused near-identical outlines for every cue.
    # This is a visual-content guard, NOT human semantic understanding or G10 approval.
    differences = [
        ImageStat.Stat(ImageChops.difference(a, b)).mean[0]
        for a, b in pairwise(images)
    ]
    assert differences and min(differences) >= 0.4, (key, differences)


def test_semantic_art_fails_closed_instead_of_reusing_generic_topic_icon():
    case = module.SCENARIOS["traffic-45s"]
    with pytest.raises(ValueError, match="out of range"):
        module.visual(len(case.cues), case)
    with pytest.raises(ValueError, match="out of range"):
        module.visual(-1, case)
    with pytest.raises(ValueError, match="Unknown semantic"):
        module.semantic_visual(case.key, "Mặt trăng")


def test_shirt_continuity_keeps_shirt_but_changes_wet_dry_state():
    expected = module.EXPECTED_OBJECTS["shirt-30s"]
    assert "shirt" in expected["Áo ướt"]
    assert "shirt" in expected["Áo khô"]
    assert "water_drops" in expected["Áo ướt"]
    assert "dry_state" in expected["Áo khô"]
    assert module.semantic_visual("shirt-30s", "Áo ướt") != module.semantic_visual(
        "shirt-30s", "Áo khô"
    )

