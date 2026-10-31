"""Narration-paced native motion sample through the real studio importer/renderer/QC."""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from uuid import uuid4

from audio_tempo import prepare_timeline
from auto_tool_video.domain import ExportInput, ProjectInput, Scene
from auto_tool_video.jobs import enqueue
from auto_tool_video.media import import_asset, probe
from auto_tool_video.quality import csv_sheet
from auto_tool_video.render import render_job
from auto_tool_video.store import Store
from create_review_video import contact_sheet
from PIL import Image
from science_story import FONT, Art, beat_timeline


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


# The source MP4 cache is only an optimization; ambiguous provenance rebuilds.
# Bounded reads prevent a cache file or art asset from driving unbounded hashing.
_MAX_CLIP_BYTES = 20 * 1024**2
_MAX_INPUT_BYTES = 64 * 1024**2
_MAX_SCENE_BYTES = 1024 * 1024
_MAX_MANIFEST_BYTES = 4096


def _file_sha256(path: Path, limit: int) -> str:
    """Hash a regular local file with an enforced byte bound and no symlink trust."""
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Unsafe or missing cache input: {path.name}")
    if path.stat().st_size > limit:
        raise ValueError(f"Cache input exceeds size limit: {path.name}")
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            count += len(chunk)
            if count > limit:
                raise ValueError(f"Cache input exceeds size limit: {path.name}")
            digest.update(chunk)
    return digest.hexdigest()


def _source_clip_fingerprint(
    root: Path, still_path: Path, scene: dict, width: int, height: int
) -> tuple[str, bool]:
    """Bind cache to all current visual inputs and source/encoder implementation."""
    scene_bytes = json.dumps(
        scene, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    if len(scene_bytes) > _MAX_SCENE_BYTES:
        raise ValueError("Science scene exceeds cache fingerprint limit.")
    # Synthetic/test renderers can omit real artwork. Rendering is permitted,
    # but a missing visual input must NEVER authorize reuse of an old clip.
    artwork = (root / "art" / "wet.png", root / "art" / "dry.png", FONT)
    visual_hashes: list[str | None] = []
    for path in artwork:
        if path.is_symlink():
            raise ValueError("Unsafe science source artwork symlink.")
        visual_hashes.append(
            _file_sha256(path, _MAX_INPUT_BYTES) if path.exists() else None
        )
    sources = {
        "scene": hashlib.sha256(scene_bytes).hexdigest(),
        "wet_art": visual_hashes[0],
        "dry_art": visual_hashes[1],
        "preview_still": _file_sha256(still_path, _MAX_INPUT_BYTES),
        "font": visual_hashes[2],
        "art_source": _file_sha256(
            Path(__file__).with_name("science_story.py"), _MAX_INPUT_BYTES
        ),
        "encoder_source": _file_sha256(Path(__file__), _MAX_INPUT_BYTES),
    }
    contract = {
        "schema": 1,
        "resolution": [width, height],
        "fps": "30/1",
        "frames": round(scene["duration"] * 30),
        "sources": sources,
    }
    fingerprint = hashlib.sha256(
        json.dumps(contract, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return fingerprint, all(value is not None for value in visual_hashes)


def _source_clip_format_ok(
    clip: Path, width: int, height: int, duration: float
) -> bool:
    if clip.is_symlink():
        raise ValueError(f"Unsafe source clip symlink: {clip.name}")
    if not clip.is_file() or not 0 < clip.stat().st_size <= _MAX_CLIP_BYTES:
        return False
    metadata = probe(clip)
    video = next(
        stream for stream in metadata["streams"] if stream["codec_type"] == "video"
    )
    return (
        (video["width"], video["height"]) == (width, height)
        and video["avg_frame_rate"] == "30/1"
        and int(video["nb_frames"]) == round(duration * 30)
    )


def _clip_manifest(clip: Path) -> Path:
    # All output names are generated locally from scene index, never JSON paths.
    return clip.with_name(clip.name + ".provenance.json")


def _valid_source_clip_cache(
    clip: Path, fingerprint: str, width: int, height: int, duration: float
) -> bool:
    manifest = _clip_manifest(clip)
    if clip.is_symlink() or manifest.is_symlink():
        raise ValueError("Unsafe symlink in science clip cache.")
    if not manifest.is_file():
        return False
    try:
        size = manifest.stat().st_size
        if not 0 < size <= _MAX_MANIFEST_BYTES:
            return False
        record = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            return False
        if record.get("version") != 1 or record.get("source_sha256") != fingerprint:
            return False
        if not _source_clip_format_ok(clip, width, height, duration):
            return False
        return record == {
            "version": 1,
            "source_sha256": fingerprint,
            "clip_sha256": _file_sha256(clip, _MAX_CLIP_BYTES),
        }
    except (OSError, TypeError, ValueError, KeyError, StopIteration):
        # Old, corrupt or untrusted metadata must never authorize a cache hit.
        return False


def _save_clip_manifest(clip: Path, fingerprint: str) -> None:
    manifest = _clip_manifest(clip)
    if manifest.is_symlink():
        raise ValueError("Unsafe science cache manifest symlink.")
    record = {
        "version": 1,
        "source_sha256": fingerprint,
        "clip_sha256": _file_sha256(clip, _MAX_CLIP_BYTES),
    }
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=manifest.parent,
            prefix=".science-clip-",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(record, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, manifest)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _proposed_science_beats(scenes: list[dict], sources: list[dict]) -> list[dict]:
    """Derive review-only beat plans from imported scenes' FINAL measured durations.

    Validate every scene before returning any modifications. This preserves
    existing asset references/IDs and never overwrites a previous manual plan.
    The cues remain estimates, not forced-aligned word timings.
    """
    if not scenes or len(scenes) != len(sources):
        raise ValueError(
            "Science scene/source count mismatch; refusing to replace beats."
        )

    planned = []
    for index, (scene, source) in enumerate(zip(scenes, sources, strict=True)):
        required = (
            "title",
            "narration",
            "template",
            "visual_description",
            "caption_emphasis",
        )
        if not isinstance(source, dict) or any(
            not isinstance(source.get(field), str) for field in required
        ):
            raise ValueError(f"Science scene {index} is missing required source text.")
        # Template is source-only Art input, not a persisted Scene field.
        if (
            scene.get("title") != source["title"]
            or scene.get("narration") != source["narration"]
            or scene.get("visual_description") != source["visual_description"]
            or scene.get("caption_emphasis") != source["caption_emphasis"]
        ):
            raise ValueError(f"Science scene {index} no longer matches its source.")
        if scene.get("second_by_second") or scene.get("beat_plan_status") == "authored":
            raise ValueError(
                f"Science scene {index} already has a beat plan; refusing overwrite."
            )

        try:
            beats = beat_timeline(source, scene["duration"])
            validated = Scene.model_validate(
                {**scene, "second_by_second": beats, "beat_plan_status": "needs_review"}
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid science beat plan for scene {index}: {exc}"
            ) from exc
        planned.append(
            {
                **scene,
                "second_by_second": [
                    beat.model_dump() for beat in validated.second_by_second
                ],
                "beat_plan_status": "needs_review",
            }
        )
    return planned


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
    if destination.is_symlink():
        raise ValueError("Unsafe science clip cache directory symlink.")
    destination.mkdir(exist_ok=True)
    sheet = Image.new("RGB", (width // 4 * 4, height // 4 * 3), "white")
    started = time.monotonic()
    for i, scene in enumerate(story["scenes"]):
        art = Art(width, height, root / "art", scene["template"])
        still = art.frame(scene["duration"] * 0.5, scene["duration"])
        still_path = destination / f"scene-{i + 1:02}.png"
        if still_path.is_symlink():
            raise ValueError("Unsafe science source still symlink.")
        still.save(still_path)
        sheet.paste(
            still.resize((width // 4, height // 4), Image.Resampling.LANCZOS),
            ((i % 4) * (width // 4), (i // 4) * (height // 4)),
        )
        if not stills:
            clip = destination / f"scene-{i + 1:02}.mp4"
            if clip.is_symlink():
                raise ValueError("Unsafe source clip symlink.")
            fingerprint, cacheable = _source_clip_fingerprint(
                root, still_path, scene, width, height
            )
            manifest = _clip_manifest(clip)
            if manifest.is_symlink():
                raise ValueError("Unsafe science cache manifest symlink.")
            if (
                reuse_clips
                and cacheable
                and scene["template"] not in rebuild_templates
                and _valid_source_clip_cache(
                    clip, fingerprint, width, height, scene["duration"]
                )
            ):
                continue
            # A crash or failed render cannot leave an apparently valid old record.
            manifest.unlink(missing_ok=True)
            print(
                f"Source {aspect} {i + 1}/{len(story['scenes'])}: {scene['template']} {scene['duration']:.3f}s",
                flush=True,
            )
            source_clip(clip, art, scene["duration"])
            # Incomplete visual inputs permit render (e.g. synthetic fixtures),
            # never a reusable entry. Validate strictly before publishing cache.
            if cacheable:
                try:
                    rendered_ok = _source_clip_format_ok(
                        clip, width, height, scene["duration"]
                    )
                except (OSError, TypeError, ValueError, KeyError, StopIteration) as exc:
                    raise ValueError(
                        "Fresh science source clip could not be verified."
                    ) from exc
                if not rendered_ok:
                    raise ValueError(
                        "Fresh science source clip has invalid frame or codec metadata."
                    )
                _save_clip_manifest(clip, fingerprint)
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
    project["scenes"] = _proposed_science_beats(project["scenes"], story["scenes"])
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
