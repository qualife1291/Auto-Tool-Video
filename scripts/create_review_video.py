"""Original illustrations + real imported narration through the application renderer."""

import argparse
import hashlib
import json
import math
import shutil
import time
from pathlib import Path
from uuid import uuid4

import cv2
from auto_tool_video.domain import ExportInput, ProjectInput, Scene
from auto_tool_video.jobs import enqueue
from auto_tool_video.media import import_asset, probe
from auto_tool_video.render import render_job
from auto_tool_video.store import Store
from PIL import Image, ImageDraw

PAPER = "#FFF8EB"
INK = "#254D3D"
BLUE = "#5CBAC6"
GOLD = "#F4BE53"
CORAL = "#E7876F"
SPEECH = [
    ("Nước đã đi đâu?", "Áo ướt khô rồi. Nước đã đi đâu nhỉ?", "motion"),
    ("Từ áo vào không khí", "Nước trên áo dần đi vào không khí.", "whiteboard"),
    ("Đó là bay hơi", "Quá trình ấy gọi là bay hơi.", "whiteboard"),
    ("Không cần nước sôi", "Bay hơi xảy ra cả khi nước chưa sôi.", "motion"),
    ("Ấm và thoáng", "Nơi ấm và thoáng thường giúp quần áo mau khô.", "motion"),
    ("Trải áo rộng", "Trải áo rộng giúp nước dễ bay hơi hơn.", "whiteboard"),
    ("Hơi nước vô hình", "Hơi nước trong không khí thường không nhìn thấy.", "motion"),
    (
        "Nước vẫn ở quanh ta",
        "Nước trên áo dần đi vào không khí.",
        "motion",
    ),
]
CAPTIONS = [
    ("contrast", ""),
    ("card", ""),
    ("accent", "bay hơi"),
    ("accent", "chưa sôi"),
    ("contrast", ""),
    ("accent", "Trải áo rộng"),
    ("accent", "không nhìn thấy"),
    ("contrast", ""),
]


def artwork(index: int) -> Image.Image:
    image = Image.new("RGB", (1600, 1400), PAPER)
    draw = ImageDraw.Draw(image)
    # Original flat illustrations, no stock material, diffusion weights or borrowed character.
    draw.ellipse((100, 90, 1500, 1320), fill="#F5EEDB")

    def shirt(x, y, scale=1.0, color=BLUE):
        points = [
            (-180, -190),
            (-300, -100),
            (-235, 35),
            (-160, -5),
            (-160, 260),
            (160, 260),
            (160, -5),
            (235, 35),
            (300, -100),
            (180, -190),
            (75, -230),
            (50, -165),
            (-50, -165),
            (-75, -230),
        ]
        points = [(round(x + a * scale), round(y + b * scale)) for a, b in points]
        draw.polygon(points, fill=color, outline=INK, width=10)
        draw.line(
            [(x - 140 * scale, y + 230 * scale), (x + 140 * scale, y + 230 * scale)],
            fill="#E5F3EF",
            width=7,
        )
        draw.rounded_rectangle(
            (x + 20 * scale, y - 50 * scale, x + 110 * scale, y + 45 * scale),
            radius=15,
            outline=INK,
            width=6,
        )
        # Deliberate garment detail: twin hem, stitched side seams and soft folds.
        draw.line(
            [(x - 140 * scale, y + 215 * scale), (x + 140 * scale, y + 215 * scale)],
            fill=INK,
            width=3,
        )
        for side in (-1, 1):
            for stitch in range(11):
                sy = y + (20 + stitch * 17) * scale
                sx = x + side * 145 * scale
                draw.line((sx, sy, sx, sy + 6 * scale), fill=INK, width=2)
        for fx, fy in [(-95, 25), (-45, 115), (100, 150)]:
            draw.arc(
                (
                    x + (fx - 15) * scale,
                    y + (fy - 45) * scale,
                    x + (fx + 15) * scale,
                    y + (fy + 35) * scale,
                ),
                80,
                260,
                fill="#378D9D",
                width=4,
            )
        draw.arc(
            (x - 64 * scale, y - 204 * scale, x + 64 * scale, y - 135 * scale),
            0,
            180,
            fill=INK,
            width=5,
        )

    def drop(x, y, radius=30):
        draw.polygon(
            [(x, y - radius * 1.8), (x - radius, y), (x + radius, y)], fill=BLUE
        )
        draw.ellipse(
            (x - radius, y - radius / 2, x + radius, y + radius * 1.5),
            fill=BLUE,
            outline=INK,
            width=4,
        )
        draw.ellipse(
            (x - radius / 2, y, x - radius / 6, y + radius / 2), fill="#D7F1EE"
        )

    def arrow(start, end, color=INK, width=14):
        draw.line([start, end], fill=color, width=width)
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        points = [end] + [
            (end[0] - 40 * math.cos(angle + a), end[1] - 40 * math.sin(angle + a))
            for a in (-0.5, 0.5)
        ]
        draw.polygon(points, fill=color)

    def sun(x, y, radius=90):
        for i in range(12):
            angle = i * math.tau / 12
            draw.line(
                [
                    (
                        x + (radius + 20) * math.cos(angle),
                        y + (radius + 20) * math.sin(angle),
                    ),
                    (
                        x + (radius + 55) * math.cos(angle),
                        y + (radius + 55) * math.sin(angle),
                    ),
                ],
                fill=GOLD,
                width=14,
            )
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=GOLD,
            outline=INK,
            width=8,
        )

    if index == 0:
        draw.line((220, 340, 1380, 340), fill=INK, width=12)
        shirt(800, 690, 1.6)
        for x in (580, 800, 1020):
            drop(x, 1170, 28)
        for x in (650, 950):
            draw.rounded_rectangle(
                (x - 15, 305, x + 15, 390), 9, fill=GOLD, outline=INK, width=5
            )
    elif index in (1, 2):
        shirt(800, 850, 1.4)
        for x in (500, 800, 1100):
            arrow((x, 560), (x + 40, 300), BLUE)
        # Dots are a schematic of motion, not visible clouds of water vapour.
        if index == 2:
            for x, y in [(400, 220), (650, 170), (900, 220), (1200, 160)]:
                draw.ellipse((x - 18, y - 18, x + 18, y + 18), fill=BLUE)
        else:
            # Magnified schematic of water on woven cloth, not a microscope photograph.
            draw.line((960, 1040, 1190, 1110), fill=INK, width=5)
            draw.ellipse((1170, 970, 1490, 1290), fill="#E0F0EC", outline=INK, width=7)
            for shift in range(-80, 81, 40):
                draw.line(
                    (1225, 1130 + shift, 1435, 1130 + shift), fill="#6DB3BC", width=4
                )
                draw.line(
                    (1330 + shift, 1025, 1330 + shift, 1235), fill="#6DB3BC", width=4
                )
            drop(1330, 1100, 35)
    elif index == 3:
        draw.rounded_rectangle(
            (420, 500, 1180, 1140), 45, fill="#D7E8DD", outline=INK, width=12
        )
        draw.rounded_rectangle((450, 760, 1150, 1110), 25, fill=BLUE)
        draw.arc((450, 460, 1150, 550), 0, 180, fill=INK, width=10)
        for x in (600, 800, 1000):
            arrow((x, 650), (x + 30, 300), BLUE)
        draw.rounded_rectangle(
            (1260, 690, 1300, 1080), 20, fill="#FFFFFF", outline=INK, width=7
        )
        draw.ellipse((1225, 1010, 1335, 1120), fill=CORAL, outline=INK, width=7)
        draw.line((1280, 1020, 1280, 830), fill=CORAL, width=16)
    elif index == 4:
        sun(1240, 280)
        shirt(740, 800, 1.5)
        for y in (480, 600, 720):
            arrow((190, y), (460, y - 30), BLUE, 12)
        draw.line((330, 1130, 1230, 1130), fill=INK, width=9)
    elif index == 5:
        shirt(800, 650, 1.7)
        arrow((370, 1100), (180, 1100), CORAL)
        arrow((1230, 1100), (1420, 1100), CORAL)
        draw.line((420, 1100, 1180, 1100), fill=CORAL, width=8)
    elif index == 6:
        draw.rounded_rectangle(
            (300, 290, 1300, 1080), 40, fill="#D6ECE9", outline=INK, width=12
        )
        draw.line((800, 300, 800, 1080), fill=INK, width=10)
        draw.line((300, 670, 1300, 670), fill=INK, width=10)
        draw.line((530, 330, 530, 570), fill=PAPER, width=18)
        draw.line((430, 725, 780, 725), fill=INK, width=5)
        shirt(620, 850, 0.55)
        sun(1200, 160, 60)
        draw.rounded_rectangle(
            (275, 1065, 1325, 1120), 12, fill="#E7CE9C", outline=INK, width=6
        )
        draw.polygon(
            [(1190, 1050), (1300, 1050), (1280, 960), (1210, 960)],
            fill=CORAL,
            outline=INK,
            width=5,
        )
        for px, py in [(1190, 830), (1290, 850), (1210, 910)]:
            draw.line((1245, 960, px, py), fill=INK, width=5)
            draw.ellipse(
                (px - 30, py - 22, px + 30, py + 22),
                fill="#7BAC83",
                outline=INK,
                width=4,
            )
    else:
        draw.line((200, 370, 1400, 370), fill=INK, width=11)
        shirt(800, 760, 1.5)
        sun(1250, 240, 65)
        for x in (600, 1000):
            draw.rounded_rectangle(
                (x - 20, 335, x + 20, 440), 9, fill=GOLD, outline=INK, width=5
            )
        for x in (370, 1230):
            arrow((x, 1040), (x + 40, 740), BLUE, 10)
    return image


def annotate_motion(image: Image.Image, index: int) -> Image.Image:
    """Explanatory vector symbols over original 3D stills; never a fluid simulation."""
    image = image.copy()
    draw = ImageDraw.Draw(image)
    if index == 4:
        x, y, radius = 1370, 170, 62
        for i in range(12):
            angle = i * math.tau / 12
            draw.line(
                [
                    (
                        x + (radius + 18) * math.cos(angle),
                        y + (radius + 18) * math.sin(angle),
                    ),
                    (
                        x + (radius + 42) * math.cos(angle),
                        y + (radius + 42) * math.sin(angle),
                    ),
                ],
                fill=GOLD,
                width=10,
            )
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=GOLD,
            outline=INK,
            width=6,
        )
        for y in (630, 790, 950):
            points = [(120 + i * 10, y + 18 * math.sin(i / 6)) for i in range(29)]
            draw.line(points, fill="#277783", width=10, joint="curve")
            end_x, end_y = points[-1]
            draw.line(
                (end_x - 35, end_y - 22, end_x, end_y, end_x - 35, end_y + 22),
                fill="#277783",
                width=10,
            )
    return image


def prepare(root: Path, art_dir: Path | None = None):
    root.mkdir(parents=True, exist_ok=True)
    assets = root / "illustrations"
    assets.mkdir(exist_ok=True)
    story = {"title": "Chiếc áo khô: nước đi đâu?", "profile": "family", "scenes": []}
    for index, (title, narration, style) in enumerate(SPEECH):
        path = assets / f"scene-{index + 1:02}.png"
        source_name = {0: "wet.png", 3: "cup.png", 4: "dry.png", 7: "dry.png"}.get(
            index
        )
        if art_dir and source_name:
            source = art_dir / source_name
            with Image.open(source) as image:
                if image.width < 1600 or image.height < 1400:
                    raise ValueError("Review 3D source must be at least 1600×1400.")
                annotate_motion(image.convert("RGB"), index).save(path)
        else:
            artwork(index).save(path)
        story["scenes"].append(
            {
                "title": title,
                "narration": narration,
                "style": style,
                "illustration": str(path.relative_to(root)),
                "illustration_source": "Original Blender Cycles CPU"
                if art_dir and source_name
                else "Original Pillow vector-style art",
                "illustration_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "caption_style": CAPTIONS[index][0],
                "caption_emphasis": CAPTIONS[index][1],
            }
        )
    (root / "story.json").write_text(
        json.dumps(story, ensure_ascii=False, indent=2) + "\n"
    )


def contact_sheet(root: Path, aspect: str, scenes: list[dict]):
    size = (270, 480) if aspect == "portrait" else (480, 270)
    count = len(scenes) * 3
    sheet = Image.new(
        "RGB", (size[0] * 6, (size[1] + 28) * math.ceil(count / 6)), "white"
    )
    draw = ImageDraw.Draw(sheet)
    capture = cv2.VideoCapture(str(root / f"review-{aspect}.mp4"))
    elapsed = 0.0
    try:
        for index, scene in enumerate(scenes):
            for offset, fraction in enumerate((0.03, 0.5, 0.95)):
                timestamp = elapsed + scene["duration"] * fraction
                capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("Cannot extract review frame.")
                still = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if index == 0 and offset == 2:
                    still.save(root / f"poster-{aspect}.png")
                if index == len(scenes) - 1 and offset == 2:
                    still.save(root / f"ending-{aspect}.png")
                still.thumbnail(size)
                number = index * 3 + offset
                x, y = (number % 6) * size[0], (number // 6) * (size[1] + 28)
                sheet.paste(still, (x, y))
                draw.text((x + 4, y + size[1] + 3), f"{timestamp:.2f}s", fill="black")
            elapsed += scene["duration"]
    finally:
        capture.release()
    sheet.save(root / f"contact-{aspect}.jpg", quality=95)


def render(root: Path, aspect: str):
    story = json.loads((root / "story.json").read_text())
    tts = json.loads((root / "tts-provenance.json").read_text())
    store = Store(root / f"studio-{aspect}")
    p = store.create(
        ProjectInput(
            title=story["title"],
            profile="family",
            aspect=aspect,
            narration="\n".join(s["narration"] for s in story["scenes"]),
        ).model_dump()
    )
    p = store.save(
        p["id"],
        {
            **p,
            "scenes": [
                Scene(
                    title=s["title"],
                    narration=s["narration"],
                    style=s["style"],
                    caption_style=s.get("caption_style", "card"),
                    caption_emphasis=s.get("caption_emphasis", ""),
                ).model_dump()
                for s in story["scenes"]
            ],
        },
    )
    for index, scene in enumerate(p["scenes"]):
        source, voice = story["scenes"][index], tts["records"][index]
        assert voice["narration"] == scene["narration"]
        audio = (root / voice["file"]).read_bytes()
        assert hashlib.sha256(audio).hexdigest() == voice["sha256"]
        p = import_asset(
            store,
            p["id"],
            scene["id"],
            p["revision"],
            (root / source["illustration"]).read_bytes(),
        )
        p = import_asset(store, p["id"], scene["id"], p["revision"], audio)
    # Deliberate hold after each short spoken idea. Never stretch or truncate speech.
    for scene in p["scenes"]:
        scene["duration"] = max(4, scene["duration"] + 0.45)
    p = store.save(p["id"], p)
    job = enqueue(
        store,
        p["id"],
        ExportInput(
            revision=p["revision"], aspect=aspect, idempotency_key=str(uuid4())
        ),
    )
    started = time.monotonic()
    print(
        f"Rendering {aspect}, {len(p['scenes'])} scenes, {sum(s['duration'] for s in p['scenes']):.2f}s",
        flush=True,
    )
    render_job(store, store.claim())
    done = store.get("jobs", job["id"])
    assert done["state"] == "succeeded", done
    asset = store.get("assets", done["result_id"])
    target = root / f"review-{aspect}.mp4"
    shutil.copy2(store.asset_path(asset), target)
    contact_sheet(root, aspect, p["scenes"])
    report = {
        "aspect": aspect,
        "job_id": job["id"],
        "project": p,
        "video": target.name,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "probe": probe(target),
        "render_seconds": time.monotonic() - started,
        "sources": "Original procedural Blender/Pillow illustrations; bundled Noto OFL; VieNeu preset narration via explicit local review script; no voice cloning; no Tongjiang assets",
        "illustrations": [
            {
                k: s[k]
                for k in ("illustration", "illustration_source", "illustration_sha256")
            }
            for s in story["scenes"]
        ],
        "caption_timing": "one phrase per scene, not word alignment",
        "review": "Creator listening/content review pending",
    }
    (root / f"report-{aspect}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "output": str(target),
                "seconds": report["render_seconds"],
                "bytes": target.stat().st_size,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--art-dir", type=Path)
    parser.add_argument(
        "--aspect", choices=["portrait", "landscape", "both"], default="both"
    )
    args = parser.parse_args()
    if args.prepare:
        prepare(
            args.output_dir.resolve(), args.art_dir.resolve() if args.art_dir else None
        )
    else:
        for aspect in (
            ["portrait", "landscape"] if args.aspect == "both" else [args.aspect]
        ):
            render(args.output_dir.resolve(), aspect)
