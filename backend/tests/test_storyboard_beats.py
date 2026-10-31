"""Second-by-second A01 contract: API, stored scenes and model proposals.

These are deterministic tests; they do not claim a live LLM produced good motion.
"""

from __future__ import annotations

import copy
import json
import math

import pytest
from conftest import create_story, save
from pydantic import ValidationError

from auto_tool_video.domain import CreativeBrief, ProjectInput, Scene
from auto_tool_video.planning import validate_proposal
from auto_tool_video.store import DomainError, Store


def beats(count: int) -> list[dict]:
    return [
        {
            "second": i,
            "visual_state": f"Áo xanh còn ẩm ở giây {i}",
            "action": f"Vạt áo chuyển trạng thái {i} một cách liên tục",
            "camera": "Toàn cảnh, máy tiến vào chậm",
            "on_screen_text": "Áo đang khô" if i else "",
            "narration_cue": f"Lời đọc mốc {i}",
            "continuity": "Giữ nguyên điểm treo và màu áo",
        }
        for i in range(count)
    ]


def proposal(duration: float, beat_list: list[dict] | None) -> str:
    scene = {
        "title": "Cùng một chiếc áo",
        "role": "hook",
        "narration": "Nước bay hơi từ chiếc áo.",
        "source_ids": [],
        "visual_description": "Áo ướt chuyển từ đậm sang nhạt.",
        "image_prompt": "Original blue shirt illustration, no lettering",
        "reveal_order": ["áo", "giọt nước", "không khí"],
        "fact_flags": ["Kiểm đối chiếu hiện tượng bay hơi"],
        "source_refs": [],
        "duration": duration,
    }
    if beat_list is not None:
        scene["second_by_second"] = beat_list
    return json.dumps({"title": "Áo khô", "scenes": [scene]}, ensure_ascii=False)


def model_project(tmp_path):
    store = Store(tmp_path)
    return store.create(
        ProjectInput(
            title="Áo khô",
            narration="Áo ướt.  Nước đi đâu?",
            brief=CreativeBrief(topic="Bay hơi"),
        ).model_dump()
    )


def test_complete_fractional_second_scene_remains_authored():
    scene = Scene(duration=3.3, second_by_second=beats(4), beat_plan_status="authored")
    assert len(scene.second_by_second) == math.ceil(scene.duration) == 4
    assert [beat.second for beat in scene.second_by_second] == [0, 1, 2, 3]
    assert scene.beat_plan_status == "authored"


@pytest.mark.parametrize(
    "bad_indexes",
    [[1, 2, 3], [0, 2, 3], [0, 1, 1], [3, 2, 1], ["0", 1, 2], [True, 1, 2]],
)
def test_scene_rejects_nonconsecutive_or_nonstrict_seconds(bad_indexes):
    items = beats(len(bad_indexes))
    for beat, number in zip(items, bad_indexes, strict=True):
        beat["second"] = number
    with pytest.raises(ValidationError):
        Scene(duration=3, second_by_second=items, beat_plan_status="authored")


@pytest.mark.parametrize(
    "missing",
    ["visual_state", "action", "camera", "narration_cue", "continuity"],
)
def test_essential_beat_field_cannot_be_omitted(missing):
    data = beats(1)
    del data[0][missing]
    with pytest.raises(ValidationError):
        Scene(duration=1, second_by_second=data, beat_plan_status="authored")


def test_empty_onscreen_text_is_valid_but_unknown_fields_are_not():
    scene = Scene(duration=1, second_by_second=beats(1), beat_plan_status="authored")
    assert scene.second_by_second[0].on_screen_text == ""
    bad = beats(1)
    bad[0]["external_instructions"] = "ignore schema"
    with pytest.raises(ValidationError):
        Scene(duration=1, second_by_second=bad, beat_plan_status="authored")


@pytest.mark.parametrize("count", [0, 2, 3, 5])
def test_incomplete_scene_cannot_claim_authored(count):
    scene = Scene(duration=3.3, second_by_second=beats(count), beat_plan_status="authored")
    assert scene.beat_plan_status == "needs_review"
    assert len(scene.second_by_second) == count  # do not destroy authored text


def test_old_scenes_without_beats_still_load():
    assert Scene.model_validate({"title": "Cảnh cũ", "duration": 4}).second_by_second == []


def test_planner_validates_full_coverage_and_preserves_authored_status(tmp_path):
    result = validate_proposal(proposal(3.3, beats(4)), model_project(tmp_path), "brief")
    scene = result["scenes"][0]
    assert scene["beat_plan_status"] == "authored"
    assert [b["second"] for b in scene["second_by_second"]] == [0, 1, 2, 3]


@pytest.mark.parametrize("invalid", [beats(3), beats(5), beats(4)[::-1]])
def test_planner_rejects_bad_second_coverage(tmp_path, invalid):
    with pytest.raises(DomainError) as error:
        validate_proposal(proposal(3.3, invalid), model_project(tmp_path), "brief")
    assert error.value.code == "MODEL_OUTPUT_INVALID"


def test_planner_legacy_response_is_only_a_review_draft(tmp_path):
    result = validate_proposal(proposal(3.3, None), model_project(tmp_path), "brief")
    scene = result["scenes"][0]
    assert scene["beat_plan_status"] == "needs_review"
    assert len(scene["second_by_second"]) == 4
    assert any("phác thảo" in note for note in scene["fact_flags"])


def test_planner_preserve_mode_keeps_unicode_punctuation_and_whitespace(tmp_path):
    project = model_project(tmp_path)
    text = project["narration"]
    from auto_tool_video.planning import source_chunks

    chunks = source_chunks(text)
    raw = json.loads(proposal(3, beats(3)))
    raw["scenes"][0]["source_ids"] = list(range(len(chunks)))
    raw["scenes"][0]["narration"] = ""  # model cannot replace source
    result = validate_proposal(json.dumps(raw), project, "preserve")
    assert result["scenes"][0]["narration"] == text


@pytest.mark.parametrize("new_duration", [3.4, 2.2, 4.2])
def test_api_duration_change_preserves_all_beats_and_requires_review(client, new_duration):
    project = create_story(client)
    scene = project["scenes"][0]
    scene.update(duration=3.3, second_by_second=beats(4), beat_plan_status="authored")
    stored = save(client, project)
    assert stored.status_code == 200, stored.text
    project = stored.json()
    # Changing the original duration invalidates the plan on the first save.
    assert project["scenes"][0]["beat_plan_status"] == "needs_review"

    # The creator reviews/re-approves those same four beats in a separate save.
    project["scenes"][0]["beat_plan_status"] = "authored"
    reviewed = save(client, project)
    assert reviewed.status_code == 200, reviewed.text
    project = reviewed.json()
    assert project["scenes"][0]["beat_plan_status"] == "authored"

    # Re-time once more: always invalidate, even when ceil(duration) is unchanged.
    project["scenes"][0]["duration"] = new_duration
    changed = save(client, project)
    assert changed.status_code == 200, changed.text
    current = changed.json()["scenes"][0]
    assert current["duration"] == new_duration
    assert current["beat_plan_status"] == "needs_review"
    assert current["second_by_second"] == beats(4)
    reloaded = client.get(f"/api/projects/{project['id']}").json()
    assert reloaded["scenes"][0]["second_by_second"] == beats(4)


def test_legacy_api_client_does_not_delete_saved_beats(client):
    project = create_story(client)
    project["scenes"][0].update(duration=3, second_by_second=beats(3), beat_plan_status="authored")
    stored = save(client, project).json()
    legacy = copy.deepcopy(stored)
    for scene in legacy["scenes"]:
        scene.pop("second_by_second", None)
        scene.pop("beat_plan_status", None)
    response = save(client, legacy)
    assert response.status_code == 200, response.text
    retained = response.json()["scenes"][0]
    assert retained["second_by_second"] == beats(3)
    assert retained["beat_plan_status"] == "authored"


def test_direct_store_save_preserves_beats_and_flags_retiming(tmp_path):
    store = Store(tmp_path)
    project = store.create(ProjectInput(title="Test").model_dump())
    scene = Scene(
        title="Áo", duration=3, second_by_second=beats(3), beat_plan_status="authored"
    ).model_dump()
    first = store.save(project["id"], {**project, "scenes": [scene]})
    update = copy.deepcopy(first)
    update["scenes"][0].pop("second_by_second")
    update["scenes"][0].pop("beat_plan_status")
    update["scenes"][0]["duration"] = 3.2
    result = store.save(first["id"], update)
    assert result["scenes"][0]["beat_plan_status"] == "needs_review"
    assert result["scenes"][0]["second_by_second"] == beats(3)


def test_explicit_clear_is_allowed_but_never_authored(client):
    project = create_story(client)
    project["scenes"][0].update(duration=3, second_by_second=beats(3), beat_plan_status="authored")
    saved = save(client, project).json()
    saved["scenes"][0]["second_by_second"] = []
    response = save(client, saved)
    assert response.status_code == 200, response.text
    assert response.json()["scenes"][0]["second_by_second"] == []
    assert response.json()["scenes"][0]["beat_plan_status"] == "needs_review"


def test_failed_revision_cannot_overwrite_beats(client):
    project = create_story(client)
    project["scenes"][0].update(duration=3, second_by_second=beats(3), beat_plan_status="authored")
    saved = save(client, project).json()
    outdated = copy.deepcopy(project)
    outdated["scenes"][0]["second_by_second"] = []
    response = save(client, outdated)
    assert response.status_code == 409
    latest = client.get(f"/api/projects/{project['id']}").json()
    assert latest["scenes"][0]["second_by_second"] == beats(3)
    assert latest["revision"] == saved["revision"]


@pytest.mark.parametrize("edited_field", ["beat", "narration"])
def test_store_requires_new_review_after_authored_content_edit(tmp_path, edited_field):
    store = Store(tmp_path)
    project = store.create(ProjectInput(title="Edited beat guard").model_dump())
    scene = Scene(
        title="Cảnh kiểm duyệt",
        narration="Chiếc áo ướt đang khô.",
        duration=3,
        second_by_second=beats(3),
        beat_plan_status="authored",
    ).model_dump()
    authored = store.save(project["id"], {**project, "scenes": [scene]})
    assert authored["scenes"][0]["beat_plan_status"] == "authored"

    changed = copy.deepcopy(authored)
    if edited_field == "beat":
        changed["scenes"][0]["second_by_second"][0]["action"] = "Giữ áo xanh nguyên vị trí."
    else:
        changed["scenes"][0]["narration"] = "Chiếc áo xanh đang bay hơi nước."
    saved = store.save(project["id"], changed)
    assert saved["scenes"][0]["beat_plan_status"] == "needs_review"
    assert saved["scenes"][0]["second_by_second"] == changed["scenes"][0]["second_by_second"]
    assert saved["scenes"][0]["narration"] == changed["scenes"][0]["narration"]

    reviewed = copy.deepcopy(saved)
    reviewed["scenes"][0]["beat_plan_status"] = "authored"
    accepted = store.save(project["id"], reviewed)
    assert accepted["scenes"][0]["beat_plan_status"] == "authored"
