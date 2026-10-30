import csv
import io
import json
import sys
from uuid import uuid4

import pytest
from conftest import attach, create_story, save

from auto_tool_video.domain import ExportInput
from auto_tool_video.jobs import enqueue
from auto_tool_video.quality import (
    CRITERIA,
    csv_sheet,
    review_decision,
    scene_signals,
    technical_checks,
)
from auto_tool_video.render import Cancelled, render_job
from auto_tool_video.store import Store


def metadata():
    return {
        "streams": [
            {
                "codec_type": "video",
                "width": 360,
                "height": 640,
                "codec_name": "h264",
                "pix_fmt": "yuv420p",
                "r_frame_rate": "30/1",
                "duration": "1",
            },
            {"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "duration": "1"},
        ],
        "format": {"duration": "1"},
    }


@pytest.mark.parametrize(
    "failure",
    [
        "dimensions",
        "video_codec",
        "fps",
        "frame_timestamps",
        "duration",
        "av_duration",
        "audio_codec",
        "narration_loudness",
        "true_peak",
    ],
)
def test_technical_failures_are_independent_and_not_hidden_by_other_passes(failure):
    info, pts, loudness = (
        metadata(),
        [i / 30 for i in range(30)],
        {"input_i": "-16", "input_tp": "-1.3"},
    )
    if failure == "dimensions":
        info["streams"][0]["width"] = 640
    elif failure == "video_codec":
        info["streams"][0]["pix_fmt"] = "rgb24"
    elif failure == "fps":
        info["streams"][0]["r_frame_rate"] = "24/1"
    elif failure == "frame_timestamps":
        pts[10] = pts[9]
    elif failure == "duration":
        info["format"]["duration"] = "2"
    elif failure == "av_duration":
        info["streams"][1]["duration"] = "1.2"
    elif failure == "audio_codec":
        info["streams"][1]["sample_rate"] = "44100"
    elif failure == "narration_loudness":
        loudness["input_i"] = "-9.6"
    elif failure == "true_peak":
        loudness["input_tp"] = "-0.3"
    checks = technical_checks(
        info,
        {"scenes": [{"duration": 1}]},
        {"kind": "preview", "silent": False},
        pts,
        loudness,
        True,
    )
    assert [c["id"] for c in checks if c["status"] == "failed"] == [failure]


@pytest.mark.parametrize("value", ["NaN", "inf", "-inf", None])
def test_nonfinite_loudness_is_not_narration_pass(value):
    checks = technical_checks(
        metadata(),
        {"scenes": [{"duration": 1}]},
        {"kind": "preview"},
        [i / 30 for i in range(30)],
        {"input_i": value, "input_tp": value},
        True,
    )
    assert next(c for c in checks if c["id"] == "narration_loudness")["status"] == "failed"


def test_silent_mode_is_explicit_not_an_infinite_loudness_score():
    checks = technical_checks(
        metadata(),
        {"scenes": [{"duration": 1}]},
        {"kind": "preview", "silent": True},
        [i / 30 for i in range(30)],
        {"input_i": "-inf", "input_tp": "-inf"},
        True,
    )
    assert not any(c["status"] == "failed" for c in checks)
    assert next(c for c in checks if c["id"] == "narration_loudness")["status"] == "not_applicable"


def signal_rows(luma, delta=0):
    return [
        {"luma": value, "delta": None if i == 0 else delta, "sharpness": 0}
        for i, value in enumerate(luma)
    ]


def test_freeze_requires_declared_motion_and_whiteboard_hold_is_expected():
    rows = signal_rows([100] * 90)
    scene = {"duration": 3, "style": "motion"}
    assert scene_signals(rows, scene, 0, 1)["findings"] == []
    findings = scene_signals(rows, {**scene, "motion_expectation": "motion_required"}, 4, 2)[
        "findings"
    ]
    assert findings[0]["kind"] == "possible_freeze" and findings[0]["timestamp"] >= 4
    for i, row in enumerate(rows):
        row["delta"] = 2 if i < 60 else 0
    assert (
        scene_signals(
            rows, {**scene, "style": "whiteboard", "motion_expectation": "motion_required"}, 0, 1
        )["findings"]
        == []
    )


def test_flash_has_timestamp_and_cuts_are_not_joined_into_fake_flicker():
    values = [100] * 60
    values[30] = 200
    findings = scene_signals(signal_rows(values, 2), {"duration": 2}, 5, 2)["findings"]
    assert findings[0]["kind"] == "luminance_flash" and findings[0]["timestamp"] == 6
    for luma in (0, 255, 0):
        assert scene_signals(signal_rows([luma] * 30), {"duration": 1}, 0, 1)["findings"] == []


def report():
    return {
        "technical": {"status": "passed"},
        "artifact": {"silent": False, "captions": True},
        "signals": {"findings": []},
    }


def approved_review():
    return {
        "criteria": {
            key: {"score": 5, "critical": False, "note": "", "at_seconds": None} for key in CRITERIA
        },
        "reviewer": "Creator test",
        "watched_full": True,
        "listened_audio": True,
        "checked_captions": True,
        "checked_facts_age": True,
        "disclosure_reviewed": True,
        "content_origin": "ai_assisted",
        "disclosure_note": "Tranh và giọng có AI hỗ trợ.",
        "acknowledged_findings": [],
    }


@pytest.mark.parametrize(
    "score,critical,status",
    [
        (5, True, "rejected"),
        (1, False, "rejected"),
        (2, False, "rejected"),
        (3, False, "revise"),
        (4, False, "approved"),
    ],
)
def test_no_average_can_compensate_for_a_core_failure(score, critical, status):
    review = approved_review()
    review["criteria"]["prompt_alignment"].update(score=score, critical=critical)
    assert review_decision(report(), review)["status"] == status


@pytest.mark.parametrize(
    "missing",
    [
        "watched_full",
        "listened_audio",
        "checked_captions",
        "checked_facts_age",
        "disclosure_reviewed",
        "score",
        "origin",
        "warning",
    ],
)
def test_good_scores_do_not_replace_required_review(missing):
    review, qc = approved_review(), report()
    if missing == "score":
        review["criteria"].pop("technical_quality")
    elif missing == "origin":
        review["content_origin"] = "unknown"
    elif missing == "warning":
        qc["signals"]["findings"] = [{"id": "flash-1-10"}]
    else:
        review[missing] = False
    assert review_decision(qc, review)["status"] == "pending_review"
    qc["technical"]["status"] = "failed"
    assert review_decision(qc, review)["status"] == "blocked"


@pytest.fixture
def quality_export(client, image_bytes):
    project = create_story(client, "Nước đi đâu?")
    project = attach(client, project, project["scenes"][0], image_bytes)
    project["scenes"][0]["duration"] = 1
    project = save(client, project).json()
    store = client.app.state.store
    job = enqueue(
        store,
        project["id"],
        ExportInput(
            revision=project["revision"], kind="preview", silent=True, idempotency_key=str(uuid4())
        ),
    )
    render_job(store, store.claim())
    path = f"/api/projects/{project['id']}/exports/{job['id']}"
    qc = client.get(path + "/quality").json()
    payload = {**approved_review(), "video_sha256": qc["artifact"]["sha256"], "review_revision": 0}
    return project, job, path, qc, payload


def test_review_survives_restart_tracks_file_and_publish_uses_export(client, quality_export):
    project, job, path, qc, payload = quality_export
    assert qc["gate"]["status"] == "pending_review"
    assert all(b["status"] == "not_run" for b in qc["benchmarks"])
    assert qc["provenance"]["inputs"][0]["stored_sha256"]
    saved = client.put(path + "/quality-review", json=payload)
    assert saved.status_code == 200 and saved.json()["gate"]["status"] == "approved"
    restored = Store(client.app.state.store.root).get("jobs", job["id"])["quality_report"]
    assert (
        restored["review_revision"] == 1 and restored["manual_review"]["reviewer"] == "Creator test"
    )
    project["title"] = "Draft changed"
    assert save(client, project).status_code == 200
    pack = client.get(f"/api/projects/{project['id']}/publish-pack?job_id={job['id']}").json()
    assert pack["title"] != "Draft changed"
    assert pack["quality"]["artifact"]["sha256"] == payload["video_sha256"]
    assert pack["generation_disclosure"]["origin"] == "ai_assisted"
    assert client.put(path + "/quality-review", json=payload).status_code == 409


def test_review_rejects_cross_project_hash_timestamp_and_known_ai_mislabel(client, quality_export):
    _, job, path, _qc, payload = quality_export
    other = create_story(client)
    assert client.get(f"/api/projects/{other['id']}/exports/{job['id']}/quality").status_code == 404
    for patch, status in [
        ({"video_sha256": "0" * 64}, 409),
        ({"criteria": {"technical_quality": {"at_seconds": 2}}}, 400),
        ({"acknowledged_findings": ["fake"]}, 400),
    ]:
        assert client.put(path + "/quality-review", json={**payload, **patch}).status_code == status
    store = client.app.state.store
    raw = store.get("jobs", job["id"])
    raw["quality_report"]["provenance"]["known_ai_usage"] = True
    store.update_job(job["id"], quality_report=raw["quality_report"])
    assert (
        client.put(
            path + "/quality-review", json={**payload, "content_origin": "no_ai"}
        ).status_code
        == 400
    )
    asset = store.get("assets", raw["result_id"])
    store.asset_path(asset).write_bytes(b"changed after QC")
    assert client.put(path + "/quality-review", json=payload).status_code == 409
    assert client.get(path + "/quality").json()["manual_review"] is None


@pytest.mark.parametrize("score", [True, False, 0, 6, 4.5, "5"])
def test_score_validation_cannot_be_forged(client, quality_export, score):
    _, _, path, _, payload = quality_export
    payload["criteria"]["technical_quality"]["score"] = score
    assert client.put(path + "/quality-review", json=payload).status_code == 422


def test_csv_is_unicode_formula_safe_and_partial_does_not_auto_approve(client, quality_export):
    _, _, path, _, payload = quality_export
    payload["criteria"] = {
        "prompt_alignment": {"score": 5, "note": '=HYPERLINK("https://bad.example")'}
    }
    assert (
        client.put(path + "/quality-review", json=payload).json()["gate"]["status"]
        == "pending_review"
    )
    response = client.get(path + "/quality.csv")
    assert response.status_code == 200 and response.text.startswith("\ufeff")
    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[2][4].startswith("'=")
    assert "Khớp kịch bản" in rows[2][0]


def test_old_export_has_unavailable_qc_not_a_fabricated_pass(client, quality_export):
    _, job, path, _, _ = quality_export
    store = client.app.state.store
    with store.connect() as conn:
        raw = store.get("jobs", job["id"], conn)
        raw.pop("quality_report")
        conn.execute("UPDATE jobs SET data=? WHERE id=?", (json.dumps(raw), job["id"]))
    assert client.get(path + "/quality").json()["gate"]["status"] == "unavailable"
    assert "Tiêu chí" in csv_sheet(client.get(path + "/quality").json())


def test_failed_qc_keeps_previous_good_video_and_failed_report(client, quality_export, monkeypatch):
    from auto_tool_video import render

    project, old, _, _, _ = quality_export
    store = client.app.state.store
    original = store.asset_path(store.get("assets", old["id"])).read_bytes()
    next_job = enqueue(
        store,
        project["id"],
        ExportInput(
            revision=project["revision"], kind="preview", silent=True, idempotency_key=str(uuid4())
        ),
    )
    monkeypatch.setattr(
        render,
        "inspect_video",
        lambda *args: {"technical": {"status": "failed"}, "gate": {"status": "blocked"}},
    )
    with pytest.raises(RuntimeError, match="QC"):
        render_job(store, store.claim())
    failed = store.get("jobs", next_job["id"])
    assert failed["state"] == "failed" and failed["result_id"] is None
    assert failed["quality_report"]["gate"]["status"] == "blocked"
    assert store.asset_path(store.get("assets", old["id"])).read_bytes() == original


def test_qc_process_is_killed_on_cancel_and_large_output_is_rejected(monkeypatch):
    from auto_tool_video import quality

    processes = []
    popen = quality.subprocess.Popen

    def capture(*args, **kwargs):
        process = popen(*args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(quality.subprocess, "Popen", capture)

    def cancel():
        raise Cancelled()

    with pytest.raises(Cancelled):
        quality._run([sys.executable, "-c", "import time;time.sleep(5)"], cancel)
    assert processes[-1].poll() is not None
    with pytest.raises(RuntimeError, match="giới hạn"):
        quality._run([sys.executable, "-c", "print('x'*(3*1024*1024))"], lambda: None)
    assert processes[-1].poll() is not None


def test_review_can_acknowledge_maximum_twenty_findings_per_twenty_scenes():
    from auto_tool_video.domain import QualityReviewInput

    qc, review = report(), approved_review()
    qc["signals"]["findings"] = [{"id": f"signal-{i}"} for i in range(400)]
    review["acknowledged_findings"] = [item["id"] for item in qc["signals"]["findings"]]
    validated = QualityReviewInput.model_validate(
        {**review, "video_sha256": "0" * 64, "review_revision": 0}
    )
    assert review_decision(qc, validated.model_dump())["status"] == "approved"
