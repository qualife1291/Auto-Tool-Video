"""Frame-exact timelines and measured silence, independent of model/renderer dependencies."""

import math
import re

DURATION_EPS = 0.01


def frames_for(duration: float) -> int:
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Duration must be finite and positive.")
    # FFprobe rounds container durations to microseconds; do not invent an extra frame.
    return max(1, math.ceil(duration * 30 - 0.0001))


def scene_timeline(scenes: list[dict]) -> list[dict]:
    frames = 0
    timeline = []
    for scene in scenes:
        count = frames_for(scene["duration"])
        timeline.append({"start": frames / 30, "duration": count / 30, "frames": count})
        frames += count
    return timeline


def silence_report(log: str, duration: float, silent: bool = False) -> dict:
    if silent:
        return {
            "status": "not_applicable",
            "reason": "Creator intentionally selected silent mode.",
            "intervals": [],
        }
    intervals = []
    start = None
    for match in re.finditer(r"silence_(start|end):\s*(-?[0-9.]+)", log):
        value = min(duration, max(0, float(match[2])))
        if match[1] == "start":
            start = value
        elif start is not None:
            intervals.append({"start": start, "end": value, "duration": max(0, value - start)})
            start = None
    if start is not None:
        intervals.append({"start": start, "end": duration, "duration": max(0, duration - start)})
    total = sum(i["duration"] for i in intervals)
    return {
        "status": "measured",
        "threshold_dbfs": -42,
        "min_interval_seconds": 0.25,
        "silence_seconds": total,
        "silence_ratio": total / duration if duration else 0,
        "longest_interval_seconds": max((i["duration"] for i in intervals), default=0),
        "intervals": intervals,
        "interpretation": "Measured low energy, not proof of missing words. Long holds need creator review.",
    }
