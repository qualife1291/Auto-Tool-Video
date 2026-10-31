"""C02 PPL-01: frozen offline Vietnamese storyboard oracle; no live model calls.

Fixture oracles are authored independently of the production validator. This
suite checks structural contracts only, not generated-art/video quality.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from auto_tool_video.domain import ProjectInput
from auto_tool_video.planning import validate_proposal
from auto_tool_video.store import DomainError

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "storyboard_eval_cases.json"
FIXTURE_BYTES = FIXTURE_PATH.read_bytes()
SUITE = json.loads(FIXTURE_BYTES)


def test_frozen_fixture_metadata_and_pairwise_coverage():
    """Keep scenario counts and independently covered axes visible to QA."""
    assert SUITE["schema_version"] == 1
    assert SUITE["seed"] == 20261031
    cases = SUITE["cases"]
    assert len(cases) == 40
    assert len({case["case_id"] for case in cases}) == 40
    assert len([c for c in cases if c["category"] == "positive"]) == 20
    assert len([c for c in cases if c["category"] == "negative"]) == 20
    assert {c["profile"] for c in cases} == {
        "preschool", "kids", "older_kids", "family", "general"
    }
    assert {c["aspect"] for c in cases} == {"portrait", "landscape"}
    assert {c["mode"] for c in cases} == {"brief", "preserve"}
    assert {c["target_duration"] for c in cases} == {30, 45, 60}
    assert {c["case_id"] for c in cases} == {
        *(f"P{i:02d}" for i in range(1, 21)),
        *(f"N{i:02d}" for i in range(1, 21)),
    }
    assert all(c["source_provenance"] == SUITE["source_provenance"] for c in cases)
    digest = hashlib.sha256(FIXTURE_BYTES).hexdigest()
    assert len(digest) == 64
    print(f"STORYBOARD_EVAL_FIXTURE_SHA256={digest}")


@pytest.mark.parametrize("case", SUITE["cases"], ids=lambda case: case["case_id"])
def test_offline_structural_oracle(case):
    """Validate REAL production contracts, not just JSON self-consistency."""
    expected = case["expected"]
    original_input = copy.deepcopy(case["project"])
    assert case["profile"] == original_input["profile"]
    assert case["aspect"] == original_input["aspect"]
    if case["case_id"] == "N18":
        assert original_input["brief"]["target_duration"] == 12
    else:
        assert case["target_duration"] == original_input["brief"]["target_duration"]
    assert case["mode"] in {"brief", "preserve"}

    if expected["validator"] == "ProjectInput.model_validate":
        assert expected["result"] == "invalid"
        assert expected["error_code"] == "ValidationError"
        with pytest.raises(ValidationError):
            ProjectInput.model_validate(original_input)
        assert case["project"] == original_input
        return

    project = ProjectInput.model_validate(original_input).model_dump()
    before = copy.deepcopy(project)
    raw = case.get("raw_proposal_json")
    if raw is None:
        raw = json.dumps(case["proposal"], ensure_ascii=False, sort_keys=True)

    if expected["result"] == "invalid":
        assert expected["error_code"] == "MODEL_OUTPUT_INVALID"
        with pytest.raises(DomainError) as error:
            validate_proposal(raw, project, case["mode"])
        assert error.value.code == expected["error_code"]
    else:
        assert expected["result"] == "valid"
        result = validate_proposal(raw, project, case["mode"])
        assert result["review_required"] is expected["review_required"]
        assert result["source_preserved"] is expected["source_preserved"]
        assert result["mode"] == case["mode"]
        assert [s["duration"] for s in result["scenes"]] == pytest.approx(
            expected["scene_durations"]
        )
        assert [s["narration"] for s in result["scenes"]] == expected["scene_narrations"]
        assert [len(s["second_by_second"]) for s in result["scenes"]] == (
            expected["beat_counts"]
        )
        assert [s["beat_plan_status"] for s in result["scenes"]] == (
            expected["beat_status"]
        )
        for scene, duration in zip(result["scenes"], expected["scene_durations"], strict=True):
            assert [b["second"] for b in scene["second_by_second"]] == list(
                range(len(scene["second_by_second"]))
            )
            assert 1 <= duration <= 20
            assert scene["fact_flags"]  # Human source review never bypassed
        assert sum(s["duration"] for s in result["scenes"]) <= (
            project["brief"]["target_duration"] + 0.01
        )

    assert project == before  # Proposal validation must not mutate the project.
    assert case["project"] == original_input
