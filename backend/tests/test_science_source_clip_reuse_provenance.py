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
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1080 if "portrait" in str(path) else 1920,
                    "height": 1920 if "portrait" in str(path) else 1080,
                    "avg_frame_rate": "30/1",
                    "nb_frames": "90",
                }
            ]
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
                tmp_path,
                aspect,
                stills=False,
                reuse_clips=reuse,
                rebuild_templates=tuple(rebuild),
            )
        return tmp_path / f"clips-{aspect}" / "scene-01.mp4"

    return tmp_path, renders, run


@pytest.mark.parametrize("aspect", ["portrait", "landscape"])
def test_changed_scene_visual_rebuilds_same_size_same_frame_cached_clip(cache_environment, aspect):
    """Genuine RED: old reuse accepts the prior MP4 despite changed story."""
    _root, renders, run = cache_environment
    original = story_scene()
    clip = run(original, aspect=aspect)
    assert clip.is_file()
    first_bytes = clip.read_bytes()

    changed = story_scene(visual_description="Áo xanh đổi vị trí, giọt lớn hơn.")
    clip = run(changed, aspect=aspect, reuse=True)
    assert len(clip.read_bytes()) == len(first_bytes) == 128
    assert len(renders) == 2, "stale visual reuse with identical resolution/FPS/frames must rebuild"
    assert clip.read_bytes() != first_bytes


@pytest.mark.parametrize("aspect", ["portrait", "landscape"])
def test_unchanged_science_source_reuses_validated_cache(cache_environment, aspect):
    _root, renders, run = cache_environment
    scene = story_scene()
    clip = run(scene, aspect=aspect)
    before = clip.read_bytes()
    run(scene, aspect=aspect, reuse=True)
    assert len(renders) == 1, "matching provenance must avoid another render"
    assert clip.read_bytes() == before


@pytest.mark.parametrize("changed", ["wet_art", "dry_art", "template", "caption", "narration"])
def test_changed_source_material_invalidates_cache(cache_environment, changed):
    root, renders, run = cache_environment
    scene = story_scene()
    clip = run(scene)
    before_size = clip.stat().st_size
    if changed in {"wet_art", "dry_art"}:
        file_name = "wet.png" if changed == "wet_art" else "dry.png"
        Image.new("RGBA", (12, 12), "#a84e5b").save(root / "art" / file_name)
    elif changed == "template":
        scene = story_scene(template="warm")
    elif changed == "caption":
        scene = story_scene(caption_emphasis="Hơi nước")
    else:
        scene = story_scene(narration="Giọt nước thoát ra khỏi áo.")
    run(scene, reuse=True)
    assert len(renders) == 2
    assert clip.stat().st_size == before_size


@pytest.mark.parametrize("tamper", ["missing_manifest", "corrupt_manifest", "changed_clip"])
def test_missing_corrupt_or_tampered_cache_rebuilds(cache_environment, tamper):
    _root, renders, run = cache_environment
    scene = story_scene()
    clip = run(scene)
    manifest = clip.with_name(clip.name + ".provenance.json")
    assert manifest.exists()
    if tamper == "missing_manifest":
        manifest.unlink()
    elif tamper == "corrupt_manifest":
        manifest.write_text("{not-json", encoding="utf-8")
    else:
        clip.write_bytes(b"X" * 128)
    run(scene, reuse=True)
    assert len(renders) == 2
    assert manifest.is_file()


def test_untrusted_probe_on_cached_clip_rebuilds(cache_environment, monkeypatch):
    _root, renders, run = cache_environment
    scene = story_scene()
    run(scene)
    valid_probe = video.probe

    def changed_probe(path):
        data = valid_probe(path)
        if len(renders) == 1:
            data["streams"][0]["avg_frame_rate"] = "29/1"
        return data

    monkeypatch.setattr(video, "probe", changed_probe)
    run(scene, reuse=True)
    assert len(renders) == 2


def test_explicit_rebuild_template_bypasses_valid_cache(cache_environment):
    _root, renders, run = cache_environment
    scene = story_scene()
    run(scene)
    run(scene, reuse=True, rebuild=("shirt",))
    assert len(renders) == 2


def test_changed_audio_content_does_not_invalidate_visual_clip(cache_environment):
    root, renders, run = cache_environment
    scene = story_scene()
    run(scene)
    audio = root / scene["audio"]
    audio.write_bytes(b"changed narration wave without video-frame edits")
    run(scene, reuse=True)
    assert len(renders) == 1, "voice asset is imported independently after source selection"


def test_unsafe_output_symlink_is_rejected(cache_environment, tmp_path):
    _root, _renders, run = cache_environment
    scene = story_scene()
    clip = run(scene)
    outside = tmp_path / "outside.mp4"
    outside.write_bytes(b"trusted outside")
    original = outside.read_bytes()
    clip.unlink()
    try:
        clip.symlink_to(outside)
    except (NotImplementedError, OSError):
        pytest.skip("Symlinks are unavailable on this filesystem.")
    with pytest.raises(ValueError, match="symlink"):
        run(scene, reuse=True)
    assert outside.read_bytes() == original


def test_too_large_cached_clip_rebuilds_without_hashing_it(cache_environment):
    _root, renders, run = cache_environment
    scene = story_scene()
    clip = run(scene)
    with clip.open("r+b") as stream:
        stream.truncate(20 * 1024**2 + 1)
    run(scene, reuse=True)
    assert len(renders) == 2
    assert clip.stat().st_size == 128


@pytest.mark.parametrize("duration", [3.01, 3.0])
def test_same_rounded_frame_count_but_changed_duration_rebuilds(cache_environment, duration):
    _root, renders, run = cache_environment
    run(story_scene())
    run(story_scene(duration=duration), reuse=True)
    assert len(renders) == (1 if duration == 3.0 else 2)


def test_missing_artwork_never_authorizes_cache_reuse(cache_environment):
    root, renders, run = cache_environment
    scene = story_scene()
    clip = run(scene)
    assert clip.is_file()
    (root / "art" / "wet.png").unlink()
    run(scene, reuse=True)
    assert len(renders) == 2
    assert not clip.with_name(clip.name + ".provenance.json").exists()
