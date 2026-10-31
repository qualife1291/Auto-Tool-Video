"""Repeated art is a G9 review hint, never a creator G10 approval."""

import cv2
import numpy as np
import pytest

from auto_tool_video.semantic_screen import repeated_visual_findings


def _frame(kind: str, color: int = 35, shift: int = 0) -> np.ndarray:
    image = np.full((160, 160), 250, dtype=np.uint8)
    cv2.rectangle(image, (12, 12), (148, 148), 120, 2)
    if kind == "same":
        cv2.rectangle(image, (48 + shift, 45), (110 + shift, 115), color, 3)
        cv2.ellipse(image, (79 + shift, 75), (15, 23), 0, 0, 360, color, 3)
    elif kind == "sun":
        cv2.circle(image, (80, 78), 38, color, 3)
        for angle in range(0, 360, 45):
            rad = np.deg2rad(angle)
            cv2.line(
                image,
                (int(80 + 45 * np.cos(rad)), int(78 + 45 * np.sin(rad))),
                (int(80 + 62 * np.cos(rad)), int(78 + 62 * np.sin(rad))),
                color,
                3,
            )
    elif kind == "road":
        cv2.line(image, (25, 50), (140, 50), color, 4)
        cv2.line(image, (25, 105), (140, 105), color, 4)
    elif kind == "drop":
        cv2.ellipse(image, (80, 80), (30, 45), 0, 0, 360, color, 3)
    return image


def _scenes(n: int) -> list[dict]:
    return [
        {"title": f"Scene {i}", "narration": f"Distinct spoken action {i}", "duration": 3}
        for i in range(n)
    ]


def test_repeated_illustration_across_distinct_cues_warns_without_approval():
    frames = [_frame("same", color=30 + i * 2, shift=i % 2) for i in range(6)]
    findings = repeated_visual_findings(frames, _scenes(6))
    assert len(findings) == 1
    assert findings[0]["kind"] == "possible_repeated_illustration"
    assert findings[0]["scene"] == 1
    assert findings[0]["end_scene"] == 6
    assert findings[0]["severity"] == "manual_review"
    assert "G10" in findings[0]["message"]


def test_distinct_art_with_same_frame_border_is_not_flagged():
    frames = [_frame(k) for k in ("same", "sun", "road", "drop", "sun")]
    assert repeated_visual_findings(frames, _scenes(len(frames))) == []


def test_legitimate_two_scene_continuity_is_not_flagged():
    assert repeated_visual_findings([_frame("same"), _frame("same")], _scenes(2)) == []


def test_blank_art_and_same_narration_do_not_generate_false_semantic_claims():
    blank = np.full((160, 160), 250, dtype=np.uint8)
    assert repeated_visual_findings([blank] * 6, _scenes(6)) == []
    scenes = [{"title": "same", "narration": "same", "duration": 3}] * 6
    assert repeated_visual_findings([_frame("same")] * 6, scenes) == []


def test_invalid_sample_count_is_explicitly_rejected():
    with pytest.raises(ValueError, match="scene count"):
        repeated_visual_findings([_frame("same")], _scenes(2))


def test_small_two_pixel_reframing_still_warns_on_four_distinct_cues():
    frames = [_frame("same", shift=i % 2 * 2) for i in range(4)]
    findings = repeated_visual_findings(frames, _scenes(4))
    assert [(item["scene"], item["end_scene"]) for item in findings] == [(1, 4)]
