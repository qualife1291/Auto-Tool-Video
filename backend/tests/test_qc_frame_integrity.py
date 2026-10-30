"""Reject plausible-looking CFR metadata when a frame was lost or shifted.

These are independent QC checks: a 29-frame H.264 video can still be fully
decodable, report 30fps and fall within the 100ms duration allowance.
"""

import json
import math
import shutil
import subprocess

import pytest

from auto_tool_video.quality import technical_checks


def _metadata(frames=90):
    return {
        "streams": [
            {
                "codec_type": "video",
                "width": 360,
                "height": 640,
                "codec_name": "h264",
                "pix_fmt": "yuv420p",
                "r_frame_rate": "30/1",
                "duration": "3",
                "nb_frames": str(frames),
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "duration": "3.033333",
            },
        ],
        "format": {"duration": "3.033333"},
    }


def _checks(pts, info=None):
    return {
        item["id"]: item
        for item in technical_checks(
            info or _metadata(),
            {"scenes": [{"duration": 1.2}, {"duration": 1.8}]},
            {"aspect": "portrait", "kind": "preview", "silent": False},
            pts,
            {"input_i": "-16", "input_tp": "-1.5"},
            decoded=True,
        )
    }


def test_positive_unequal_scenes_match_exact_30fps_grid():
    pts = [i / 30 for i in range(90)]
    checks = _checks(pts)
    assert all(item["status"] == "passed" for item in checks.values())
    assert checks["frame_timestamps"]["actual"]["expected_frames"] == 90
    assert checks["frame_timestamps"]["actual"]["frames"] == 90


@pytest.mark.parametrize(
    "tampering",
    [
        "missing_last",
        "missing_first",
        "extra_last",
        "constant_33ms_offset",
        "duplicate_middle",
        "pts_jump",
        "nonfinite",
        "nonuniform_drift",
    ],
)
def test_false_cfr_or_wrong_frame_count_must_fail(tampering):
    pts = [i / 30 for i in range(90)]
    if tampering == "missing_last":
        pts.pop()
    elif tampering == "missing_first":
        pts.pop(0)
    elif tampering == "extra_last":
        pts.append(3.0)
    elif tampering == "constant_33ms_offset":
        pts = [x + 1 / 30 for x in pts]
    elif tampering == "duplicate_middle":
        pts[45] = pts[44]
    elif tampering == "pts_jump":
        pts[45] += 1 / 30
    elif tampering == "nonfinite":
        pts[45] = math.nan
    elif tampering == "nonuniform_drift":
        pts = [i / 30 + i * 0.00005 for i in range(90)]
    if tampering in {"missing_last", "missing_first", "extra_last"}:
        # Deliberately spoof a consistent codec-level count to test real PTS.
        info = _metadata(len(pts))
    else:
        info = _metadata()
    checks = _checks(pts, info)
    assert checks["frame_timestamps"]["status"] == "failed", tampering
    # A different green check must not compensate for missing frames.
    assert checks["duration"]["status"] == "passed"


@pytest.mark.parametrize("reported_count", ["89", "91", "N/A", "-1", "89.5"])
def test_ffprobe_reported_frame_count_cannot_disagree_with_decoded_pts(reported_count):
    info = _metadata()
    info["streams"][0]["nb_frames"] = reported_count
    assert _checks([i / 30 for i in range(90)], info)["frame_timestamps"]["status"] == "failed"


def test_optional_nb_frames_absence_does_not_hide_valid_decoded_pts():
    info = _metadata()
    del info["streams"][0]["nb_frames"]
    assert _checks([i / 30 for i in range(90)], info)["frame_timestamps"]["status"] == "passed"


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="real FFmpeg/FFprobe required",
)
@pytest.mark.parametrize("frame_count,expected_status", [(30, "passed"), (29, "failed")])
def test_real_decodable_h264_catches_one_missing_tail_frame(tmp_path, frame_count, expected_status):
    video = tmp_path / "cfr.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=white:s=360x640:r=30",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=mono:sample_rate=48000",
            "-frames:v",
            str(frame_count),
            "-t",
            "1",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-threads",
            "2",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "1",
            str(video),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    info = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(video)]
        )
    )
    frames = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "frame=best_effort_timestamp_time",
                "-of",
                "json",
                str(video),
            ]
        )
    )
    pts = [float(f["best_effort_timestamp_time"]) for f in frames["frames"]]
    assert len(pts) == frame_count
    # Prove the stream is fully decodable; this alone is insufficient for QC.
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-xerror", "-i", str(video), "-f", "null", "-"],
        check=True,
        capture_output=True,
        timeout=30,
    )
    checks = technical_checks(
        info,
        {"scenes": [{"duration": 1.0}]},
        {"kind": "preview", "aspect": "portrait", "silent": True},
        pts,
        {"input_tp": "-inf"},
        decoded=True,
    )
    by_name = {item["id"]: item for item in checks}
    assert by_name["full_decode"]["status"] == "passed"
    assert by_name["duration"]["status"] == "passed"
    assert by_name["fps"]["status"] == "passed"
    assert by_name["frame_timestamps"]["status"] == expected_status
