"""High-detail Comfy candidates must remain grounded in narration and story beats."""

from auto_tool_video.image_prompt import build_image_prompt


def _project(aspect="portrait"):
    return {
        "aspect": aspect,
        "brief": {
            "style_bible": "Warm watercolor science illustration",
            "character_bible": "Same blue shirt",
        },
    }


def _scene(**changes):
    item = {
        "title": "Nước bay hơi",
        "image_prompt": "  Blue cotton shirt in a garden  ",
        "visual_description": "Cotton fibers, tiny wet droplets and moving air in a sunlit yard",
        "narration": "Nước trên áo bay hơi vào không khí.",
        "beat_plan_status": "authored",
        "second_by_second": [
            {"second": 0, "visual_state": "wet blue shirt", "action": "water beads sparkle"},
            {
                "second": 1,
                "visual_state": "visible threads and beads of water",
                "action": "droplets evaporate into air",
            },
            {"second": 2, "visual_state": "dry blue shirt", "action": "fabric dries"},
        ],
    }
    item.update(changes)
    return item


def test_scene_specific_midpoint_action_and_narration_are_in_final_prompt():
    positive, negative = build_image_prompt(_project(), _scene())
    assert positive.startswith("  Blue cotton shirt in a garden  \n")
    assert "Nước trên áo bay hơi vào không khí." in positive
    assert "droplets evaporate into air" in positive
    assert "visible threads and beads of water" in positive
    assert "Cotton fibers, tiny wet droplets" in positive
    assert "Warm watercolor" in positive
    assert "mostly blank background" in negative


def test_other_scene_has_different_action_despite_same_base_asset():
    first, _ = build_image_prompt(_project(), _scene())
    other, _ = build_image_prompt(
        _project(),
        _scene(
            narration="Gió làm chiếc áo khô nhanh hơn.",
            second_by_second=[
                {"second": 0, "visual_state": "fluttering cloth", "action": "gust bends the shirt"}
            ],
        ),
    )
    assert first != other
    assert "gust bends the shirt" in other
    assert "droplets evaporate into air" not in other


def test_only_authored_beats_used_and_legacy_scene_remains_supported():
    positive, _ = build_image_prompt(
        _project("landscape"),
        _scene(
            beat_plan_status="needs_review",
            second_by_second=[
                {
                    "second": 0,
                    "visual_state": "generic placeholder",
                    "action": "generic action",
                }
            ],
        ),
    )
    assert "generic placeholder" not in positive
    assert "generic action" not in positive
    assert "16:9" in positive
    assert "Same blue shirt" in positive


def test_portrait_full_bleed_preserves_caption_safe_area_and_no_fake_quality_claim():
    positive, negative = build_image_prompt(_project(), _scene(visual_description=""))
    assert "9:16" in positive
    assert "full-bleed" in positive
    assert "caption" in positive
    assert "material" in positive.lower()
    assert "low-detail" in negative
    assert "cropped subject" in negative
    assert "quality score" not in positive.lower()
