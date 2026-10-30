"""Four original Vietnamese-content QA videos, 12/30/45/60s, two aspects.

Pillow art and offline eSpeak are engineering fixtures, not approved voices or
fact-checked creator footage. Never mark production/human review approved.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from auto_tool_video.domain import ExportInput, Scene
from auto_tool_video.jobs import enqueue
from auto_tool_video.media import import_asset, probe
from auto_tool_video.render import render_job
from auto_tool_video.store import Store
from auto_tool_video.timing import frames_for
from PIL import Image, ImageDraw


@dataclass(frozen=True)
class Scenario:
    key: str
    title: str
    scene_seconds: int
    cues: tuple[tuple[str, str], ...]

    @property
    def seconds(self) -> int:
        return self.scene_seconds * len(self.cues)


SCENARIOS = {
    "water-12s": Scenario(
        "water-12s",
        "Vòng tuần hoàn của nước",
        3,
        (
            ("Giọt nước", "Nhìn giọt nước nhỏ."),
            ("Bay hơi", "Nước đang bay hơi."),
            ("Mây trắng", "Hơi nước tạo thành mây."),
            ("Mưa xuống", "Rồi mưa lại rơi xuống."),
        ),
    ),
    "shirt-30s": Scenario(
        "shirt-30s",
        "Vì sao áo ướt lại khô?",
        5,
        (
            ("Áo ướt", "Chiếc áo vừa được giặt."),
            ("Ánh nắng", "Nắng mang thêm năng lượng."),
            ("Gió thổi", "Gió giúp hơi nước đi xa."),
            ("Bay hơi", "Nước bay hơi từ sợi vải."),
            ("Trải rộng", "Trải áo ra để thoáng khí."),
            ("Áo khô", "Cuối cùng áo đã khô."),
        ),
    ),
    "traffic-45s": Scenario(
        "traffic-45s",
        "An toàn khi qua đường",
        5,
        (
            ("Dừng lại", "Dừng ở mép vỉa hè."),
            ("Quan sát", "Nhìn trái rồi nhìn phải."),
            ("Lắng nghe", "Nghe tiếng xe gần mình."),
            ("Đèn đường", "Chờ đèn dành cho người đi bộ."),
            ("Vạch đi bộ", "Chọn đúng vạch qua đường."),
            ("Đi chậm", "Không chạy vội qua phố."),
            ("Tập trung", "Tập trung quan sát giao thông."),
            ("Người lớn", "Trẻ nhỏ cần người lớn đi cùng."),
            ("An toàn", "Cẩn thận khi qua đường nhé."),
        ),
    ),
    "energy-60s": Scenario(
        "energy-60s",
        "Một phút tiết kiệm năng lượng",
        5,
        (
            ("Bắt đầu", "Điện giúp cuộc sống tiện lợi."),
            ("Bật đèn", "Chỉ bật đèn khi cần."),
            ("Ánh sáng", "Tận dụng ánh sáng ban ngày."),
            ("Quạt mát", "Tắt quạt khi ra khỏi phòng."),
            ("Máy lạnh", "Đóng cửa khi dùng máy lạnh."),
            ("Thiết bị", "Chọn thiết bị phù hợp nhu cầu."),
            ("Sạc điện", "Rút bộ sạc khi không dùng."),
            ("Nấu ăn", "Đậy nắp nồi để giữ nhiệt."),
            ("Tủ lạnh", "Đóng cửa tủ lạnh thật kín."),
            ("Gia đình", "Cùng nhau nhắc thói quen tốt."),
            ("Việc nhỏ", "Việc nhỏ tạo thay đổi lớn."),
            ("Tổng kết", "Tiết kiệm điện mỗi ngày nhé."),
        ),
    ),
}

SIZES = {
    "preview": {"portrait": (360, 640), "landscape": (640, 360)},
    "export": {"portrait": (1080, 1920), "landscape": (1920, 1080)},
}
COMPRESSOR = "acompressor=threshold=-25dB:ratio=3:attack=20:release=200"


def validate_scenario(scenario: Scenario) -> None:
    if not 1 <= len(scenario.cues) <= 20:
        raise ValueError("Scene count must be between 1 and 20")
    if not 1 <= scenario.scene_seconds <= 20:
        raise ValueError("A scene must be between 1 and 20 seconds")
    if scenario.seconds > 60:
        raise ValueError("Studio preset maximum is 60 seconds")
    if sum(frames_for(scenario.scene_seconds) for _ in scenario.cues) > 1800:
        raise ValueError("Actual 30fps timeline exceeds 60 seconds")
    if any(len(title) > 70 or len(cue) > 500 for title, cue in scenario.cues):
        raise ValueError("Scene caption/narration bound exceeded")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def visual(index: int, scenario: Scenario) -> bytes:
    image = Image.new("RGB", (1400, 1000), "#FFF8EB")
    draw = ImageDraw.Draw(image)
    colors = ("#ADDDE4", "#DDEAB4", "#E8B587", "#BDB5E0", "#F8D274")
    shift = (index * 61) % 180
    draw.rounded_rectangle((125, 135, 1250, 880), radius=90, fill="#F5F1DC")
    draw.ellipse(
        (245 + shift, 180, 950 + shift, 785),
        fill=colors[index % len(colors)],
        outline="#254D3D",
        width=17,
    )
    if scenario.key.startswith("water"):
        draw.polygon([(650, 240), (460, 650), (835, 650)], fill="#73BFD0")
    elif scenario.key.startswith("shirt"):
        draw.polygon(
            [
                (390, 250),
                (520, 220),
                (600, 310),
                (740, 310),
                (825, 220),
                (960, 250),
                (1020, 470),
                (865, 540),
                (865, 745),
                (475, 745),
                (475, 540),
                (330, 470),
            ],
            fill=colors[index % len(colors)],
            outline="#254D3D",
            width=12,
        )
    elif scenario.key.startswith("traffic"):
        draw.rectangle(
            (600, 250, 780, 705),
            fill="#344B45",
            outline="#132823",
            width=15,
        )
        for i, light in enumerate(("#DE6B62", "#E9BE67", "#76BD88")):
            y = 285 + i * 135
            draw.ellipse((640, y, 740, y + 100), fill=light)
    else:
        draw.rectangle(
            (490, 380, 850, 610),
            fill="#F8E19B",
            outline="#254D3D",
            width=15,
        )
        draw.line((565, 480, 760, 480), fill="#254D3D", width=17)
    draw.line((85, 920, 1315, 920), fill="#254D3D", width=16)
    output = io.BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


def voice(text: str, path: Path) -> dict:
    espeak = shutil.which("espeak")
    if espeak is None:
        raise RuntimeError("eSpeak must be installed for these voiced fixtures")
    raw = path.with_suffix(".raw.wav")
    subprocess.run(
        [espeak, "-v", "vi", "-s", "175", "-w", str(raw), text],
        capture_output=True,
        check=True,
        timeout=30,
    )
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-v",
                "error",
                "-y",
                "-i",
                str(raw),
                "-af",
                COMPRESSOR,
                "-c:a",
                "pcm_s16le",
                str(path),
            ],
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        raw.unlink(missing_ok=True)
    with wave.open(str(path), "rb") as wav:
        duration = wav.getnframes() / wav.getframerate()
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
            raise ValueError("Source voice not mono PCM16")
    return {"duration": duration, "narration": text, "sha256": digest(path)}


def beats(seconds: int, narration: str) -> list[dict]:
    return [
        {
            "second": i,
            "visual_state": f"Cảnh rõ nét, liên tục ở giây {i}",
            "action": "Chuyển động minh họa nhẹ",
            "camera": "Máy cố định",
            "on_screen_text": narration if i == 0 else "",
            "narration_cue": narration,
            "continuity": "Giữ nguyên chủ thể và màu sắc",
        }
        for i in range(seconds)
    ]


def render_one(
    root: Path,
    scenario: Scenario,
    aspect: str,
    kind: str,
    voices: list[Path],
) -> dict:
    store = Store(root / aspect)
    project = store.create(
        {
            "title": scenario.title,
            "profile": "family",
            "platform": "shorts",
            "aspect": aspect,
            "narration": " ".join(cue for _, cue in scenario.cues),
        }
    )
    project["scenes"] = [
        Scene(
            title=title,
            narration=cue,
            duration=scenario.scene_seconds,
            style=("whiteboard", "motion")[i % 2],
            caption_style=("card", "contrast", "accent")[i % 3],
            caption_emphasis=cue.split()[0] if i % 3 == 2 else "",
            layout=("board", "full_frame")[i % 2],
            transition=("cut", "dissolve")[i % 2],
            second_by_second=beats(scenario.scene_seconds, cue),
            beat_plan_status="authored",
        ).model_dump()
        for i, (title, cue) in enumerate(scenario.cues)
    ]
    project = store.save(project["id"], project)
    for i, scene in enumerate(project["scenes"]):
        project = import_asset(
            store,
            project["id"],
            scene["id"],
            project["revision"],
            visual(i, scenario),
        )
        project = import_asset(
            store,
            project["id"],
            scene["id"],
            project["revision"],
            voices[i].read_bytes(),
        )
    for scene in project["scenes"]:
        scene["duration"] = scenario.scene_seconds
        # Do not auto-approve beats after media changes.
        scene["beat_plan_status"] = "needs_review"
    project = store.save(project["id"], project)
    options = ExportInput(
        revision=project["revision"],
        aspect=aspect,
        kind=kind,
        silent=False,
        idempotency_key=str(uuid4()),
    )
    job = enqueue(store, project["id"], options)
    try:
        render_job(store, store.claim())
    except RuntimeError as exc:
        failed = store.get("jobs", job["id"])
        report = failed.get("quality_report") or {}
        checks = report.get("technical", {}).get("checks", [])
        defects = [
            {"id": check["id"], "actual": check.get("actual")}
            for check in checks
            if check.get("status") == "failed"
        ]
        diagnostic = root / f"scenario-qc-failed-{aspect}.json"
        diagnostic.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise RuntimeError(
            f"{scenario.key} {aspect}: final MP4 QC rejected: {defects}; "
            f"diagnostic={diagnostic.name}"
        ) from exc
    completed = store.get("jobs", job["id"])
    if completed["state"] != "succeeded":
        raise AssertionError(f"Render did not succeed: {completed['state']}")
    asset = store.get("assets", completed["result_id"])
    output = root / f"{scenario.key}-{aspect}-{kind}.mp4"
    shutil.copyfile(store.asset_path(asset), output)
    metadata = probe(output)
    videos = [s for s in metadata["streams"] if s["codec_type"] == "video"]
    audios = [s for s in metadata["streams"] if s["codec_type"] == "audio"]
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError("Expected exactly one video and one audio stream")
    video, audio = videos[0], audios[0]
    expected = SIZES[kind][aspect]
    if (video["width"], video["height"]) != expected:
        raise ValueError(f"{aspect}: wrong resolution")
    if video["codec_name"] != "h264" or video["r_frame_rate"] != "30/1":
        raise ValueError("Expected H264 CFR 30fps")
    if audio["codec_name"] != "aac" or audio["sample_rate"] != "48000":
        raise ValueError("Expected AAC 48kHz")
    duration = float(metadata["format"]["duration"])
    if abs(duration - scenario.seconds) > 0.12:
        raise ValueError(f"Duration {duration} != {scenario.seconds}")
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-v",
            "error",
            "-xerror",
            "-i",
            str(output),
            "-map",
            "0",
            "-f",
            "null",
            "-",
        ],
        check=True,
        capture_output=True,
        timeout=180,
    )
    frames = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_frames",
                "-show_entries",
                "frame=best_effort_timestamp_time",
                "-of",
                "json",
                str(output),
            ],
            timeout=120,
        )
    )["frames"]
    if len(frames) != scenario.seconds * 30:
        raise ValueError("Wrong decoded frame count")
    for i, frame in enumerate(frames):
        pts = float(frame["best_effort_timestamp_time"])
        if not math.isfinite(pts) or abs(pts - i / 30) > 0.002:
            raise ValueError("Frame PTS gap/duplication")
    return {
        "file": output.name,
        "sha256": digest(output),
        "aspect": aspect,
        "resolution": list(expected),
        "seconds": duration,
        "frames": len(frames),
        "technical": "PASS",
        "full_decode": "PASS",
        "creator_review": "NOT RUN",
    }


def run(key: str, root: Path, kind: str = "preview") -> dict:
    scenario = SCENARIOS[key]
    validate_scenario(scenario)
    root.mkdir(parents=True, exist_ok=True)
    audio_dir = root / "voices"
    audio_dir.mkdir(exist_ok=True)
    voices = []
    records = []
    report = {
        "scenario": key,
        "title": scenario.title,
        "scenes": len(scenario.cues),
        "target_seconds": scenario.seconds,
        "cues": [{"title": t, "narration": c} for t, c in scenario.cues],
        "source": "Pillow art + local eSpeak vi, 175 wpm",
        "audio_mastering": "synthetic-fixture compressor only",
        "release_approved": False,
        "human_review": "NOT RUN",
        "voice_approval": "NOT APPROVED",
        "outputs": [],
    }
    try:
        for i, (_title, cue) in enumerate(scenario.cues):
            path = audio_dir / f"voice-{i + 1:02d}.wav"
            info = voice(cue, path)
            if info["duration"] + 0.12 > scenario.scene_seconds:
                raise ValueError(f"Scene {i + 1}: voice overflows allotted time")
            voices.append(path)
            records.append(info)
        report["voice_inputs"] = records
        for aspect in ("portrait", "landscape"):
            report["outputs"].append(render_one(root, scenario, aspect, kind, voices))
        report["status"] = "TECHNICAL_PASS_ONLY"
    except Exception as exc:
        report["status"] = "FAILED"
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        (root / "scenario-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--kind", choices=tuple(SIZES), default="preview")
    args = parser.parse_args()
    root = args.output_dir or Path(tempfile.mkdtemp(prefix="video-qa-"))
    run(args.scenario, root, args.kind)
