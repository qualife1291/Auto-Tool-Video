"""Functional smoke: original illustration + generated tone, never labelled as AI narration."""

import argparse
import io
import json
import math
import tempfile
import wave
from pathlib import Path
from uuid import uuid4

from auto_tool_video.domain import ExportInput, Scene
from auto_tool_video.jobs import enqueue
from auto_tool_video.media import import_asset, probe
from auto_tool_video.render import render_job
from auto_tool_video.store import Store
from PIL import Image, ImageDraw


def run(root: Path, aspect: str, full: bool, scene_count: int = 3):
    store = Store(root)
    project = store.create(
        {
            "title": "Vòng tuần hoàn minh họa",
            "profile": "family",
            "platform": "shorts",
            "aspect": aspect,
            "narration": "Nước đi đâu?",
        }
    )
    project["scenes"] = [
        Scene(
            title=title,
            narration="Âm thanh fixture là tiếng sine, không phải giọng AI.",
            duration=1,
        ).model_dump()
        for title in (["Nước ở đâu?", "Quan sát", "Cùng tìm hiểu"] * 7)[:scene_count]
    ]
    project = store.save(project["id"], project)
    for index, scene in enumerate(project["scenes"]):
        image = Image.new("RGB", (1400, 1000), "white")
        draw = ImageDraw.Draw(image)
        draw.ellipse(
            (300, 120, 1000, 820),
            fill=["#B3DDE6", "#DDEAB4", "#E8B587"][index % 3],
            outline="#254D3D",
            width=12,
        )
        draw.line((100, 900, 1300, 900), fill="#254D3D", width=10)
        out = io.BytesIO()
        image.save(out, "PNG")
        project = import_asset(
            store, project["id"], scene["id"], project["revision"], out.getvalue()
        )
        audio = io.BytesIO()
        import struct

        with wave.open(audio, "wb") as wav:
            wav.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
            wav.writeframes(
                b"".join(
                    struct.pack(
                        "<h",
                        round(
                            2500 * math.sin(i * math.tau * (220 + index * 110) / 48000)
                        ),
                    )
                    for i in range(24000)
                )
            )
        project = import_asset(
            store, project["id"], scene["id"], project["revision"], audio.getvalue()
        )
    request = ExportInput(
        revision=project["revision"],
        silent=False,
        aspect=aspect,
        kind="export" if full else "preview",
        idempotency_key=str(uuid4()),
    )
    job = enqueue(store, project["id"], request)
    render_job(store, store.claim())
    result = store.get("jobs", job["id"])
    assert result["state"] == "succeeded"
    path = store.asset_path(store.get("assets", result["result_id"]))
    print(
        json.dumps(
            {
                "aspect": aspect,
                "output": str(path),
                "probe": probe(path)["format"],
                "fixture_audio": "synthetic tone, not TTS",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--portrait1080",
        action="store_true",
        help="Full1080p for both requested aspects",
    )
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    root = args.output_dir or Path(tempfile.mkdtemp(prefix="studio-smoke-"))
    for aspect in ["portrait", "landscape"]:
        run(root / aspect, aspect, args.portrait1080)
