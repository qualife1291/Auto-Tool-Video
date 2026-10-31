"""C05 / #90: cached science MP4s must match the actual source provenance.

Fixture never calls Blender or expensive 1080p FFmpeg, but executes the
unmodified create_story_video.build selection path with real local files.
The initial stale-provenance case intentionally fails on the old code.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
video = importlib.import_module("create_story_video")


class AfterSourceSelection(Exception):
    """Stop before the unrelated studio import/render/export stage."""


class TinyArt:
    def __init__(self, width: int, height: int, art_dir: Path, template: str):
        self.width, self.height, self.template = width, height, template

    def frame(self, seconds: float, duration: float) -> Image.Image:
        return Image.new("RGB", (16, 16), "#7a9fa0")


def story_scene(**changes) -> dict:
    scene = {
        "title": "Áo ướt",
        "narration": "Nước trên áo bay hơi.",
        "duration": 3.0,
        "template": "shirt",
        "caption_emphasis": "Nước",
        "visual_description": "Giữ nguyên áo và giọt nước.",
        "role": "hook",
        "reveal_order": ["Áo ướt", "Giọt nước"],
        "audio": "scene-01.wav",
    }
    return {**scene, **changes}


@pytest.fixture
def cache_environment(tmp_path, monkeypatch):
    (tmp_path / "art").mkdir()
    Image.new("RGBA", (12, 12), "#5b8b8b").save(tmp_path / "art" / "wet.png")
    Image.new("RGBA", (12, 12), "#cee3db").save(tmp_path / "art" / "dry.png")
    renders: list[tuple[str, float]] = []
    monkeypatch.setattr(video, "Art", TinyArt)

    def fake_render(path: Path, art: TinyArt, duration: float) -> None:
        renders.append((art.template, duration))
        # Different render generations have the same byte length and frame count.
        path.write_bytes(bytes([len(renders) % 251]) * 128)

    def fake_probe(path: Path) -> dict:
        return {
            "streams": [{
                "codec_type": "video",
                "width": 1080 if "portrait" in str(path) else 1920,
                "height": 1920 if "portrait" in str(path) else 1080,
                "avg_frame_rate": "30/1",
                "nb_frames": "90",
            }]
        }

    def stop_store(_root: Path):
        raise AfterSourceSelection()

    monkeypatch.setattr(video, "source_clip", fake_render)
    monkeypatch.setattr(video, "probe", fake_probe)
    monkeypatch.setattr(video, "Store", stop_store)

    def run(scene: dict, *, aspect="portrait", reuse=False, rebuild=()):
        (tmp_path / "story.json").write_text(
            json.dumps({"title": "Science review", "scenes": [scene]}, ensure_ascii=False),
            encoding="utf-8",
        )
        with pytest.raises(AfterSourceSelection):
            video.build(
                tmp_path, aspect, stills=False, reuse_clips=reuse,
                rebuild_templates=tuple(rebuild),
            )
        return tmp_path / f"clips-{aspect}" / "scene-01.mp4"

    return tmp_path, renders, run


@pytest.mark.parametrize("aspect", ["portrait", "landscape"])
def test_changed_scene_visual_rebuilds_same_size_same_frame_cached_clip(cache_environment, aspect):
    """Genuine RED: old reuse accepts the prior MP4 despite changed story."""
    root, renders, run = cache_environment
    original = story_scene()
    clip = run(original, aspect=aspect)
    assert clip.is_file()
    first_bytes = clip.read_bytes()

    changed = story_scene(visual_description="Áo xanh đổi vị trí, giọt lớn hơn.")
    clip = run(changed, aspect=aspect, reuse=True)
    assert len(clip.read_bytes()) == len(first_bytes) == 128
    assert len(renders) == 2, "stale visual reuse with identical resolution/FPS/frames must rebuild"
    assert clip.read_bytes() != first_bytes
