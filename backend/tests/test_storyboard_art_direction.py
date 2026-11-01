"""Storyboard direction contract: actionable shots instead of generic icon sequences."""

from auto_tool_video.planning import SYSTEM_PROMPT


def test_storyboard_generation_requires_narration_pacing_and_specific_object_changes():
    normalized = " ".join(SYSTEM_PROMPT.split())
    for phrase in (
        "short spoken Vietnamese clauses",
        "punctuation for natural breaths",
        "object, physical action and visible consequence",
        "beginning/middle/end",
    ):
        assert phrase in normalized


def test_storyboard_art_direction_preserves_camera_and_color_continuity():
    normalized = " ".join(SYSTEM_PROMPT.split())
    for phrase in (
        "stable color palette",
        "material textures",
        "camera hold, pan or slow push",
        "portrait and landscape caption safe zones",
        "no arbitrary zoom",
    ):
        assert phrase in normalized
