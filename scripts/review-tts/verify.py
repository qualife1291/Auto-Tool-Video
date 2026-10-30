"""Measure the actual exports; ASR is an aid, not a human listening verdict."""

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import soundfile as sf
from faster_whisper import WhisperModel
from generate import prepare


def normalized(text):
    return re.findall(r"\w+", text.casefold())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.output_dir.resolve()
    results = []
    for aspect, dimensions in [("portrait", (1080, 1920)), ("landscape", (1920, 1080))]:
        path = root / f"review-{aspect}.mp4"
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        info = json.loads(result.stdout)
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
        assert (video["width"], video["height"]) == dimensions
        assert video["codec_name"] == "h264" and video["avg_frame_rate"] == "30/1"
        assert audio["codec_name"] == "aac" and audio["sample_rate"] == "48000"
        assert abs(float(audio["duration"]) - float(video["duration"])) < 0.1
        subprocess.run(
            ["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"],
            capture_output=True,
            check=True,
            timeout=120,
        )
        measured = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostats",
                "-i",
                str(path),
                "-vn",
                "-af",
                "loudnorm=I=-16:TP=-1:LRA=11:print_format=json",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
        loudness = json.JSONDecoder().raw_decode(
            measured.stderr[measured.stderr.rfind("{") :]
        )[0]
        # input_* measures this file; output_* is only the analysis filter's hypothetical result.
        assert -17 <= float(loudness["input_i"]) <= -15, loudness
        assert float(loudness["input_tp"]) <= -1, loudness
        results.append(
            {
                "aspect": aspect,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
                "probe": info,
                "measured_loudness": loudness,
                "full_decode": "passed",
            }
        )
        print(
            aspect,
            "decode/metadata/LUFS/true-peak passed",
            loudness["input_i"],
            loudness["input_tp"],
            flush=True,
        )
    model_dir = args.model_dir / "asr-turbo"
    identity = prepare(
        "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
        "0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf",
        [
            "config.json",
            "model.bin",
            "tokenizer.json",
            "vocabulary.json",
            "preprocessor_config.json",
        ],
        model_dir,
        "mit",
        2 * 1024**3,
    )
    model = WhisperModel(
        str(model_dir),
        device="cpu",
        compute_type="int8",
        cpu_threads=2,
        local_files_only=True,
    )
    story = json.loads((root / "story.json").read_text())
    records = []
    # Transcribe the exported MP4, including its AAC normalization and scene holds.
    for index, scene in enumerate(story["scenes"]):
        clip = root / f"asr-scene-{index + 1:02}.wav"
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-ss",
                str(index * 4),
                "-t",
                "4",
                "-i",
                str(root / "review-portrait.mp4"),
                "-vn",
                "-ar",
                "16000",
                "-ac",
                "1",
                str(clip),
            ],
            capture_output=True,
            check=True,
            timeout=30,
        )
        started = time.monotonic()
        waveform, sample_rate = sf.read(clip, dtype="float32")
        assert sample_rate == 16000 and waveform.ndim == 1
        # The supported ndarray API avoids a second decoder and PyAV version-specific flags.
        segments, _ = model.transcribe(
            waveform,
            language="vi",
            beam_size=5,
            vad_filter=False,
            condition_on_previous_text=False,
        )
        recognized = " ".join(segment.text.strip() for segment in segments)
        expected_words, heard_words = (
            normalized(scene["narration"]),
            normalized(recognized),
        )
        similarity = difflib.SequenceMatcher(
            a=expected_words, b=heard_words, autojunk=False
        ).ratio()
        records.append(
            {
                "scene": index + 1,
                "expected": scene["narration"],
                "recognized": recognized,
                "token_sequence_similarity": similarity,
                "seconds": time.monotonic() - started,
                "needs_listening_review": expected_words != heard_words,
            }
        )
        print(
            f"ASR {index + 1}: {recognized} | similarity {similarity:.3f}", flush=True
        )
    report = {
        "files": results,
        "asr_model": identity,
        "asr": records,
        "human_listening": "Pending creator review; ASR does not certify pronunciation, timing or content.",
        "captions": "Short scene-level cues, not forced alignment.",
    }
    (root / "verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
