"""Explicit, isolated CPU synthesis for the review artifact; never run on app startup."""

import argparse
import hashlib
import importlib.metadata
import json
import shutil
import time
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

MODEL = "pnnbao-ump/VieNeu-TTS-v3-Turbo"
REVISION = "61b85e3d937fbbacb387714180e8182823512523"
CODEC = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX"
CODEC_REVISION = "ceff0d0749bfb3fa2d61149794ec6feef0d1e1ae"
GRAPHS = [
    "onnx_update/" + file
    for file in [
        "vieneu_prefill.onnx",
        "vieneu_decode_step.onnx",
        "vieneu_acoustic_cached.onnx",
        "vieneu_backbone_shared.data",
        "vieneu_v3_heads.npz",
        "config.json",
        "tokenizer.json",
    ]
]
CODEC_FILES = [
    "moss_audio_tokenizer_decode_full.onnx",
    "moss_audio_tokenizer_decode_shared.data",
    "moss_audio_tokenizer_decode_step.onnx",
    "codec_browser_onnx_meta.json",
    "moss_audio_tokenizer_encode.onnx",
    "moss_audio_tokenizer_encode.data",
]


def request(url):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Auto-Tool-Video-review"}),
        timeout=60,
    )


def prepare(
    repo,
    revision,
    files,
    destination,
    license_id="apache-2.0",
    max_file_bytes=600 * 1024**2,
):
    with request(
        f"https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true"
    ) as response:
        metadata = json.load(response)
    if (
        metadata["sha"] != revision
        or metadata.get("cardData", {}).get("license") != license_id
    ):
        raise RuntimeError("Model identity/license differs from reviewed source.")
    destination.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name in files:
        item = next(row for row in metadata["siblings"] if row["rfilename"] == name)
        size = item["size"]
        if (
            size > max_file_bytes
            or shutil.disk_usage(destination).free < size + 2 * 1024**3
        ):
            raise RuntimeError(
                "Insufficient disk or model file exceeds reviewed budget."
            )
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            pending = target.with_suffix(target.suffix + ".part")
            try:
                with (
                    request(
                        f"https://huggingface.co/{repo}/resolve/{revision}/{name}"
                    ) as response,
                    pending.open("wb") as output,
                ):
                    received = 0
                    while chunk := response.read(1024 * 1024):
                        received += len(chunk)
                        if received > size:
                            raise RuntimeError("Model download exceeds declared size.")
                        output.write(chunk)
                if received != size:
                    raise RuntimeError("Incomplete model download.")
                pending.replace(target)
            finally:
                pending.unlink(missing_ok=True)
        with target.open("rb") as content:
            digest = hashlib.file_digest(content, "sha256").hexdigest()
        lfs = item.get("lfs", {})
        if target.stat().st_size != size or (lfs and digest != lfs["sha256"]):
            raise RuntimeError(f"Checksum mismatch: {name}")
        if (
            not lfs
            and hashlib.sha1(
                b"blob " + str(size).encode() + b"\0" + target.read_bytes()
            ).hexdigest()
            != item["blobId"]
        ):
            raise RuntimeError(f"Git blob integrity mismatch: {name}")
        manifest.append({"file": name, "bytes": size, "sha256": digest})
        print(f"Verified {repo}/{name}", flush=True)
    return {
        "repository": repo,
        "revision": revision,
        "license": license_id,
        "files": manifest,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--voice")
    args = parser.parse_args()
    root = args.output_dir.resolve()
    story = json.loads((root / "story.json").read_text())
    model_dir, codec_dir = args.model_dir / "vieneu", args.model_dir / "codec"
    identities = [
        prepare(MODEL, REVISION, GRAPHS, model_dir),
        prepare(CODEC, CODEC_REVISION, CODEC_FILES, codec_dir),
    ]

    # SDK 3.8.3's high-level factory does not expose codec_dir. Its actual ONNX engine
    # accepts explicit pinned paths, so synthesis performs no implicit remote loading.
    import vieneu
    from vieneu._v3_turbo_engine.onnx_runtime_lite import OnnxV3LiteEngine
    from vieneu_utils.core_utils import strip_encoder_pad_frame

    voices_file = Path(vieneu.__file__).parent / "assets" / "voices_v3_turbo.json"
    voices = json.loads(voices_file.read_text())
    voice = args.voice or (
        "Hải Đăng" if "Hải Đăng" in voices["presets"] else voices["default_voice"]
    )
    if voice not in voices["presets"]:
        raise ValueError(f"Voice unavailable: {voice}. Choose an installed preset.")
    preset = voices["presets"][voice]
    started = time.monotonic()
    engine = OnnxV3LiteEngine(
        checkpoint_path=str(model_dir),
        onnx_dir=str(model_dir / "onnx_update"),
        codec_dir=str(codec_dir),
        threads=2,
    )
    engine.babble_retries = 1
    load_seconds = time.monotonic() - started
    output = root / "audio"
    output.mkdir(exist_ok=True)
    records = []
    for index, scene in enumerate(story["scenes"]):
        cached = next(
            (row for row in records if row["narration"] == scene["narration"]), None
        )
        if cached:
            target = output / f"scene-{index + 1:02}.wav"
            shutil.copy2(root / cached["file"], target)
            records.append(
                {
                    **cached,
                    "index": index,
                    "file": str(target.relative_to(root)),
                    "synthesis_seconds": 0,
                    "reused_from_scene": cached["index"] + 1,
                }
            )
            print(
                f"Voice {voice}, scene {index + 1}: reused identical narration from scene {cached['index'] + 1}",
                flush=True,
            )
            continue
        np.random.seed(20261030 + index)
        started = time.monotonic()
        waveform = engine.infer(
            text=scene["narration"],
            speaker_emb=np.asarray(preset["speaker_emb"], dtype=np.float32),
            ref_codes=strip_encoder_pad_frame(
                np.asarray(preset["codes"], dtype=np.int64)
            ),
            temperature=0.7,
            top_k=25,
            top_p=0.95,
            max_new_frames=300,
        )
        if (
            not waveform.size
            or not np.isfinite(waveform).all()
            or np.max(np.abs(waveform)) > 1
        ):
            raise RuntimeError("Invalid or clipping TTS waveform.")
        waveform = np.pad(waveform, (4800, 12000))
        duration = len(waveform) / 48000
        if duration > 19.3:
            raise RuntimeError(
                "Review sentence is too long; edit script rather than truncating speech."
            )
        target = output / f"scene-{index + 1:02}.wav"
        sf.write(target, waveform, 48000, subtype="PCM_16")
        record = {
            "index": index,
            "file": str(target.relative_to(root)),
            "narration": scene["narration"],
            "duration": duration,
            "synthesis_seconds": time.monotonic() - started,
            "seed": 20261030 + index,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        }
        records.append(record)
        print(
            f"Voice {voice}, scene {index + 1}: {duration:.2f}s, synthesized {record['synthesis_seconds']:.2f}s",
            flush=True,
        )
    provenance = {
        "sdk": "vieneu",
        "version": importlib.metadata.version("vieneu"),
        "backend": "ONNX CPU FP32",
        "models": identities,
        "voice": voice,
        "voice_source": "SDK bundled preset; no cloning",
        "voices_sha256": hashlib.sha256(voices_file.read_bytes()).hexdigest(),
        "load_seconds": load_seconds,
        "threads": 2,
        "audio_sample_rate": 48000,
        "records": records,
        "review": "Real synthesis; human listening review pending.",
    }
    (root / "tts-provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
