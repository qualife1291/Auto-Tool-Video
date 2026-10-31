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
MIN_LOW_DETAIL_SCENES = 4
LOW_DETAIL_MAX_EDGE_PIXELS = 20
LOW_DETAIL_MAX_LUMA_SPREAD = 12


def _edge_similarity(left: np.ndarray, right: np.ndarray) -> float | None:
    if left.shape != right.shape or left.ndim != 2:
        return None
    a = cv2.Canny(left.astype(np.uint8), 40, 100) > 0
    b = cv2.Canny(right.astype(np.uint8), 40, 100) > 0
    if min(int(a.sum()), int(b.sum())) < MIN_EDGE_PIXELS:
        return None
    kernel = np.ones((5, 5), np.uint8)
    a_near = cv2.dilate(a.astype(np.uint8), kernel) > 0
    b_near = cv2.dilate(b.astype(np.uint8), kernel) > 0
    return float(((a & b_near).sum() + (b & a_near).sum()) / (a.sum() + b.sum()))


def _low_detail(sample: np.ndarray) -> bool:
    """Flag a near-empty illustration ROI, not the meaning of its artwork."""
    if sample.shape != (160, 160):
        return False
    gray = sample.astype(np.uint8)
    spread = float(np.percentile(gray, 95) - np.percentile(gray, 5))
    edges = int(cv2.countNonZero(cv2.Canny(gray, 40, 100)))
    return spread <= LOW_DETAIL_MAX_LUMA_SPREAD and edges <= LOW_DETAIL_MAX_EDGE_PIXELS


def repeated_visual_findings(
    samples: list[np.ndarray], scenes: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Flag long runs of similar illustration ROIs with different spoken cues.

    Input is one 160x160 grayscale illustration ROI sampled near each scene's
    end. Similar or near-empty artwork produces a *review request*, never G10 approval.
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

    low_start: int | None = None
    for index in range(len(samples) + 1):
        eligible = index < len(samples) and _low_detail(samples[index])
        extends = (
            eligible
            and low_start is not None
            and scenes[index].get("narration", "").strip()
            != scenes[index - 1].get("narration", "").strip()
        )
        if low_start is not None and not extends:
            if index - low_start >= MIN_LOW_DETAIL_SCENES:
                start, end = low_start + 1, index
                findings.append(
                    {
                        "id": f"low-detail-art-{start}-{end}",
                        "kind": "possible_low_detail_illustration",
                        "severity": "manual_review",
                        "scene": start,
                        "end_scene": end,
                        "timestamp": round(
                            sum(float(scene["duration"]) for scene in scenes[:low_start]), 3
                        ),
                        "message": (
                            f"Cảnh {start}–{end} gần như không có minh họa. "
                            "Cần xem khung hình thật; G10 chưa được phê duyệt."
                        ),
                        "remedy": (
                            "Xem khung hình ở đầu/giữa/cuối từng cảnh và đối chiếu storyboard. "
                            "Xác nhận khoảng trống có chủ đích hoặc bổ sung hình truyền đạt ý."
                        ),
                    }
                )
            low_start = None
        if eligible and low_start is None:
            low_start = index
    return findings
