"""Measured, pitch-preserving WAV tempo for the local review-video pipeline.

This is an opt-in build-time helper, not the studio's M3 TTS feature.
"""

from __future__ import annotations

import hashlib
import math
import os
import shutil
import subprocess
import wave
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

TEMPO = 0.92


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _wave_info(path: Path) -> tuple[int, int, float]:
    with wave.open(str(path), "rb") as stream:
        if (
            stream.getnchannels() != 1
            or stream.getsampwidth() != 2
            or stream.getcomptype() != "NONE"
            or stream.getframerate() < 8000
        ):
            raise ValueError(
                "Narration must be uncompressed mono 16-bit PCM WAV (>=8 kHz)."
            )
        frames = stream.getnframes()
        if frames <= 0:
            raise ValueError("Narration WAV contains no samples.")
        rate = stream.getframerate()
        return rate, frames, frames / rate


def stretch_narration(source: Path, output: Path, expected_sha256: str) -> dict:
    """Slow 0.92x with FFmpeg atempo, retaining original pitch and provenance.

    atempo uses time-domain overlap/add; changing WAV sample rate would change pitch.
    The new file is validated and only then atomically replaces the old output.
    """
    source, output = source.resolve(), output.resolve()
    if source == output:
        raise ValueError("Do not overwrite the source narration.")
    if _sha256(source) != expected_sha256:
        raise ValueError(
            "Narration source SHA256 changed; refusing to retime stale audio."
        )
    rate, samples, duration = _wave_info(source)
    if not math.isfinite(duration) or duration > 20:
        raise ValueError("Input narration is outside the 20-second scene limit.")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.stem}-{uuid4().hex}.wav")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-y",
                "-i",
                str(source),
                "-map",
                "0:a:0",
                "-vn",
                "-af",
                f"atempo={TEMPO:.2f}",
                "-ar",
                str(rate),
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(temporary),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
        output_rate, output_samples, output_duration = _wave_info(temporary)
        expected = duration / TEMPO
        # WSOLA overlap/add is not sample-exact; use measured duration instead.
        if output_rate != rate or abs(output_duration - expected) > max(
            0.06, expected * 0.03
        ):
            raise ValueError("Tempo output sample rate/duration failed verification.")
        if output_duration <= duration:
            raise ValueError("Slowed narration must be longer than the original.")
        result = {
            "file": str(output),
            "source_sha256": expected_sha256,
            "sha256": _sha256(temporary),
            "tempo": TEMPO,
            "pitch_policy": "preserved-by-ffmpeg-atempo-not-resampling",
            "filter": f"atempo={TEMPO:.2f}",
            "sample_rate": output_rate,
            "source_frames": samples,
            "output_frames": output_samples,
            "source_duration": duration,
            "duration": output_duration,
            "expected_duration": expected,
        }
        os.replace(temporary, output)
        return result
    finally:
        temporary.unlink(missing_ok=True)


def tight_audio(
    root: Path, record: dict, index: int, *, output_path: Path | None = None
) -> dict:
    """Keep source speech and small lead/tail margins before WSOLA retiming."""
    import numpy as np

    source = (root / record["file"]).resolve()
    if not source.is_relative_to(root.resolve()):
        raise ValueError("Voice input must reside inside the local review directory.")
    if _sha256(source) != record["sha256"]:
        raise ValueError("Narration source SHA256 mismatch.")
    rate, _, _ = _wave_info(source)
    with wave.open(str(source), "rb") as stream:
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
    start = max(0, int(active[0]) * window - round(rate * 0.06))
    end = min(len(samples), (int(active[-1]) + 1) * window + round(rate * 0.10))
    target = output_path or root / "audio-tight" / f"scene-{index + 1:02}.wav"
    target.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(target), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(samples[start:end].tobytes())
    return {
        "file": str(target.relative_to(root)),
        "source_file": record["file"],
        "source_sha256": record["sha256"],
        "sha256": _sha256(target),
        "trim_start_seconds": start / rate,
        "trim_end_seconds": (len(samples) - end) / rate,
        "duration": (end - start) / rate,
        "margins": "60ms lead/100ms tail around -52dB RMS activity; never trim internal pauses",
    }


def prepare_timeline(root: Path) -> dict:
    """Derive every scene's frame count from real retimed WAV output samples."""
    import json
    from copy import deepcopy

    root = root.resolve()
    original = json.loads((root / "story.json").read_text(encoding="utf-8"))
    tts = json.loads((root / "tts-provenance.json").read_text(encoding="utf-8"))
    story = deepcopy(original)
    scenes = story["scenes"]
    source_records = tts["records"]
    if not scenes or len(scenes) != len(source_records) or len(scenes) > 20:
        raise ValueError(
            "Narration source record count must match 1..20 storyboard scenes."
        )
    # Fail all mismatched inputs before generating derived WAVs.
    for scene, record in zip(scenes, source_records, strict=True):
        if scene["narration"] != record["narration"]:
            raise ValueError("Narration provenance does not match scene text.")
        source = (root / record["file"]).resolve()
        if not source.is_relative_to(root) or _sha256(source) != record["sha256"]:
            raise ValueError("Narration source SHA256 mismatch or unsafe path.")
    records = []
    duration_total = 0.0
    # Do not overwrite previous approved outputs until ALL scenes have passed.
    with TemporaryDirectory(prefix=".audio-stage-", dir=root) as temp_dir:
        stage = Path(temp_dir)
        changes = []
        for i, (scene, record) in enumerate(zip(scenes, source_records, strict=True)):
            tight_output = stage / "audio-tight" / f"scene-{i + 1:02}.wav"
            trimmed = tight_audio(root, record, i, output_path=tight_output)
            tempo_output = stage / "audio-tempo" / f"scene-{i + 1:02}.wav"
            stretched = stretch_narration(tight_output, tempo_output, trimmed["sha256"])
            measured = stretched["duration"]
            frame_count = max(30, math.ceil((measured + 0.10) * 30 - 0.0001))
            duration = frame_count / 30
            if measured > 19.65 or duration > 20 or duration_total + duration > 60:
                raise ValueError(
                    "Retimed narration exceeds the importer scene limit or 60-second preset."
                )
            old_duration = scene.get("duration")
            final_tight = root / "audio-tight" / tight_output.name
            final_tempo = root / "audio-tempo" / tempo_output.name
            scene["audio"] = str(final_tempo.relative_to(root))
            scene["duration"] = duration
            if scene.get("second_by_second") and old_duration != duration:
                scene["beat_plan_status"] = "needs_review"
            duration_total += duration
            records.append(
                {
                    **trimmed,
                    **stretched,
                    "file": str(final_tempo.relative_to(root)),
                    "trimmed_file": str(final_tight.relative_to(root)),
                    "original_source_sha256": trimmed["source_sha256"],
                    "trimmed_sha256": trimmed["sha256"],
                    "tempo_input_sha256": stretched["source_sha256"],
                    "source_sha256": trimmed["source_sha256"],
                    "trimmed_duration": trimmed["duration"],
                    "scene_duration": duration,
                    "scene_frames": frame_count,
                }
            )
            changes.extend(((tight_output, final_tight), (tempo_output, final_tempo)))

        staged_story = stage / "story.json"
        staged_timing = stage / "audio-timing.json"
        staged_story.write_text(
            json.dumps(story, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        staged_timing.write_text(
            json.dumps(records, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        changes.extend(
            (
                (staged_timing, root / "audio-timing.json"),
                (staged_story, root / "story.json"),
            )
        )
        # Save all previous destinations before publishing any new files.
        # Restore the previous media and metadata if publication fails midway.
        backups = {}
        for index, (_, destination) in enumerate(changes):
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                backup = stage / f"backup-{index:03}"
                shutil.copy2(destination, backup)
                backups[destination] = backup
        changed = []
        try:
            for staged, destination in changes:
                os.replace(staged, destination)
                changed.append(destination)
        except BaseException:
            for destination in reversed(changed):
                backup = backups.get(destination)
                if backup is None:
                    destination.unlink(missing_ok=True)
                else:
                    os.replace(backup, destination)
            raise
    print(
        "Timeline",
        round(duration_total, 3),
        "seconds; tempo 0.92x, WAV-measured",
        flush=True,
    )
    return story
