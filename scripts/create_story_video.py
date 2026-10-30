"""Narration-paced native motion sample through the real studio importer/renderer/QC."""

import argparse
import hashlib
import json
import math
import subprocess
import time
import wave
from pathlib import Path
from uuid import uuid4

import numpy as np
from auto_tool_video.domain import ExportInput, ProjectInput, Scene
from auto_tool_video.jobs import enqueue
from auto_tool_video.media import import_asset, probe
from auto_tool_video.quality import csv_sheet
from auto_tool_video.render import render_job
from auto_tool_video.store import Store
from create_review_video import contact_sheet
from PIL import Image
from science_story import Art


def tight_audio(root: Path, record: dict, index: int) -> dict:
    source = root / record["file"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == record["sha256"]
    with wave.open(str(source), "rb") as stream:
        assert stream.getnchannels() == 1 and stream.getsampwidth() == 2
        rate = stream.getframerate()
        samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2")
    window = max(1, round(rate * 0.01))
    energies = np.array(
        [
            np.sqrt(np.mean(samples[i : i + window].astype(float) ** 2)) / 32768
            for i in range(0, len(samples), window)
        ]
    )
    active = np.flatnonzero(energies > max(10 ** (-52 / 20), energies.max() * 0.006))
    if not len(active):
        raise ValueError("Narration contains no measurable speech.")
    start = max(0, active[0] * window - round(rate * 0.06))
    end = min(len(samples), (active[-1] + 1) * window + round(rate * 0.10))
    target = root / "audio-tight" / f"scene-{index + 1:02}.wav"
    target.parent.mkdir(exist_ok=True)
    with wave.open(str(target), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(samples[start:end].tobytes())
    return {
        "file": str(target.relative_to(root)),
        "source_file": record["file"],
        "source_sha256": record["sha256"],
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "trim_start_seconds": start / rate,
        "trim_end_seconds": (len(samples) - end) / rate,
        "duration": (end - start) / rate,
        "margins": "60ms lead/100ms tail around -52dB RMS activity; never trim internal pauses",
    }


def prepare_timeline(root: Path):
    story = json.loads((root / "story.json").read_text())
    tts = json.loads((root / "tts-provenance.json").read_text())
    records = []
    for i, (scene, record) in enumerate(
        zip(story["scenes"], tts["records"], strict=True)
    ):
        assert scene["narration"] == record["narration"]
        voice = tight_audio(root, record, i)
        records.append(voice)
        scene["audio"] = voice["file"]
        scene["duration"] = max(1, math.ceil((voice["duration"] + 0.10) * 30) / 30)
    if sum(s["duration"] for s in story["scenes"]) > 60:
        raise ValueError(
            "Narration exceeds the short preset; edit script rather than truncate speech."
        )
    (root / "story.json").write_text(
        json.dumps(story, ensure_ascii=False, indent=2) + "\n"
    )
    (root / "audio-timing.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        "Timeline",
        round(sum(s["duration"] for s in story["scenes"]), 3),
        "seconds; no fixed 4-second holds",
        flush=True,
    )
    return story


def source_clip(path: Path, art: Art, duration: float):
    frames = round(duration * 30)
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{art.width}x{art.height}",
        "-r",
        "30",
        "-i",
        "pipe:0",
        "-an",
        "-c:v",
        "libx264",
        "-crf",
        "12",
        "-preset",
        "veryfast",
        "-threads",
        "2",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for index in range(frames):
            process.stdin.write(art.frame(index / 30, duration).tobytes())
        process.stdin.close()
        error = process.stderr.read()
        if process.wait(timeout=90):
            raise RuntimeError(error.decode(errors="replace")[:500])
    except BaseException:
        process.kill()
        process.wait()
        raise
    if path.stat().st_size > 20 * 1024**2:
        raise ValueError(
            "Source clip exceeds importer limit; do not silently reduce resolution."
        )


def build(
    root: Path,
    aspect: str,
    stills: bool,
    reuse_clips: bool = False,
    rebuild_templates: tuple[str, ...] = (),
):
    story = json.loads((root / "story.json").read_text())
    width, height = (1080, 1920) if aspect == "portrait" else (1920, 1080)
    destination = root / f"clips-{aspect}"
    destination.mkdir(exist_ok=True)
    sheet = Image.new("RGB", (width // 4 * 4, height // 4 * 3), "white")
    started = time.monotonic()
    for i, scene in enumerate(story["scenes"]):
        art = Art(width, height, root / "art", scene["template"])
        still = art.frame(scene["duration"] * 0.5, scene["duration"])
        still.save(destination / f"scene-{i + 1:02}.png")
        sheet.paste(
            still.resize((width // 4, height // 4), Image.Resampling.LANCZOS),
            ((i % 4) * (width // 4), (i // 4) * (height // 4)),
        )
        if not stills:
            clip = destination / f"scene-{i + 1:02}.mp4"
            if reuse_clips and scene["template"] not in rebuild_templates:
                metadata = probe(clip)
                video = next(
                    s for s in metadata["streams"] if s["codec_type"] == "video"
                )
                assert (video["width"], video["height"]) == (width, height)
                assert video["avg_frame_rate"] == "30/1"
                assert int(video["nb_frames"]) == round(scene["duration"] * 30)
                assert clip.stat().st_size <= 20 * 1024**2
                continue
            print(
                f"Source {aspect} {i + 1}/{len(story['scenes'])}: {scene['template']} {scene['duration']:.3f}s",
                flush=True,
            )
            source_clip(clip, art, scene["duration"])
    sheet.save(root / f"art-contact-{aspect}.jpg", quality=95)
    if stills:
        return
    store = Store(root / f"studio-{aspect}")
    project = store.create(
        ProjectInput(
            title=story["title"],
            profile="family",
            aspect=aspect,
            narration="\n".join(s["narration"] for s in story["scenes"]),
        ).model_dump()
    )
    project = store.save(
        project["id"],
        {
            **project,
            "scenes": [
                Scene(
                    title=s["title"],
                    narration=s["narration"],
                    duration=s["duration"],
                    style="motion",
                    layout="full_frame",
                    visual_fit="cover",
                    transition="dissolve",
                    caption_style="accent" if i % 3 else "contrast",
                    caption_emphasis=s["caption_emphasis"],
                    visual_description=s["visual_description"],
                    reveal_order=s["reveal_order"],
                    role=s["role"],
                    motion_expectation="motion_required",
                ).model_dump()
                for i, s in enumerate(story["scenes"])
            ],
        },
    )
    for i, scene in enumerate(project["scenes"]):
        for path in [
            destination / f"scene-{i + 1:02}.mp4",
            root / story["scenes"][i]["audio"],
        ]:
            project = import_asset(
                store,
                project["id"],
                scene["id"],
                project["revision"],
                path.read_bytes(),
            )
    for scene, source in zip(project["scenes"], story["scenes"], strict=True):
        scene["duration"] = source["duration"]
    project = store.save(project["id"], project)
    job = enqueue(
        store,
        project["id"],
        ExportInput(
            revision=project["revision"], aspect=aspect, idempotency_key=str(uuid4())
        ),
    )
    render_start = time.monotonic()
    render_job(store, store.claim())
    done = store.get("jobs", job["id"])
    assert done["state"] == "succeeded"
    output = root / f"review-{aspect}.mp4"
    output.write_bytes(
        store.asset_path(store.get("assets", done["result_id"])).read_bytes()
    )
    contact_sheet(root, aspect, project["scenes"])
    report = {
        "aspect": aspect,
        "project": project,
        "video": output.name,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "probe": probe(output),
        "render_seconds": time.monotonic() - render_start,
        "source_and_render_seconds": time.monotonic() - started,
        "sources": "Original procedural Blender shirt cutouts + native supersampled science illustration clips; same preset local VieNeu; no external assets",
        "caption_timing": "scene-level pages, not forced alignment",
        "human_review": "pending creator listening and full playback",
    }
    (root / f"report-{aspect}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    (root / f"quality-report-{aspect}.json").write_text(
        json.dumps(done["quality_report"], ensure_ascii=False, indent=2) + "\n"
    )
    (root / f"qa-qc-sheet-{aspect}.csv").write_text(csv_sheet(done["quality_report"]))
    print(
        "Complete", aspect, output.stat().st_size, report["render_seconds"], flush=True
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--aspect", choices=["portrait", "landscape", "both"], default="both"
    )
    parser.add_argument("--timeline", action="store_true")
    parser.add_argument("--stills", action="store_true")
    parser.add_argument("--reuse-clips", action="store_true")
    parser.add_argument("--rebuild-template", action="append", default=[])
    args = parser.parse_args()
    root = args.output_dir.resolve()
    if args.timeline:
        prepare_timeline(root)
    else:
        for aspect in (
            ["portrait", "landscape"] if args.aspect == "both" else [args.aspect]
        ):
            build(
                root,
                aspect,
                args.stills,
                args.reuse_clips,
                tuple(args.rebuild_template),
            )
