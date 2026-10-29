"""Measure a real 20-scene render; no model quality or real-time claim."""

import argparse
import json
import resource
import time
from pathlib import Path

from smoke_export import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    run(args.output_dir, "portrait", False, scene_count=20)
    elapsed = time.perf_counter() - started
    report = {
        "scenes": 20,
        "frames": 600,
        "resolution": "360x640",
        "elapsed_seconds": round(elapsed, 3),
        "frames_per_second": round(600 / elapsed, 2),
        "python_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "max_child_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        "fixture": "original Pillow diagrams + sine tone, not AI models or narration",
    }
    (args.output_dir / "benchmark.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report))
