"""Engineering semantic manifests must not masquerade as creator signoff."""

import hashlib
import importlib
import json
from pathlib import Path


def test_semantic_manifest(monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(root / "scripts"))
    scenarios = importlib.import_module("qa_video_scenarios")

    # Avoid expensive eSpeak/FFmpeg here; test the real scenario report builder.
    monkeypatch.setattr(
        scenarios,
        "voice",
        lambda cue, path, rate: {
            "duration": 0.5,
            "narration": cue,
            "sha256": "stub-voice",
        },
    )
    monkeypatch.setattr(
        scenarios,
        "render_one",
        lambda root, scenario, aspect, kind, voices: {"aspect": aspect},
    )

    report = scenarios.run("water-12s", tmp_path)
    persisted = json.loads((tmp_path / "scenario-report.json").read_text("utf-8"))
    assert persisted == report
    assert report["status"] == "TECHNICAL_PASS_ONLY"
    assert report["release_approved"] is False
    assert report["human_review"] == "NOT RUN"
    assert len(report["cues"]) == len(scenarios.SCENARIOS["water-12s"].cues)

    hashes = set()
    for i, cue in enumerate(report["cues"]):
        title = cue["title"]
        assert cue["expected_objects"] == list(
            scenarios.EXPECTED_OBJECTS["water-12s"][title]
        )
        assert cue["semantic_review"] == "NOT RUN"
        expected_hash = hashlib.sha256(
            scenarios.visual(i, scenarios.SCENARIOS["water-12s"])
        ).hexdigest()
        assert cue["visual_sha256"] == expected_hash
        hashes.add(expected_hash)

    # Different water-cycle actions must not silently reuse one generic picture.
    assert len(hashes) == len(report["cues"])
