"""Negative contracts for the separate real FullHD smoke verifier.

These lightweight tests ensure no QC gate is quietly relaxed to return green.
The actual H264/AAC/FFmpeg export is executed by qa-dual1080-smoke.yml.
"""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "verify_dual_1080_smoke", ROOT / "scripts/verify_dual_1080_smoke.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
IntegrityError = module.IntegrityError


def metadata():
    return {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "pix_fmt": "yuv420p",
                "width": 1080,
                "height": 1920,
                "r_frame_rate": "30/1",
                "avg_frame_rate": "30/1",
                "duration": "3.0",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "3.02",
            },
        ],
        "format": {"duration": "3.02"},
    }


def frames():
    return [{"best_effort_timestamp_time": f"{i / 30:.6f}"} for i in range(90)]


def test_native_dimensions_and_video_audio_contract():
    data = module.validate_streams(metadata(), "portrait", 3)
    assert data["dimensions"] == [1080, 1920]
    assert data["audio_hz"] == 48000
    landscape = metadata()
    landscape["streams"][0].update(width=1920, height=1080)
    assert module.validate_streams(landscape, "landscape", 3)["dimensions"] == [1920, 1080]


@pytest.mark.parametrize(
    "change",
    [
        ("video", "codec_name", "vp9"),
        ("video", "pix_fmt", "rgb24"),
        ("video", "width", 720),
        ("video", "height", 1080),
        ("video", "avg_frame_rate", "30000/1001"),
        ("video", "r_frame_rate", "0/0"),
        ("audio", "codec_name", "mp3"),
        ("audio", "sample_rate", "44100"),
        ("audio", "duration", "3.3"),
        ("video", "duration", "2.7"),
        ("format", "duration", "NaN"),
    ],
)
def test_bad_stream_metadata_fails_closed(change):
    obj = copy.deepcopy(metadata())
    kind, key, value = change
    target = (
        obj["format"]
        if kind == "format"
        else next(stream for stream in obj["streams"] if stream["codec_type"] == kind)
    )
    target[key] = value
    with pytest.raises(IntegrityError):
        module.validate_streams(obj, "portrait", 3)


def test_mono_video_without_audio_is_not_mistaken_for_silent_approval():
    obj = metadata()
    obj["streams"].pop()
    with pytest.raises(IntegrityError, match="video.*audio"):
        module.validate_streams(obj, "portrait", 3)


def test_full_pts_sequence_has_exact_90_frames():
    assert module.validate_frame_pts(frames(), 3)["decoded_frames"] == 90


@pytest.mark.parametrize("mutation", ["duplicate", "gap", "missing", "negative", "nan"])
def test_frame_count_and_pts_regressions_are_rejected(mutation):
    data = frames()
    if mutation == "duplicate":
        data[25]["best_effort_timestamp_time"] = data[24]["best_effort_timestamp_time"]
    if mutation == "gap":
        data[26]["best_effort_timestamp_time"] = "1.3"
    if mutation == "missing":
        data.pop()
    if mutation == "negative":
        data[0]["best_effort_timestamp_time"] = "-1"
    if mutation == "nan":
        data[30]["best_effort_timestamp_time"] = "NaN"
    with pytest.raises(IntegrityError):
        module.validate_frame_pts(data, 3)


def test_measured_integrated_loudness_and_true_peak_both_mandatory():
    log = 'Summary:\n{\n "input_i": "-16.15",\n "input_tp": "-1.35",\n "input_lra": "0"\n}'
    assert module.parse_loudnorm_log(log) == {
        "integrated_lufs": -16.15,
        "true_peak_dbtp": -1.35,
    }


@pytest.mark.parametrize(
    "integrated,true_peak",
    [("-17.01", "-1.2"), ("-14.99", "-1.2"), ("-16", "-0.99"), ("-inf", "-2")],
)
def test_bad_audio_is_not_approved(integrated, true_peak):
    log = '{"input_i": "' + integrated + '", "input_tp": "' + true_peak + '"}'
    with pytest.raises(IntegrityError):
        module.parse_loudnorm_log(log)


def test_missing_and_duplicated_outputs_fail_closed(tmp_path):
    with pytest.raises(IntegrityError, match="portrait"):
        module.locate_mp4s(tmp_path)
    for aspect in module.ASPECTS:
        exports = tmp_path / aspect / "exports"
        exports.mkdir(parents=True)
        (exports / "one.mp4").write_bytes(b"not a real mp4")
    assert set(module.locate_mp4s(tmp_path)) == {"portrait", "landscape"}
    (tmp_path / "landscape" / "exports" / "two.mp4").write_bytes(b"duplicate")
    with pytest.raises(IntegrityError, match="landscape"):
        module.locate_mp4s(tmp_path)


def test_preflight_error_writes_red_report_and_never_claims_review(tmp_path):
    report = tmp_path / "qa" / "report.json"
    assert module.run(tmp_path / "missing", report, 3) == 1
    import json

    result = json.loads(report.read_text())
    assert result["status"] == "failed"
    assert result["release_approved"] is False
    assert result["human_review"] == "not_run"
    assert result["errors"]
