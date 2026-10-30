"""Read-only local audit of an existing video using its actual export snapshot."""

import argparse
import json
from pathlib import Path

from auto_tool_video.quality import csv_sheet, inspect_video


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument(
        "--snapshot", type=Path, required=True, help="report-*.json or export job JSON"
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--silent", action="store_true")
    args = parser.parse_args()
    source = json.loads(args.snapshot.read_text())
    snapshot = source.get("project", source.get("snapshot"))
    if not snapshot:
        parser.error(
            "Snapshot must contain project or snapshot; do not guess scene boundaries."
        )
    options = source.get("options") or {
        "kind": "export",
        "aspect": source.get("aspect", snapshot.get("aspect", "portrait")),
        "silent": args.silent,
        "captions": True,
    }
    report = inspect_video(args.video.resolve(), snapshot, options)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "quality-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )
    (args.output_dir / "qa-qc-sheet.csv").write_text(csv_sheet(report))
    print(
        json.dumps(
            {
                "technical": report["technical"]["status"],
                "gate": report["gate"]["status"],
                "findings": len(report.get("signals", {}).get("findings", [])),
                "sha256": report["artifact"]["sha256"],
            }
        )
    )
    if report["technical"]["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
