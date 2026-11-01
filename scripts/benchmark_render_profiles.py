#!/usr/bin/env python3
"""Bounded OFFLINE 1080p30 x264 A/B harness; never changes production presets.

Explicit opt-in command only. In ordinary pytest, only contract/unit tests run.
RGB24 test frames are generated deterministically and streamed without raw-video
files; source SHA256 is compared across encodes of the same aspect ratio.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import threading
import time
import uuid

FPS = 30
CRF = 18
THREADS = 2
ASPECTS = {"portrait": (1080, 1920), "landscape": (1920, 1080)}
PRESETS = ("veryfast", "medium")
MAX_TOTAL_SECONDS = 10
MIN_SECONDS = 5
CHUNK_SIZE = 1024 * 1024


class BenchmarkError(RuntimeError):
    """A benchmark contract, validation or execution failure."""


def validate_config(seconds: int, timeout: int, max_rss_mib: int) -> None:
    if type(seconds) is not int or not MIN_SECONDS <= seconds <= MAX_TOTAL_SECONDS:
        raise BenchmarkError("seconds must be an integer in [5, 10]")
    if type(timeout) is not int or not 15 <= timeout <= 600:
        raise BenchmarkError("timeout must be an integer in [15, 600]")
    if type(max_rss_mib) is not int or not 256 <= max_rss_mib <= 4096:
        raise BenchmarkError("max-rss-mib must be an integer in [256, 4096]")


def raw_source_args(ffmpeg: str, width: int, height: int, seconds: int) -> list[str]:
    if width <= 0 or height <= 0 or seconds <= 0:
        raise BenchmarkError("invalid source dimensions/duration")
    return [
        ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-threads", "1",
        "-filter_threads", "1", "-f", "lavfi", "-i",
        f"testsrc2=size={width}x{height}:rate={FPS}:duration={seconds}",
        "-frames:v", str(FPS * seconds), "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1",
    ]


def encode_args(
    ffmpeg: str, width: int, height: int, preset: str, target: Path
) -> list[str]:
    if preset not in PRESETS:
        raise BenchmarkError("preset must be veryfast or medium")
    if width <= 0 or height <= 0:
        raise BenchmarkError("invalid encode dimensions")
    return [
        ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
        "-r", str(FPS), "-i", "pipe:0", "-map", "0:v:0", "-an", "-c:v", "libx264",
        "-preset", preset, "-crf", str(CRF), "-threads", str(THREADS),
        "-filter_threads", "1", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(target),
    ]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda: f.read(CHUNK_SIZE), b""):
            digest.update(buf)
    return digest.hexdigest()


def _rss_kib(pid: int) -> int | None:
    """Best effort resident *current* RSS; never silently ignore unavailable monitor."""
    if pid <= 0:
        return 0
    try:
        with open(f"/proc/{pid}/status", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
        # Exited Linux process may have already removed VmRSS.
        if os.path.isdir("/proc"):
            return 0
    except FileNotFoundError:
        if os.path.isdir("/proc"):
            return 0
    except (OSError, ValueError):
        pass
    try:
        result = subprocess.run(
            ["ps", "-o", "rss=", "-p", str(pid)],
            capture_output=True, text=True, timeout=2, check=False,
        )
        if result.returncode == 0:
            return int(result.stdout.strip().splitlines()[-1])
        if result.returncode == 1:
            return 0  # process already ended
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        pass
    return None


def _stop(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def _run_with_bounds(
    producer_argv: list[str], encoder_argv: list[str],
    *, max_seconds: int, max_rss_mib: int, expected_bytes: int,
) -> dict[str, object]:
    """Feed identical raw RGB stream to encoder; monitor elapsed/RSS and fail closed."""
    source_hash = hashlib.sha256()
    copied = 0
    feed_error: list[str] = []
    peak_kib = 0
    producer: subprocess.Popen[bytes] | None = None
    encoder: subprocess.Popen[bytes] | None = None
    started = time.perf_counter()
    with tempfile.TemporaryFile() as gen_stderr, tempfile.TemporaryFile() as enc_stderr:
        try:
            producer = subprocess.Popen(
                producer_argv, stdout=subprocess.PIPE, stderr=gen_stderr,
                stdin=subprocess.DEVNULL, start_new_session=True,
            )
            encoder = subprocess.Popen(
                encoder_argv, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=enc_stderr, start_new_session=True,
            )
            assert producer.stdout is not None and encoder.stdin is not None

            def feeder() -> None:
                nonlocal copied
                try:
                    while True:
                        piece = producer.stdout.read(CHUNK_SIZE)
                        if not piece:
                            break
                        source_hash.update(piece)
                        copied += len(piece)
                        if copied > expected_bytes:
                            raise BenchmarkError("generated RGB24 exceeds expected size")
                        encoder.stdin.write(piece)
                except (OSError, BrokenPipeError, BenchmarkError) as exc:
                    feed_error.append(str(exc))
                finally:
                    producer.stdout.close()
                    try:
                        encoder.stdin.close()
                    except OSError:
                        pass

            worker = threading.Thread(target=feeder, daemon=True)
            worker.start()
            while worker.is_alive() or producer.poll() is None or encoder.poll() is None:
                elapsed = time.perf_counter() - started
                if elapsed > max_seconds:
                    raise BenchmarkError(f"timeout after {max_seconds} seconds")
                p_rss = _rss_kib(producer.pid)
                e_rss = _rss_kib(encoder.pid)
                if p_rss is None or e_rss is None:
                    raise BenchmarkError("RSS monitoring unavailable; bounded run refused")
                peak_kib = max(peak_kib, p_rss + e_rss)
                if peak_kib > max_rss_mib * 1024:
                    raise BenchmarkError("combined generator+encoder RSS exceeded cap")
                worker.join(timeout=0.1)
            if feed_error:
                raise BenchmarkError("raw source stream failed: " + feed_error[0][:200])
            if producer.wait() != 0 or encoder.wait() != 0:
                gen_stderr.seek(0)
                enc_stderr.seek(0)
                detail = (gen_stderr.read(1536) + enc_stderr.read(1536)).decode("utf-8", "replace")
                raise BenchmarkError("FFmpeg producer/encoder failed: " + detail[:1200])
            if copied != expected_bytes:
                raise BenchmarkError(f"RGB24 stream truncated: {copied} != {expected_bytes}")
            return {
                "source_sha256": source_hash.hexdigest(),
                "source_bytes": copied,
                "pipeline_wall_seconds": round(time.perf_counter() - started, 4),
                "observed_peak_combined_rss_kib": peak_kib,
                "measurement_note": "generator + RGB24 pipe + encode/mux; NOT isolated encoder time",
            }
        finally:
            if producer is not None:
                _stop(producer)
            if encoder is not None:
                _stop(encoder)


def probe_video(ffprobe: str, ffmpeg: str, target: Path, frames: int, width: int, height: int, timeout: int) -> dict[str, object]:
    argv = [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_streams", "-show_frames", "-of", "json", str(target)]
    out = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    if out.returncode:
        raise BenchmarkError("ffprobe failed: " + out.stderr[:800])
    try:
        metadata = json.loads(out.stdout)
        video = metadata["streams"][0]
        stamps = [float(f["best_effort_timestamp_time"]) for f in metadata["frames"] if "best_effort_timestamp_time" in f]
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        raise BenchmarkError("invalid ffprobe metadata") from exc
    if (
        video.get("codec_name") != "h264" or video.get("pix_fmt") != "yuv420p"
        or int(video.get("width", 0)) != width or int(video.get("height", 0)) != height
        or video.get("avg_frame_rate") != "30/1"
        or len(stamps) != frames or int(video.get("nb_frames", 0)) != frames
    ):
        raise BenchmarkError("wrong stream codec/fps/size/frame count")
    if abs(stamps[0]) > 0.001 or any(abs((b - a) - 1 / FPS) > 0.001 for a, b in zip(stamps, stamps[1:])):
        raise BenchmarkError("non-CFR, non-monotonic or missing frame presentation timestamp")
    full_decode = subprocess.run(
        [ffmpeg, "-v", "error", "-xerror", "-i", str(target), "-map", "0:v:0", "-f", "null", "-"],
        capture_output=True, timeout=timeout, check=False,
    )
    if full_decode.returncode:
        raise BenchmarkError("full decode failed: " + full_decode.stderr.decode("utf-8", "replace")[:800])
    return {"codec": "h264", "pixel_format": "yuv420p", "fps": "30/1", "frame_count": frames,
            "pts_first": round(stamps[0], 6), "pts_last": round(stamps[-1], 6), "full_decode": "PASS", "audio": "NOT RUN (video-only fixture)"}


def benchmark(aspects: list[str], seconds: int, timeout: int, max_rss_mib: int, output_dir: Path) -> Path:
    validate_config(seconds, timeout, max_rss_mib)
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        raise BenchmarkError("ffmpeg and ffprobe must already be installed (no download)")
    if not aspects or any(a not in ASPECTS for a in aspects) or len(set(aspects)) != len(aspects):
        raise BenchmarkError("invalid aspect selection")
    if output_dir.is_symlink() or output_dir.exists() and not output_dir.is_dir():
        raise BenchmarkError("unsafe output-dir")
    output_dir.mkdir(parents=True, exist_ok=True)
    # One staging directory, removed on every error; preserve any older benchmark runs.
    with tempfile.TemporaryDirectory(prefix=".c05-pending-", dir=output_dir) as temporary:
        stage = Path(temporary)
        evidence: dict[str, object] = {
            "schema": "c05-x264-ab-v1", "status": "OBSERVED", "seconds": seconds, "fps": FPS,
            "crf": CRF, "encoder_threads": THREADS,
            "ffmpeg_version": subprocess.run([ffmpeg, "-version"], capture_output=True, text=True, timeout=10, check=True).stdout.splitlines()[0],
            "limits": {"run_timeout_seconds": timeout, "max_combined_rss_mib": max_rss_mib},
            "runs": [], "quality_human_g10": "NOT RUN", "vmaf": "NOT RUN", "psnr": "NOT RUN",
            "notes": "Deterministic synthetic video-only input; no real Studio compositor/audio/creator claims.",
        }
        run_results: list[dict[str, object]] = []
        for aspect in aspects:
            width, height = ASPECTS[aspect]
            source = raw_source_args(ffmpeg, width, height, seconds)
            expected = width * height * 3 * FPS * seconds
            aspect_source_hash: str | None = None
            for preset in PRESETS:
                video = stage / f"{aspect}-{preset}.mp4"
                encoder = encode_args(ffmpeg, width, height, preset, video)
                observed = _run_with_bounds(source, encoder, max_seconds=timeout, max_rss_mib=max_rss_mib, expected_bytes=expected)
                digest = str(observed["source_sha256"])
                if aspect_source_hash is not None and digest != aspect_source_hash:
                    raise BenchmarkError("RGB24 source differs between presets; comparison invalid")
                aspect_source_hash = digest
                inspect = probe_video(ffprobe, ffmpeg, video, FPS * seconds, width, height, timeout)
                result: dict[str, object] = {
                    "aspect": aspect, "dimensions": [width, height], "preset": preset,
                    "source_command": source, "encode_command": encoder[:-1] + [video.name],
                    "video_bytes": video.stat().st_size, "video_sha256": sha256_file(video),
                    **observed, **inspect,
                }
                run_results.append(result)
        evidence["runs"] = run_results
        (stage / "report.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        output = output_dir / f"x264-1080p30-{uuid.uuid4().hex[:12]}"
        stage.rename(output)
        return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OFFLINE bounded x264 A/B (opt-in, not CI)")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=5, help="5..10 seconds / aspect")
    parser.add_argument("--aspect", choices=("both", *ASPECTS.keys()), default="both")
    parser.add_argument("--timeout-seconds", type=int, default=180, help="15..600 per encode")
    parser.add_argument("--max-rss-mib", type=int, default=2048, help="256..4096 combined generator+encoder")
    args = parser.parse_args(argv)
    try:
        names = list(ASPECTS) if args.aspect == "both" else [args.aspect]
        result = benchmark(names, args.seconds, args.timeout_seconds, args.max_rss_mib, args.output_dir)
        print(json.dumps({"ok": True, "report": str(result / "report.json"), "directory": str(result)}))
        return 0
    except (BenchmarkError, subprocess.TimeoutExpired, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "reason": str(exc)[:500]}), file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
