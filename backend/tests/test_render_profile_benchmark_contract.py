"""Fast safety contracts for C05's OPT-IN local benchmark (never run FullHD here)."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

FILE = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_render_profiles.py"
spec = importlib.util.spec_from_file_location("c05_render_profile_benchmark", FILE)
assert spec is not None and spec.loader is not None
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


def test_encoder_contract_1080p30_crf18_two_threads(tmp_path: Path) -> None:
    for aspect, (width, height) in benchmark.ASPECTS.items():
        assert aspect in ("portrait", "landscape")
        for preset in benchmark.PRESETS:
            command = benchmark.encode_args("ffmpeg", width, height, preset, tmp_path / "output.mp4")
            assert command[command.index("-preset") + 1] == preset
            assert command[command.index("-crf") + 1] == "18"
            assert command[command.index("-threads") + 1] == "2"
            assert command[command.index("-r") + 1] == "30"
            assert command[command.index("-pix_fmt") + 1] == "rgb24"
            assert command[command.index("-c:v") + 1] == "libx264"
            assert command[command.index("-movflags") + 1] == "+faststart"
            assert "-an" in command
            assert not any("http://" in a or "https://" in a for a in command)
            assert "medium" not in command if preset == "veryfast" else True


def test_raw_source_is_explicit_rgb24_not_reencoded_reference() -> None:
    src = benchmark.raw_source_args("ffmpeg", 1080, 1920, 5)
    assert src[src.index("-frames:v") + 1] == "150"
    assert src[src.index("-pix_fmt") + 1] == "rgb24"
    assert src[-1] == "pipe:1"
    assert "testsrc2=size=1080x1920:rate=30:duration=5" in src


@pytest.mark.parametrize("seconds", [0, 1, 4, 11, 60, True, 5.5, "5"])
def test_reject_unsafe_duration(seconds: object) -> None:
    with pytest.raises(benchmark.BenchmarkError, match="seconds"):
        benchmark.validate_config(seconds, 60, 1024)


@pytest.mark.parametrize("timeout,ram", [(14, 1024), (601, 1024), (60, 255), (60, 4097)])
def test_reject_unsafe_timeout_and_ram(timeout: int, ram: int) -> None:
    with pytest.raises(benchmark.BenchmarkError):
        benchmark.validate_config(5, timeout, ram)


def test_reject_unknown_preset_and_invalid_aspect(tmp_path: Path) -> None:
    with pytest.raises(benchmark.BenchmarkError, match="preset"):
        benchmark.encode_args("ffmpeg", 1080, 1920, "ultrafast", tmp_path / "a.mp4")
    with pytest.raises(benchmark.BenchmarkError, match="invalid aspect"):
        benchmark.benchmark(["4k"], 5, 60, 1024, tmp_path / "out")


def test_no_output_created_on_invalid_request(tmp_path: Path) -> None:
    target = tmp_path / "out"
    with pytest.raises(benchmark.BenchmarkError):
        benchmark.benchmark(["portrait"], 4, 60, 1024, target)
    assert not target.exists()


def test_reject_symlinked_output_dir(tmp_path: Path) -> None:
    actual = tmp_path / "real"
    actual.mkdir()
    symlink = tmp_path / "symlink"
    symlink.symlink_to(actual, target_is_directory=True)
    with pytest.raises(benchmark.BenchmarkError, match="unsafe"):
        benchmark.benchmark(["portrait"], 5, 60, 1024, symlink)


def make_ffprobe_metadata(frames: int = 30, *, fps: str = "30/1", codec: str = "h264") -> str:
    return json.dumps(
        {"streams": [{"codec_name": codec, "pix_fmt": "yuv420p", "width": 32, "height": 32,
                       "avg_frame_rate": fps, "nb_frames": str(frames)}],
         "frames": [{"best_effort_timestamp_time": f"{idx/30:.6f}"} for idx in range(frames)]}
    )


def test_probe_validates_real_timestamp_contract(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    commands: list[list[str]] = []
    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        return subprocess.CompletedProcess(args, 0, make_ffprobe_metadata() if args[0] == "ffprobe" else "", "")
    monkeypatch.setattr(benchmark.subprocess, "run", fake_run)
    check = benchmark.probe_video("ffprobe", "ffmpeg", tmp_path / "fake.mp4", 30, 32, 32, 5)
    assert check["full_decode"] == "PASS"
    assert check["frame_count"] == 30
    assert any("-xerror" in call for call in commands)


@pytest.mark.parametrize("metadata", [make_ffprobe_metadata(29), make_ffprobe_metadata(fps="60/1"),
                                       make_ffprobe_metadata(codec="hevc")])
def test_probe_fails_closed_for_wrong_frame_fps_codec(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, metadata: str,
) -> None:
    monkeypatch.setattr(benchmark.subprocess, "run", lambda args, **kwargs: subprocess.CompletedProcess(args, 0, metadata, ""))
    with pytest.raises(benchmark.BenchmarkError, match="wrong stream"):
        benchmark.probe_video("ffprobe", "ffmpeg", tmp_path / "invalid.mp4", 30, 32, 32, 5)


def test_probe_rejects_nonmonotonic_pts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    broken = json.loads(make_ffprobe_metadata())
    broken["frames"][8]["best_effort_timestamp_time"] = "0.000"
    monkeypatch.setattr(benchmark.subprocess, "run", lambda args, **kwargs: subprocess.CompletedProcess(args, 0, json.dumps(broken), ""))
    with pytest.raises(benchmark.BenchmarkError, match="non-CFR"):
        benchmark.probe_video("ffprobe", "ffmpeg", tmp_path / "invalid.mp4", 30, 32, 32, 5)


def test_probe_decode_failure_is_visible(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if args[0] == "ffprobe":
            return subprocess.CompletedProcess(args, 0, make_ffprobe_metadata(), "")
        return subprocess.CompletedProcess(args, 1, "", b"decoder failed")
    monkeypatch.setattr(benchmark.subprocess, "run", fake_run)
    with pytest.raises(benchmark.BenchmarkError, match="full decode failed"):
        benchmark.probe_video("ffprobe", "ffmpeg", tmp_path / "bad.mp4", 30, 32, 32, 5)


def test_stream_timeout_kills_child_processes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(benchmark, "_rss_kib", lambda _pid: 1)
    producer = [sys.executable, "-c", "import time; time.sleep(4)"]
    consumer = [sys.executable, "-c", "import sys; sys.stdin.buffer.read()"]
    with pytest.raises(benchmark.BenchmarkError, match="timeout"):
        benchmark._run_with_bounds(producer, consumer, max_seconds=1, max_rss_mib=256, expected_bytes=0)


def test_rss_breach_stops_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(benchmark, "_rss_kib", lambda _pid: 1024 * 1024)
    producer = [sys.executable, "-c", "import time; time.sleep(4)"]
    consumer = [sys.executable, "-c", "import sys; sys.stdin.buffer.read()"]
    with pytest.raises(benchmark.BenchmarkError, match="RSS exceeded"):
        benchmark._run_with_bounds(producer, consumer, max_seconds=2, max_rss_mib=256, expected_bytes=0)


def test_failure_cleans_staging_and_preserves_old_results(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output = tmp_path / "outputs"
    output.mkdir()
    existing = output / "previous-ok"
    existing.mkdir()
    (existing / "keep.json").write_text("last good")
    monkeypatch.setattr(benchmark, "_run_with_bounds", lambda *args, **kwargs: (_ for _ in ()).throw(benchmark.BenchmarkError("simulated encoder fault")))
    with pytest.raises(benchmark.BenchmarkError, match="encoder fault"):
        benchmark.benchmark(["portrait"], 5, 15, 512, output)
    assert sorted(p.name for p in output.iterdir()) == ["previous-ok"]
    assert (existing / "keep.json").read_text() == "last good"


@pytest.mark.skipif(os.environ.get("C05_TINY_FFMPEG") != "1", reason="only explicit opt-in tiny 32x32 FFmpeg integration")
def test_opt_in_tiny_rgb24_full_decode(tmp_path: Path) -> None:
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    assert ffmpeg and ffprobe
    expected = 32 * 32 * 3 * 30
    hashes = []
    for preset in benchmark.PRESETS:
        dest = tmp_path / f"{preset}.mp4"
        source = benchmark.raw_source_args(ffmpeg, 32, 32, 1)
        cmd = benchmark.encode_args(ffmpeg, 32, 32, preset, dest)
        record = benchmark._run_with_bounds(source, cmd, max_seconds=30, max_rss_mib=512, expected_bytes=expected)
        hashes.append(record["source_sha256"])
        assert dest.is_file()
        assert benchmark.probe_video(ffprobe, ffmpeg, dest, 30, 32, 32, 10)["full_decode"] == "PASS"
    assert hashes[0] == hashes[1]
