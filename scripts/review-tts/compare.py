"""Compare existing *real* VieNeu review exports without choosing a voice by ASR score.

Usage: python scripts/review-tts/compare.py --baseline /path/voice-a \
  --candidate /path/voice-b --output /path/voice-ab.json

Both inputs must have come from the pinned generate.py and verify.py runs,
with their original story, WAVs, model manifests and MP4 evidence intact.
Does not download models, call cloud services, or perform human listening.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import wave
from pathlib import Path

MAX_AUDIO = 24 * 1024**2
MAX_VIDEO = 200 * 1024**2


def _read_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024**2:
        raise ValueError(f"Missing/unsafe evidence: {path.name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"Invalid evidence type: {path.name}")
    return data


def _safe_path(root: Path, name: str, max_bytes: int) -> Path:
    if not isinstance(name, str) or not name:
        raise ValueError("Invalid evidence filename")
    path = root / name
    if (
        Path(name).is_absolute()
        or ".." in Path(name).parts
        or path.is_symlink()
        or not path.resolve().is_relative_to(root.resolve())
        or not path.is_file()
        or not 0 < path.stat().st_size <= max_bytes
    ):
        raise ValueError("Evidence path unavailable or unsafe")
    return path


def _hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_trial(root: Path) -> dict:
    story = _read_json(root / "story.json")
    provenance = _read_json(root / "tts-provenance.json")
    verification = _read_json(root / "verification.json")
    scenes = story.get("scenes")
    records = provenance.get("records")
    asr = verification.get("asr")
    models = provenance.get("models")
    if (
        not isinstance(scenes, list)
        or not 1 <= len(scenes) <= 20
        or not isinstance(records, list)
        or len(records) != len(scenes)
        or not isinstance(asr, list)
        or len(asr) != len(scenes)
        or provenance.get("sdk") != "vieneu"
        or not isinstance(provenance.get("voice"), str)
        or not provenance["voice"]
        or not isinstance(models, list)
        or not models
        or any(not isinstance(m, dict) or m.get("license") != "apache-2.0" for m in models)
    ):
        raise ValueError("Review is not a complete pinned VieNeu trial")
    trials = []
    for i, (scene, record, check) in enumerate(zip(scenes, records, asr, strict=True)):
        if (
            not isinstance(scene, dict)
            or not isinstance(record, dict)
            or not isinstance(check, dict)
            or record.get("narration") != scene.get("narration")
            or check.get("expected") != scene.get("narration")
            or check.get("scene") != i + 1
            or not isinstance(check.get("token_sequence_similarity"), (int, float))
            or not 0 <= check["token_sequence_similarity"] <= 1
        ):
            raise ValueError(f"Scene narration/ASR evidence mismatch at {i + 1}")
        name = record.get("file")
        if not isinstance(name, str) or not name.startswith("audio/"):
            raise ValueError("Trial WAV must remain under audio/")
        audio = _safe_path(root, name, MAX_AUDIO)
        if _hash(audio) != record.get("sha256"):
            raise ValueError(f"Modified VieNeu audio: scene {i + 1}")
        try:
            with wave.open(str(audio)) as wav:
                if (
                    wav.getframerate() != 48000
                    or wav.getnchannels() != 1
                    or wav.getsampwidth() != 2
                    or wav.getnframes() == 0
                ):
                    raise ValueError("Wrong VieNeu WAV format")
                duration = wav.getnframes() / wav.getframerate()
        except (wave.Error, EOFError) as exc:
            raise ValueError("Corrupt VieNeu WAV") from exc
        trials.append(
            {
                "scene": i + 1,
                "title": scene.get("title", ""),
                "narration": scene["narration"],
                "file": name,
                "sha256": record["sha256"],
                "duration": round(duration, 3),
                "asr": check.get("recognized", ""),
                "asr_token_similarity": round(check["token_sequence_similarity"], 3),
                "needs_listening_review": bool(check.get("needs_listening_review")),
            }
        )
    exports = []
    for aspect in ("portrait", "landscape"):
        name = f"review-{aspect}.mp4"
        path = _safe_path(root, name, MAX_VIDEO)
        rec = next(
            (f for f in verification.get("files", []) if f.get("aspect") == aspect),
            None,
        )
        if not isinstance(rec, dict) or rec.get("sha256") != _hash(path):
            raise ValueError(f"Missing/tampered verified MP4: {aspect}")
        if rec.get("full_decode") != "passed":
            raise ValueError(f"Unverified MP4 full decode: {aspect}")
        exports.append({"aspect": aspect, "sha256": rec["sha256"]})
    return {
        "voice": provenance["voice"],
        "sdk_version": provenance.get("version"),
        "models": [
            {"repository": m.get("repository"), "revision": m.get("revision"), "license": m["license"]}
            for m in models
        ],
        "scenes": trials,
        "exports": exports,
    }


def compare_trials(baseline: Path, candidate: Path) -> dict:
    left, right = load_trial(baseline), load_trial(candidate)
    if [(s["title"], s["narration"]) for s in left["scenes"]] != [
        (s["title"], s["narration"]) for s in right["scenes"]
    ]:
        raise ValueError("A/B requires identical scripts, scene order and titles")
    comparisons = []
    for a, b in zip(left["scenes"], right["scenes"], strict=True):
        comparisons.append(
            {
                "scene": a["scene"],
                "narration": a["narration"],
                "baseline_wav_sha256": a["sha256"],
                "candidate_wav_sha256": b["sha256"],
                "baseline_asr_similarity": a["asr_token_similarity"],
                "candidate_asr_similarity": b["asr_token_similarity"],
                "candidate_minus_baseline_asr": round(
                    b["asr_token_similarity"] - a["asr_token_similarity"], 3
                ),
                "baseline_duration": a["duration"],
                "candidate_duration": b["duration"],
                "manual_listening": {
                    "pronunciation": None,
                    "naturalness": None,
                    "pace": None,
                    "regional_accent": None,
                    "notes": "",
                },
            }
        )
    return {
        "source": "VieNeu pinned local ONNX CPU trials (not eSpeak)",
        "baseline": {"voice": left["voice"], "models": left["models"], "exports": left["exports"]},
        "candidate": {
            "voice": right["voice"],
            "models": right["models"],
            "exports": right["exports"],
        },
        "same_story": True,
        "scenes": comparisons,
        "winner": None,
        "human_listening": "PENDING — ASR scores cannot replace listening and creator review",
        "license_review": "Model notices verified; speaker/asset rights still require review",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Never overwrite an existing listening comparison")
    report = compare_trials(args.baseline, args.candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Compared {len(report['scenes'])} scenes; human listening PENDING")


if __name__ == "__main__":
    main()
