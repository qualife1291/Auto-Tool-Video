"""C05 science review beat persistence regression.

Uses the actual build path, Scene and SQLite Store, and real FFmpeg-encoded
synthetic clip/WAV imports. Only expensive art creation and the final export
are replaced. These are technical fixtures, not approved voice or video.
"""

from __future__ import annotations

import importlib
import json
import math
import subprocess
import sys
import wave
from pathlib import Path

import pytest
from PIL import Image

from auto_tool_video.store import Store

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

review = importlib.import_module("create_story_video")


class StopBeforeExport(Exception):
    """The persisted studio project is the integration boundary under test."""


class TinyArt:
    def __init__(self, width: int, height: int, art_dir: Path, template: str):
        self.width = width
        self.height = height

    def frame(self, seconds: float, duration: float) -> Image.Image:
        return Image.new("RGB", (32, 32), "#bfd6d5")


def synthetic_clip(path: Path, art: TinyArt, duration: float) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=32x32:r=30",
            "-frames:v",
            str(round(duration * 30)),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(path),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )


def write_audio(path: Path, seconds: float) -> None:
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(48_000)
        stream.writeframes(b"\x00\x00" * round(seconds * 48_000))


@pytest.mark.parametrize("aspect", ["portrait", "landscape"])
def test_build_persists_proposed_beats_after_real_media_import(tmp_path, monkeypatch, aspect):
    """Old build persists empty beats; corrected build must save editable plans."""
    scenes = [
        {
            "title": "Áo ướt",
            "narration": "Nước trên áo sẽ bay hơi. Mời cùng khám phá!",
            "duration": 91 / 30,
            "template": "shirt",
            "role": "hook",
            "caption_emphasis": "Nước",
            "visual_description": "Giữ áo xanh trên dây.",
            "reveal_order": ["Giữ áo", "Phóng to giọt nước"],
            "audio": "scene-01.wav",
        },
        {
            "title": "Nhìn vào sợi vải",
            "narration": "Nước thấm giữa các sợi vải. Chúng ta quan sát nhé!",
            "duration": 4.0,
            "template": "weave",
            "role": "context",
            "caption_emphasis": "sợi vải",
            "visual_description": "Phóng đại bề mặt sợi vải.",
            "reveal_order": ["Giữ áo", "Phóng đại khe dệt"],
            "audio": "scene-02.wav",
        },
    ]
    (tmp_path / "story.json").write_text(
        json.dumps({"title": "Áo khô: nước đã đi đâu?", "scenes": scenes}, ensure_ascii=False),
        encoding="utf-8",
    )
    for scene in scenes:
        write_audio(tmp_path / scene["audio"], scene["duration"] - 0.3)

    monkeypatch.setattr(review, "Art", TinyArt)
    monkeypatch.setattr(review, "source_clip", synthetic_clip)

    def stop_after_save(*args, **kwargs):
        raise StopBeforeExport

    monkeypatch.setattr(review, "enqueue", stop_after_save)
    with pytest.raises(StopBeforeExport):
        review.build(tmp_path, aspect, stills=False)

    store = Store(tmp_path / f"studio-{aspect}")
    projects = store.list_projects()
    assert len(projects) == 1
    project = projects[0]
    assert project["aspect"] == aspect
    assert project["revision"] >= 6  # initial save, four imports, final save
    assert len(project["scenes"]) == len(scenes)

    for saved, source in zip(project["scenes"], scenes, strict=True):
        assert saved["id"]
        assert saved["narration"] == source["narration"]
        assert saved["duration"] == source["duration"]
        assert saved["style"] == "motion"
        assert saved["image_id"] and saved["audio_id"]
        assert store.get("assets", saved["image_id"])["kind"] == "clip"
        assert store.get("assets", saved["audio_id"])["kind"] == "audio"
        assert saved["beat_plan_status"] == "needs_review"
        beats = saved["second_by_second"]
        assert [beat["second"] for beat in beats] == list(range(math.ceil(saved["duration"])))
        assert all(beat["visual_state"] and beat["action"] for beat in beats)
        assert all(beat["narration_cue"] and beat["continuity"] for beat in beats)
        assert any("dự kiến" in beat["narration_cue"] for beat in beats)
