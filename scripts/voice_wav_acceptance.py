"""Reproducible 12-scene Vietnamese voiced WAV → 0.92x → MP4 acceptance test.

eSpeak is an engineering speech fixture, NOT approved VieNeu narration, and not
human listening, pronunciation, child-safety, or creator quality approval.
All generated media must stay outside Git.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import subprocess
import wave
from pathlib import Path
from uuid import uuid4

from audio_tempo import prepare_timeline

CUES = (
    ("Câu hỏi", "Vì sao áo ướt có thể khô?"),
    ("Nước bay hơi", "Nước trong vải dần bay hơi."),
    ("Không khí", "Không khí đưa hơi nước đi xa."),
    ("Gió", "Khi có gió, áo khô nhanh hơn."),
    ("Ánh nắng", "Trời nắng cung cấp thêm nhiệt."),
    ("Nhiệt độ", "Nhiệt giúp nước bay hơi nhanh."),
    ("Trải áo", "Trải rộng áo để đón gió."),
    ("Đừng gấp", "Đừng gấp áo khi còn ướt."),
    ("Bóng râm", "Trong bóng râm áo vẫn có thể khô."),
    ("Không cần sôi", "Không cần nước phải sôi mới bay hơi."),
    ("Quan sát", "Quan sát vạt áo khô dần từng giờ."),
    ("Tổng kết", "Bây giờ em đã hiểu vì sao áo khô."),
)
SPEECH_RATE = 95


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wav_info(path: Path) -> dict:
    with wave.open(str(path), "rb") as audio:
        assert audio.getnchannels() == 1
        assert audio.getsampwidth() == 2
        assert audio.getframerate() >= 8000
        assert audio.getnframes() > 0
        return {
            "rate": audio.getframerate(),
            "frames": audio.getnframes(),
            "duration": audio.getnframes() / audio.getframerate(),
        }


def create_wav_set(root: Path) -> dict:
    """Generate original Vietnamese utterances locally with source hashes."""
    tool = shutil.which("espeak")
    if not tool:
        raise RuntimeError("Install eSpeak for voiced Vietnamese WAV acceptance")
    root.mkdir(parents=True, exist_ok=True)
    sources = root / "raw-wav"
    sources.mkdir(exist_ok=True)
    records, scenes = [], []
    version = subprocess.check_output([tool, "--version"], text=True).strip()
    for i, (title, narration) in enumerate(CUES, start=1):
        output = sources / f"scene-{i:02d}.wav"
        subprocess.run(
            [tool, "-v", "vi", "-s", str(SPEECH_RATE), "-w", str(output), narration],
            check=True,
            capture_output=True,
            timeout=30,
        )
        info = wav_info(output)
        assert info["duration"] < 19.65
        records.append(
            {
                "file": str(output.relative_to(root)),
                "sha256": sha256(output),
                "narration": narration,
                "duration": info["duration"],
                "rate": info["rate"],
            }
        )
        scenes.append({"title": title, "narration": narration, "duration": 5})
    story = {"title": "Vì sao áo ướt lại khô? — mẫu kiểm thử", "scenes": scenes}
    (root / "story.json").write_text(
        json.dumps(story, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (root / "tts-provenance.json").write_text(
        json.dumps({"records": records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "source": "local eSpeak Vietnamese vi voice; not a human or approved VieNeu voice",
        "engine": version,
        "engine_rate": SPEECH_RATE,
        "license_note": "Internal QA fixture; review voice/tool rights before distributing",
        "approval": "NOT APPROVED — no listening, factual, safety or quality sign-off",
        "cue_count": len(CUES),
        "raw": records,
    }
    (root / "voice-source-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def verify_tempo(root: Path) -> dict:
    """Execute actual A04 path, check SHA/WAV/30fps/scene limits."""
    original = json.loads((root / "tts-provenance.json").read_text())
    story = prepare_timeline(root)
    timed = json.loads((root / "audio-timing.json").read_text())
    assert len(original["records"]) == len(timed) == len(story["scenes"]) == 12
    total = 0.0
    for source, segment, scene in zip(
        original["records"], timed, story["scenes"], strict=True
    ):
        raw = root / source["file"]
        processed = root / segment["file"]
        assert raw.is_file() and processed.is_file()
        assert sha256(raw) == source["sha256"] == segment["original_source_sha256"]
        assert sha256(processed) == segment["sha256"]
        assert segment["tempo"] == 0.92
        assert wav_info(processed)["rate"] == wav_info(raw)["rate"]
        assert abs(wav_info(processed)["duration"] - segment["duration"]) < 0.001
        assert abs(segment["duration"] - segment["trimmed_duration"] / 0.92) < 0.09
        assert scene["audio"] == segment["file"]
        assert scene["duration"] >= segment["duration"] + 0.09
        assert abs(scene["duration"] * 30 - round(scene["duration"] * 30)) < 1e-6
        total += scene["duration"]
    assert total <= 60
    return {"total_seconds": total, "files": len(timed), "tempo": 0.92}


def render_aspect(root: Path, aspect: str) -> dict:
    """Import 12 voiced WAVs with original illustrations and export real 1080p."""
    from auto_tool_video.domain import ExportInput, Scene
    from auto_tool_video.jobs import enqueue
    from auto_tool_video.media import import_asset, probe
    from auto_tool_video.render import render_job
    from auto_tool_video.store import Store
    from PIL import Image, ImageDraw

    width, height = (1080, 1920) if aspect == "portrait" else (1920, 1080)
    story = json.loads((root / "story.json").read_text())
    store = Store(root / f"studio-{aspect}")
    project = store.create(
        {
            "title": story["title"],
            "profile": "family",
            "platform": "shorts",
            "aspect": aspect,
            "narration": " ".join(s["narration"] for s in story["scenes"]),
        }
    )
    project["scenes"] = [
        Scene(
            title=s["title"], narration=s["narration"], duration=s["duration"]
        ).model_dump()
        for s in story["scenes"]
    ]
    project = store.save(project["id"], project)
    for i, scene in enumerate(project["scenes"]):
        # Unique original art per scene, no third-party media or downloaded assets.
        image_width, image_height = (
            (960, 1706) if aspect == "portrait" else (1280, 720)
        )
        canvas = Image.new("RGB", (image_width, image_height), "#f8faf8")
        draw = ImageDraw.Draw(canvas)
        w, h = canvas.size
        draw.rectangle(
            (w // 8, h // 3, w * 7 // 8, h * 2 // 3),
            fill=(115 + i * 7, 170 - i * 5, 195 + i * 3),
        )
        draw.ellipse(
            (w // 3, h // 5, w * 2 // 3, h // 2), fill="#ecce76"
        )
        draw.line(
            (w // 8, h * 3 // 4, w * 7 // 8, h * 3 // 4),
            fill="#254d3d",
            width=10,
        )
        data = io.BytesIO()
        canvas.save(data, "PNG")
        project = import_asset(
            store, project["id"], scene["id"], project["revision"], data.getvalue()
        )
        voice = root / story["scenes"][i]["audio"]
        project = import_asset(
            store, project["id"], scene["id"], project["revision"], voice.read_bytes()
        )
    request = ExportInput(
        revision=project["revision"],
        silent=False,
        aspect=aspect,
        kind="export",
        idempotency_key=str(uuid4()),
    )
    job = enqueue(store, project["id"], request)
    render_job(store, store.claim())
    done = store.get("jobs", job["id"])
    if done["state"] != "succeeded":
        raise AssertionError(f"Real narration MP4 export failed: {done}")
    source = store.asset_path(store.get("assets", done["result_id"]))
    dest = root / f"voice-review-{aspect}.mp4"
    shutil.copyfile(source, dest)
    metadata = probe(dest)
    video = next(s for s in metadata["streams"] if s["codec_type"] == "video")
    audio = next(s for s in metadata["streams"] if s["codec_type"] == "audio")
    assert (int(video["width"]), int(video["height"])) == (width, height)
    assert video["avg_frame_rate"] == "30/1"
    assert audio["codec_name"] == "aac"
    target = sum(s["duration"] for s in story["scenes"])
    observed = float(metadata["format"]["duration"])
    assert abs(observed - target) <= 0.12, (observed, target)
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-xerror",
            "-i", str(dest), "-f", "null", "-",
        ],
        check=True,
        capture_output=True,
        timeout=180,
    )
    report = {
        "aspect": aspect,
        "file": dest.name,
        "sha256": sha256(dest),
        "expected_duration": target,
        "measured_duration": observed,
        "resolution": [width, height],
        "video_codec": video["codec_name"],
        "audio_codec": audio["codec_name"],
        "full_decode": "PASS",
        "technical_quality": done.get("quality_report"),
        "narration_approval": "NOT APPROVED — eSpeak engineering voice",
    }
    (root / f"voice-report-{aspect}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    root = args.output_dir.resolve()
    create_wav_set(root)
    result = verify_tempo(root)
    print(json.dumps({"voice_fixture": result}, ensure_ascii=False), flush=True)
    if args.render:
        for aspect in ("portrait", "landscape"):
            report = render_aspect(root, aspect)
            summary = {k: v for k, v in report.items() if k != "technical_quality"}
            print(json.dumps({"render": summary}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
