"""Advisory cross-scene image repetition screening, not semantic verification.

This deliberately cannot decide whether a drawing matches its narration or whether
repeated artwork is intentional. Only human review can resolve the warning.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

# A sequence of at least four distinct narrated scenes with nearly unchanged
# edges warrants human review. The threshold is a heuristic, not an acceptance gate.
EDGE_SIMILARITY = 0.78
MIN_CONSECUTIVE_PAIRS = 3
MIN_EDGE_PIXELS = 100


def _edge_similarity(left: np.ndarray, right: np.ndarray) -> float | None:
    if left.shape != right.shape or left.ndim != 2:
        return None
    a = cv2.Canny(left.astype(np.uint8), 40, 100) > 0
    b = cv2.Canny(right.astype(np.uint8), 40, 100) > 0
    if min(int(a.sum()), int(b.sum())) < MIN_EDGE_PIXELS:
        return None
    kernel = np.ones((3, 3), np.uint8)
    a_near = cv2.dilate(a.astype(np.uint8), kernel) > 0
    b_near = cv2.dilate(b.astype(np.uint8), kernel) > 0
    return float(((a & b_near).sum() + (b & a_near).sum()) / (a.sum() + b.sum()))


def repeated_visual_findings(
    samples: list[np.ndarray], scenes: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Flag long runs of similar illustration ROIs with different spoken cues.

    Input is one 160x160 grayscale illustration ROI sampled near each scene's
    end. A result is a *review request*, never a G9/G10 pass or failure.
    """
    if len(samples) != len(scenes):
        raise ValueError("Visual sample count must equal scene count")
    findings: list[dict[str, Any]] = []
    run_start: int | None = None
    run_scores: list[float] = []

    def flush() -> None:
        nonlocal run_start, run_scores
        if run_start is not None and len(run_scores) >= MIN_CONSECUTIVE_PAIRS:
            start = run_start + 1
            end = run_start + len(run_scores) + 1
            findings.append(
                {
                    "id": f"repeated-art-{start}-{end}",
                    "kind": "possible_repeated_illustration",
                    "severity": "manual_review",
                    "scene": start,
                    "end_scene": end,
                    "timestamp": round(
                        sum(float(scene["duration"]) for scene in scenes[:run_start]), 3
                    ),
                    "min_edge_similarity": round(min(run_scores), 3),
                    "message": (
                        f"Cảnh {start}–{end} có minh họa gần lặp dù lời thoại khác nhau. "
                        "Cần xem/nghe và đối chiếu storyboard; G10 chưa được phê duyệt."
                    ),
                    "remedy": (
                        "Kiểm từng vật thể/hành động với lời thoại trên video thực tế. "
                        "Giữ cảnh lặp có chủ đích; thay minh họa nếu không truyền đạt ý mới."
                    ),
                }
            )
        run_start = None
        run_scores = []

    for index in range(len(samples) - 1):
        different_cue = (
            scenes[index].get("narration", "").strip()
            != scenes[index + 1].get("narration", "").strip()
        )
        score = _edge_similarity(samples[index], samples[index + 1]) if different_cue else None
        if score is not None and score >= EDGE_SIMILARITY:
            if run_start is None:
                run_start = index
            run_scores.append(score)
        else:
            flush()
    flush()
    return findings
