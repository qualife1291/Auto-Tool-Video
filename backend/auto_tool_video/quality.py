"""Local post-render QC and creator decisions. No learned benchmark scores or network calls."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import subprocess
import tempfile
import time
from collections.abc import Callable
from fractions import Fraction
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .domain import QualityReviewInput
from .media import probe
from .store import DomainError, Store, now

POLICY = "local-qc-1"
CRITERIA = {
    "prompt_alignment": (
        "Khớp kịch bản / prompt",
        "Đúng vật thể, màu, số lượng và hành động cốt lõi.",
        "Sửa brief/cảnh nếu sai thông điệp; không giữ chỉ vì hình đẹp.",
    ),
    "motion_smoothness": (
        "Chuyển động mượt",
        "Camera/vật thể không giật gây mất tập trung.",
        "Kiểm mốc cảnh báo ở tốc độ thật; dựng lại chuyển động nếu lỗi rõ.",
    ),
    "temporal_consistency": (
        "Nhất quán thời gian",
        "Chủ thể, trang phục và nền ổn định theo ý đồ.",
        "Thay clip/keyframe lỗi; kiểm reference và continuity trước xuất lại.",
    ),
    "physical_plausibility": (
        "Logic vật lý",
        "Hành động và quan hệ nhân quả đúng với phong cách đã chọn.",
        "Sửa mô hình/hành động; dùng template kiểm được cho giải thích khoa học.",
    ),
    "technical_quality": (
        "Chất lượng kỹ thuật",
        "Đủ nét, không vỡ khối/răng cưa, chữ rõ và phát lại tốt.",
        "Kiểm nguồn gốc và encode; upscale không khôi phục chi tiết bị thiếu.",
    ),
}
BENCHMARKS = [
    {
        "name": "VBench / VBench-2.0",
        "status": "not_run",
        "reason": "Chưa cài runtime/checkpoint benchmark; local proxies không phải VBench scores.",
    },
    {
        "name": "AIGCBench",
        "status": "not_run",
        "reason": "Chưa chạy bộ I2V/reference dataset và learned metrics chính thức.",
    },
]


def sha256_file(path: Path, check: Callable[[], None] = lambda: None) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            check()
            digest.update(chunk)
    return digest.hexdigest()


def provenance_for(store: Store, job: dict, check: Callable[[], None] = lambda: None) -> dict:
    inputs = []
    seen = set()
    for scene in job["snapshot"]["scenes"]:
        for field in ("image_id", "audio_id"):
            identifier = scene.get(field)
            if not identifier or identifier in seen:
                continue
            seen.add(identifier)
            asset = store.get("assets", identifier)
            provenance = asset.get("provenance", {})
            inputs.append(
                {
                    "asset_id": identifier,
                    "kind": asset["kind"],
                    "source": asset.get("source", "unknown"),
                    "stored_sha256": sha256_file(store.asset_path(asset), check),
                    "import_sha256": asset.get("sha256"),
                    "provider": {
                        key: provenance[key]
                        for key in (
                            "provider",
                            "model",
                            "digest",
                            "checkpoint",
                            "workflow_sha256",
                            "seed",
                        )
                        if key in provenance
                    },
                }
            )
    known_ai = any(item["source"] == "comfyui-local" for item in inputs)
    return {
        "snapshot_sha256": hashlib.sha256(
            json.dumps(job["snapshot"], sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
        "inputs": inputs,
        "known_ai_usage": known_ai,
        "origin": "ai_assisted_known" if known_ai else "unverified",
        "marking": "Unsigned metadata and local sidecar; no C2PA signature or robust watermark; platforms may strip metadata.",
        "legal_compliance_certified": False,
    }


def _run(argv: list[str], check: Callable[[], None], timeout: float = 300) -> tuple[int, str, str]:
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen(argv, stdout=stdout, stderr=stderr)
        started = time.monotonic()
        try:
            while process.poll() is None:
                check()
                if stdout.tell() > 2 * 1024**2 or stderr.tell() > 2 * 1024**2:
                    raise RuntimeError("Phản hồi QC vượt giới hạn.")
                if time.monotonic() - started > timeout:
                    raise RuntimeError("QC vượt giới hạn thời gian.")
                time.sleep(0.05)
            check()
            values = []
            for stream in (stdout, stderr):
                if stream.tell() > 2 * 1024**2:
                    raise RuntimeError("Phản hồi QC vượt giới hạn.")
                stream.seek(0)
                values.append(stream.read().decode("utf-8", errors="replace"))
            return process.returncode, values[0], values[1]
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)


def _number(value: Any) -> float | None:
    try:
        result = float(Fraction(str(value)))
        return result if math.isfinite(result) else None
    except (ValueError, TypeError, ZeroDivisionError, OverflowError):
        return None


def technical_checks(
    info: dict, snapshot: dict, options: dict, pts: list[float], loudness: dict, decoded: bool
) -> list[dict]:
    video: dict[str, Any] = next(
        (s for s in info.get("streams", []) if s.get("codec_type") == "video"), {}
    )
    audio: dict[str, Any] = next(
        (s for s in info.get("streams", []) if s.get("codec_type") == "audio"), {}
    )
    landscape = options.get("aspect") == "landscape"
    target = (
        ((640, 360) if landscape else (360, 640))
        if options["kind"] == "preview"
        else ((1920, 1080) if landscape else (1080, 1920))
    )
    duration = sum(math.ceil(s["duration"] * 30) / 30 for s in snapshot["scenes"])
    checks = []

    def add(identifier: str, passed: bool, actual: Any, message: str):
        checks.append(
            {
                "id": identifier,
                "status": "passed" if passed else "failed",
                "actual": actual,
                "message": message,
            }
        )

    add("full_decode", decoded, decoded, "Giải mã toàn bộ video và audio không lỗi.")
    dimensions = [video.get("width"), video.get("height")]
    add(
        "dimensions",
        tuple(dimensions) == target,
        dimensions,
        f"Canvas đích {target[0]}×{target[1]}, không suy từ nhãn HD.",
    )
    add(
        "video_codec",
        video.get("codec_name") == "h264" and video.get("pix_fmt") == "yuv420p",
        [video.get("codec_name"), video.get("pix_fmt")],
        "H.264/yuv420p.",
    )
    fps = _number(video.get("r_frame_rate"))
    add("fps", fps is not None and abs(fps - 30) < 0.001, fps, "Preset 30fps.")
    valid_pts = len(pts) > 1 and all(math.isfinite(t) for t in pts)
    gaps = np.diff(pts) if valid_pts else np.array([])
    cfr = bool(valid_pts and np.all(np.abs(gaps - 1 / 30) <= 0.002))
    add(
        "frame_timestamps",
        cfr,
        {"frames": len(pts), "max_gap_seconds": float(gaps.max()) if len(gaps) else None},
        "PTS tăng đều; frame gap/repeat timestamp không bị che bằng average fps.",
    )
    actual_duration = _number(info.get("format", {}).get("duration"))
    add(
        "duration",
        actual_duration is not None and abs(actual_duration - duration) <= 0.1,
        actual_duration,
        f"Thời lượng theo snapshot {duration:.3f}s ±0,1s.",
    )
    vd, ad = _number(video.get("duration")), _number(audio.get("duration"))
    add(
        "av_duration",
        vd is not None and ad is not None and abs(vd - ad) <= 0.1,
        {"video": vd, "audio": ad},
        "Lệch thời lượng audio/video tối đa100ms; không chứng nhận lip-sync.",
    )
    add(
        "audio_codec",
        audio.get("codec_name") == "aac" and str(audio.get("sample_rate")) == "48000",
        [audio.get("codec_name"), audio.get("sample_rate")],
        "AAC48kHz, có track thật.",
    )
    integrated, peak = _number(loudness.get("input_i")), _number(loudness.get("input_tp"))
    if options.get("silent"):
        # Silence is explicit; do not count an unmeasurable stream as narration passing LUFS.
        silent = str(loudness.get("input_tp", "")).lower() == "-inf" or (
            peak is not None and peak <= -60
        )
        add(
            "intentional_silence",
            silent,
            peak,
            "Creator chủ động chọn không lời; track không có âm thanh ngoài ý muốn.",
        )
        checks.append(
            {
                "id": "narration_loudness",
                "status": "not_applicable",
                "actual": None,
                "message": "Silent mode; không chấm −inf như lời đọc đạt.",
            }
        )
    else:
        add(
            "narration_loudness",
            integrated is not None and -17 <= integrated <= -15,
            integrated,
            "Integrated−16LUFS±1, đo input_i trên thành phẩm.",
        )
        add("true_peak", peak is not None and peak <= -1, peak, "True peak<=−1dBTP sau AAC.")
    return checks


def scene_signals(rows: list[dict], scene: dict, start: float, scene_number: int) -> dict:
    findings = []
    luma = [row["luma"] for row in rows]
    for i in range(1, len(rows) - 1):
        if (
            abs(luma[i] - luma[i - 1]) >= 35
            and abs(luma[i] - luma[i + 1]) >= 35
            and abs(luma[i - 1] - luma[i + 1]) <= 8
        ):
            findings.append(
                {
                    "id": f"flash-{scene_number}-{i}",
                    "kind": "luminance_flash",
                    "timestamp": round(start + i / 30, 3),
                    "scene": scene_number,
                    "message": "Biến động sáng ngắn trong vùng minh họa; xem lại ở tốc độ thật.",
                    "remedy": "Kiểm frame lân cận và chuyển cảnh; đây không phải phép kiểm an toàn nhạy sáng.",
                }
            )
    run, longest, longest_start = 0, 0, 0
    for i, row in enumerate(rows):
        active = (
            0.15
            <= i / 30
            <= (
                scene["duration"] * 0.65
                if scene.get("style") == "whiteboard"
                else scene["duration"] - 0.15
            )
        )
        run = run + 1 if active and row["delta"] is not None and row["delta"] <= 0.08 else 0
        if run > longest:
            longest, longest_start = run, i - run + 1
    if scene.get("motion_expectation", "allow_static") == "motion_required" and longest / 30 >= 0.5:
        findings.append(
            {
                "id": f"freeze-{scene_number}-{longest_start}",
                "kind": "possible_freeze",
                "timestamp": round(start + longest_start / 30, 3),
                "scene": scene_number,
                "message": f"Hình gần lặp {longest / 30:.2f}s trong cảnh yêu cầu chuyển động.",
                "remedy": "Kiểm đây có phải hold chủ đích; thay clip/chuyển động nếu gây mất tập trung.",
            }
        )
    sharpness = [row["sharpness"] for row in rows]
    deltas = [row["delta"] for row in rows if row["delta"] is not None]
    return {
        "scene": scene_number,
        "frames": len(rows),
        "motion_expectation": scene.get("motion_expectation", "allow_static"),
        "longest_active_near_repeat_seconds": round(longest / 30, 3),
        "mean_pixel_delta": float(np.mean(deltas)) if deltas else None,
        "laplacian_variance_p05": float(np.percentile(sharpness, 5)) if sharpness else None,
        "findings": findings[:20],
    }


def scan_video(path: Path, scenes: list[dict], check: Callable[[], None]) -> dict:
    capture = cv2.VideoCapture(str(path))
    metrics = []
    try:
        frame_number = 0
        for number, scene in enumerate(scenes, 1):
            rows, previous = [], None
            start = frame_number / 30
            for _ in range(math.ceil(scene["duration"] * 30)):
                check()
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("Không đủ frame để QC theo snapshot.")
                height, width = frame.shape[:2]
                box = (
                    (240 / 1920, 230 / 1080, 1440 / 1920, 580 / 1080)
                    if width > height
                    else (90 / 1080, 420 / 1920, 810 / 1080, 850 / 1920)
                )
                x, y, w, h = box
                roi = frame[
                    round(y * height) : round((y + h) * height),
                    round(x * width) : round((x + w) * width),
                ]
                gray = cv2.resize(
                    cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), (160, 160), interpolation=cv2.INTER_AREA
                )
                rows.append(
                    {
                        "luma": float(gray.mean()),
                        "sharpness": float(cv2.Laplacian(gray, cv2.CV_32F).var()),
                        "delta": float(np.abs(gray.astype(float) - previous).mean())
                        if previous is not None
                        else None,
                    }
                )
                previous = gray.astype(float)
                frame_number += 1
                if frame_number > 6000:
                    raise RuntimeError("QC vượt giới hạn frame.")
            metrics.append(scene_signals(rows, scene, start, number))
    finally:
        capture.release()
    return {
        "method": "Every frame, illustration ROI resized to160×160 grayscale; pixel/luminance proxies, not VBench or semantic/physics scores.",
        "thresholds": {
            "isolated_luma_jump": 35,
            "return_tolerance": 8,
            "near_repeat_mae": 0.08,
            "motion_required_freeze_seconds": 0.5,
        },
        "sharpness_policy": "Laplacian descriptive only: line art and soft backgrounds do not have a universal blur threshold.",
        "scenes": metrics,
        "findings": [item for metric in metrics for item in metric["findings"]],
    }


def inspect_video(
    path: Path,
    snapshot: dict,
    options: dict,
    provenance: dict | None = None,
    check: Callable[[], None] = lambda: None,
) -> dict:
    report: dict[str, Any] = {
        "schema_version": 1,
        "policy_version": POLICY,
        "created_at": now(),
        "artifact": {
            "sha256": sha256_file(path, check),
            "bytes": path.stat().st_size,
            "duration": sum(math.ceil(s["duration"] * 30) / 30 for s in snapshot["scenes"]),
            "silent": bool(options.get("silent")),
            "captions": bool(options.get("captions")),
        },
        "provenance": provenance
        or {"known_ai_usage": False, "origin": "unverified", "legal_compliance_certified": False},
        "benchmarks": BENCHMARKS,
        "expected_scenes": [
            {
                key: scene.get(key, "")
                for key in (
                    "id",
                    "title",
                    "narration",
                    "image_prompt",
                    "visual_description",
                    "style",
                    "motion_expectation",
                    "image_id",
                )
            }
            for scene in snapshot["scenes"]
        ],
        "manual_review": None,
        "review_revision": 0,
    }
    try:
        info = probe(path)
        report["artifact"].update(
            aspect=options.get("aspect", "portrait"),
            kind=options["kind"],
            viewer_profile=snapshot.get("profile", "unknown"),
        )
        argv = [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-xerror",
            "-threads",
            "2",
            "-i",
            str(path),
            "-af",
            "loudnorm=I=-16:TP=-1:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ]
        code, _, error = _run(argv, check)
        loudness = (
            json.JSONDecoder().raw_decode(error[error.rfind("{") :])[0] if "{" in error else {}
        )
        pts_code, data, _ = _run(
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
                str(path),
            ],
            check,
        )
        pts = (
            [
                float(frame["best_effort_timestamp_time"])
                for frame in json.loads(data).get("frames", [])
            ]
            if pts_code == 0
            else []
        )
        checks = technical_checks(info, snapshot, options, pts, loudness, code == 0)
        report["technical"] = {
            "status": "failed" if any(c["status"] == "failed" for c in checks) else "passed",
            "checks": checks,
        }
        report["signals"] = (
            scan_video(path, snapshot["scenes"], check)
            if code == 0
            else {"findings": [], "not_run_reason": "Decode failed."}
        )
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError, DomainError):
        report["technical"] = {
            "status": "failed",
            "checks": [
                {
                    "id": "analysis_complete",
                    "status": "failed",
                    "actual": None,
                    "message": "Không hoàn thành QC. Kiểm tệp, snapshot, FFmpeg/FFprobe và tài nguyên rồi chạy lại.",
                }
            ],
        }
        report["signals"] = {"findings": [], "not_run_reason": "Technical analysis incomplete."}
    report["gate"] = review_decision(report, None)
    return report


def review_decision(report: dict, review: dict | None) -> dict:
    if report["technical"]["status"] != "passed":
        return {
            "status": "blocked",
            "reasons": ["Cổng kỹ thuật chưa đạt; sửa đầu vào/encode và xuất lại."],
        }
    values = (review or {}).get("criteria", {})
    rejected = [
        CRITERIA[key][0]
        for key, value in values.items()
        if value.get("critical") or (value.get("score") is not None and value["score"] <= 2)
    ]
    if rejected:
        return {"status": "rejected", "reasons": rejected}
    revised = [CRITERIA[key][0] for key, value in values.items() if value.get("score") == 3]
    if revised:
        return {"status": "revise", "reasons": revised}
    missing = [CRITERIA[key][0] for key in CRITERIA if values.get(key, {}).get("score") is None]
    for key, label in [
        ("watched_full", "Xem hết video ở tốc độ thật"),
        ("checked_facts_age", "Kiểm kiến thức và độ tuổi"),
        ("disclosure_reviewed", "Review nguồn gốc và nhãn AI"),
    ]:
        if not review or not review.get(key):
            missing.append(label)
    if not report["artifact"]["silent"] and (not review or not review.get("listened_audio")):
        missing.append("Nghe audio trong thành phẩm")
    if report["artifact"]["captions"] and (not review or not review.get("checked_captions")):
        missing.append("Kiểm phụ đề và dấu tiếng Việt")
    if not review or review.get("content_origin", "unknown") == "unknown":
        missing.append("Xác nhận nguồn gốc nội dung")
    known = {f["id"] for f in report.get("signals", {}).get("findings", [])}
    if known - set((review or {}).get("acknowledged_findings", [])):
        missing.append("Xem và xác nhận các cảnh báo tự động")
    return {"status": "pending_review" if missing else "approved", "reasons": missing}


def quality_job(store: Store, project_id: str, job_id: str, conn=None) -> dict:
    job = store.get("jobs", job_id, conn)
    if job["project_id"] != project_id or job["options"]["kind"] not in {"preview", "export"}:
        raise DomainError("NOT_FOUND", "Không tìm thấy bản xuất của dự án này.", 404)
    return job


def quality_payload(job: dict) -> dict:
    return job.get("quality_report") or {
        "schema_version": 1,
        "policy_version": POLICY,
        "gate": {
            "status": "unavailable",
            "reasons": ["Bản xuất này chưa có QC; dựng lại để chạy kiểm định mới."],
        },
        "benchmarks": BENCHMARKS,
    }


def save_review(store: Store, project_id: str, job_id: str, request: QualityReviewInput) -> dict:
    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        job = quality_job(store, project_id, job_id, conn)
        report = job.get("quality_report")
        if job["state"] != "succeeded" or not report:
            raise DomainError("VALIDATION_ERROR", "Chọn bản xuất thành công có báo cáo QC.")
        if request.review_revision != report["review_revision"]:
            raise DomainError(
                "REVISION_CONFLICT", "Phiếu đã đổi ở nơi khác. Tải lại phiếu trước lưu.", 409
            )
        asset = store.get("assets", job["result_id"], conn)
        if (
            request.video_sha256 != report["artifact"]["sha256"]
            or sha256_file(store.asset_path(asset)) != request.video_sha256
        ):
            raise DomainError(
                "REVISION_CONFLICT", "File/hash không khớp bản được kiểm. Hãy xuất/kiểm lại.", 409
            )
        if any(
            value.at_seconds is not None and value.at_seconds > report["artifact"]["duration"]
            for value in request.criteria.values()
        ):
            raise DomainError("VALIDATION_ERROR", "Mốc lỗi phải nằm trong video.")
        known = {f["id"] for f in report.get("signals", {}).get("findings", [])}
        if set(request.acknowledged_findings) - known:
            raise DomainError("VALIDATION_ERROR", "Cảnh báo đã thay đổi; tải lại phiếu.")
        if report["provenance"].get("known_ai_usage") and request.content_origin == "no_ai":
            raise DomainError(
                "VALIDATION_ERROR", "Có nguồn AI đã biết; kiểm lại khai báo nguồn gốc."
            )
        review = {
            **request.model_dump(exclude={"review_revision", "video_sha256"}),
            "saved_at": now(),
        }
        report.update(
            manual_review=review,
            review_revision=report["review_revision"] + 1,
            gate=review_decision(report, review),
        )
        conn.execute("UPDATE jobs SET data=? WHERE id=?", (json.dumps(job), job_id))
    return report


def csv_sheet(report: dict) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)

    def safe(value: Any) -> str:
        text = str(value) if value is not None else ""
        return (
            "'" + text
            if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n"))
            else text
        )

    writer.writerow(
        ["Video SHA256", report.get("artifact", {}).get("sha256", "unavailable"), "Policy", POLICY]
    )
    writer.writerow(
        ["Tiêu chí", "Điểm 1–5", "Critical", "Giây", "Lỗi / bằng chứng", "Tín hiệu đạt", "Xử lý"]
    )
    review = report.get("manual_review") or {}
    for key, (label, signal, remedy) in CRITERIA.items():
        row = review.get("criteria", {}).get(key, {})
        writer.writerow(
            [
                safe(value)
                for value in [
                    label,
                    row.get("score"),
                    row.get("critical", False),
                    row.get("at_seconds"),
                    row.get("note", ""),
                    signal,
                    remedy,
                ]
            ]
        )
    writer.writerow(
        ["Người duyệt", safe(review.get("reviewer", "")), "Gate", report["gate"]["status"]]
    )
    writer.writerow(
        [
            "Lưu lúc (UTC)",
            review.get("saved_at", ""),
            "Phiên bản phiếu",
            report.get("review_revision", 0),
        ]
    )
    writer.writerow(
        [
            "Aspect",
            report.get("artifact", {}).get("aspect", ""),
            "Nhóm xem",
            report.get("artifact", {}).get("viewer_profile", ""),
        ]
    )
    writer.writerow(
        [
            "Quy tắc",
            "Critical hoặc1–2: loại;3: sửa;4–5 chỉ duyệt khi đủ kiểm thủ công và kỹ thuật. Không lấy trung bình.",
        ]
    )
    return "\ufeff" + output.getvalue()
