"""Check offline QA voice evidence is measurable but not human-approved."""
import ast
from pathlib import Path


def test_voice_report_records_pacing_without_approving_espeak():
    source = (
        Path(__file__).resolve().parents[2] / "scripts" / "qa_video_scenarios.py"
    ).read_text(encoding="utf-8")
    ast.parse(source)
    assert '"effective_wpm": round(60 * words / duration, 1)' in source
    assert '"voice_review": "NOT RUN"' in source
    assert '"voice_approval": "NOT APPROVED"' in source
