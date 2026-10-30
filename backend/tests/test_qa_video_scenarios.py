"""Fast contracts for varied Vietnamese video scenarios; no fake render pass."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from auto_tool_video.domain import Scene
from auto_tool_video.timing import frames_for

ROOT = Path(__file__).resolve().parents[2]
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
            title=title, narration=spoken, duration=case.scene_seconds,
            second_by_second=beat_list, beat_plan_status="authored",
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
        "invalid", "Wrong contract", scene_seconds,
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
        "over-limit", "65 seconds", 5,
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
