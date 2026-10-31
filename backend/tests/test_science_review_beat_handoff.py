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

from auto_tool_video.domain import ProjectInput, Scene
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


def science_source(duration: float) -> dict:
    return {
        "title": "Nước đã đi đâu?",
        "narration": "Áo ướt rồi khô. Nước đã đi đâu nhỉ?",
        "template": "shirt",
        "caption_emphasis": "Nước",
        "visual_description": "Giữ chiếc áo xanh, zoom nhẹ vào giọt nước.",
        "duration": duration,
    }


@pytest.mark.parametrize("duration", [3.0, 91 / 30, 599 / 30, 20.0])
def test_fractional_and_twenty_second_beats_validate_and_roundtrip(tmp_path, duration):
    """Real Scene validation and Store.save cover 30fps and <=20-second limits."""
    store = Store(tmp_path / "studio")
    project = store.create(
        ProjectInput(title="Áo khô: nước đã đi đâu?", narration="Nước đi đâu?").model_dump()
    )
    source = science_source(duration)
    scene = Scene(
        title=source["title"],
        narration=source["narration"],
        duration=duration,
        style="motion",
        layout="full_frame",
        visual_description=source["visual_description"],
        caption_emphasis=source["caption_emphasis"],
    ).model_dump()
    project = store.save(project["id"], {**project, "scenes": [scene]})
    old_id = scene["id"]
    planned = review._proposed_science_beats(project["scenes"], [source])
    assert planned[0]["id"] == old_id
    assert planned[0]["beat_plan_status"] == "needs_review"
    assert [beat["second"] for beat in planned[0]["second_by_second"]] == list(
        range(math.ceil(duration))
    )
    assert any(
        beat["narration_cue"].startswith("Cue dự kiến (chưa forced-align):")
        for beat in planned[0]["second_by_second"]
    )
    project = store.save(project["id"], {**project, "scenes": planned})
    restored = Store(tmp_path / "studio").get("projects", project["id"])
    assert restored["revision"] == project["revision"]
    assert restored["scenes"][0]["id"] == old_id
    assert restored["scenes"][0]["second_by_second"] == planned[0]["second_by_second"]
    assert restored["scenes"][0]["beat_plan_status"] == "needs_review"


@pytest.mark.parametrize(
    "invalid",
    ["missing-template", "bad-template", "other-narration", "missing-caption", "existing-plan"],
)
def test_invalid_science_source_fails_without_mutating_existing_scene(invalid):
    scene_source = science_source(91 / 30)
    scene = Scene(
        title=scene_source["title"],
        narration=scene_source["narration"],
        duration=scene_source["duration"],
        visual_description=scene_source["visual_description"],
        caption_emphasis=scene_source["caption_emphasis"],
    ).model_dump()
    before = json.dumps(scene, sort_keys=True)
    if invalid == "missing-template":
        scene_source.pop("template")
    elif invalid == "bad-template":
        scene_source["template"] = "nonexistent"
    elif invalid == "other-narration":
        scene_source["narration"] = "Nội dung khác."
    elif invalid == "missing-caption":
        scene_source.pop("caption_emphasis")
    else:
        scene["beat_plan_status"] = "authored"
        before = json.dumps(scene, sort_keys=True)

    with pytest.raises(ValueError, match="Science scene|Invalid science beat plan"):
        review._proposed_science_beats([scene], [scene_source])
    assert json.dumps(scene, sort_keys=True) == before


@pytest.mark.parametrize("field", ["visual_description", "caption_emphasis"])
def test_changed_visual_or_caption_fails_without_mutating_inputs(field):
    """Same title/narration does not authorize contradictory source beat text."""
    source = science_source(91 / 30)
    scene = Scene(
        title=source["title"],
        narration=source["narration"],
        duration=source["duration"],
        visual_description=source["visual_description"],
        caption_emphasis=source["caption_emphasis"],
    ).model_dump()
    scene[field] += " (manual edit)"
    saved_before = json.dumps(scene, ensure_ascii=False, sort_keys=True)
    source_before = json.dumps(source, ensure_ascii=False, sort_keys=True)

    with pytest.raises(ValueError, match="no longer matches its source"):
        review._proposed_science_beats([scene], [source])

    assert json.dumps(scene, ensure_ascii=False, sort_keys=True) == saved_before
    assert json.dumps(source, ensure_ascii=False, sort_keys=True) == source_before


@pytest.mark.parametrize("duration", [29 / 30, 601 / 30])
def test_out_of_range_scene_duration_is_rejected_by_existing_domain(duration):
    """The domain Scene contract rejects sub-1s and >20s scenes."""
    source = science_source(duration)
    with pytest.raises(ValueError):
        Scene(
            title=source["title"],
            narration=source["narration"],
            duration=duration,
            visual_description=source["visual_description"],
            caption_emphasis=source["caption_emphasis"],
        )


def test_source_count_mismatch_fails_before_writing_any_plan():
    source = science_source(2.0)
    first = Scene(title=source["title"], narration=source["narration"]).model_dump()
    second = Scene(title="Cảnh khác", narration="Giữ nguyên!").model_dump()
    original = json.dumps([first, second], sort_keys=True)

    with pytest.raises(ValueError, match="count mismatch"):
        review._proposed_science_beats([first, second], [source])
    assert json.dumps([first, second], sort_keys=True) == original


def test_synthetic_multiscene_timing_stays_under_sixty_seconds():
    sources = [science_source(599 / 30), science_source(20), science_source(3)]
    scenes = [
        Scene(
            title=source["title"],
            narration=source["narration"],
            duration=source["duration"],
            visual_description=source["visual_description"],
            caption_emphasis=source["caption_emphasis"],
        ).model_dump()
        for source in sources
    ]
    result = review._proposed_science_beats(scenes, sources)
    assert sum(scene["duration"] for scene in result) <= 60
    assert [len(scene["second_by_second"]) for scene in result] == [20, 20, 3]
    assert all(scene["beat_plan_status"] == "needs_review" for scene in result)
