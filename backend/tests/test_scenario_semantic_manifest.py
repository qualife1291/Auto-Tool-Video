"""Engineering semantic manifest must never masquerade as creator signoff."""
import ast
from pathlib import Path


def test_scenario_report_tracks_semantic_review_and_art_hash():
    path = Path(__file__).resolve().parents[2] / "scripts" / "qa_video_scenarios.py"
    source = path.read_text(encoding="utf-8")
    ast.parse(source)
    assert '"expected_objects": list(EXPECTED_OBJECTS[scenario.key][title])' in source
    assert '"visual_sha256": hashlib.sha256(visual(i, scenario)).hexdigest()' in source
    assert '"semantic_review": "NOT RUN"' in source
    assert '"release_approved": False' in source
