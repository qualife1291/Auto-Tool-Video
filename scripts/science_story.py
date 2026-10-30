"""Original, typed educational motion templates. Not a molecular/cloth physics simulation."""

import argparse
import functools
import json
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

STORY = [
    (
        "Nước đã đi đâu?",
        "Áo vừa giặt còn ướt. Một lúc sau lại khô. Nước đã đi đâu?",
        "hook",
        "shirt",
        "Nước",
        "Áo ướt lớn ở trung tâm; zoom nhẹ vào giọt nước; nối sang sợi vải.",
    ),
    (
        "Nhìn vào sợi vải",
        "Nước thấm giữa các sợi vải. Ta cùng phóng to để xem nhé!",
        "context",
        "weave",
        "sợi vải",
        "Giữ áo làm bối cảnh; vẽ lần lượt các sợi dọc, ngang; nước nằm trong khe dệt.",
    ),
    (
        "Những phần tử rất nhỏ",
        "Nước gồm những phần tử rất nhỏ, gọi là các phân tử.",
        "explain",
        "molecules",
        "phân tử",
        "Vẽ khung nước và bề mặt; các chấm phân tử rung nhẹ, ghi rõ phóng đại minh họa.",
    ),
    (
        "Thoát khỏi bề mặt",
        "Ở bề mặt, một số phân tử nước thoát vào không khí.",
        "explain",
        "escape",
        "bề mặt",
        "Các chấm trong nước chuyển động nhẹ; một số rời bề mặt theo đường cong rồi mờ dần.",
    ),
    (
        "Đó là bay hơi",
        "Nước lỏng chuyển thành hơi nước. Quá trình này gọi là bay hơi.",
        "explain",
        "evaporation",
        "bay hơi",
        "Bề mặt nước còn nguyên; mũi tên và phân tử nối vùng nước với vùng không khí.",
    ),
    (
        "Hơi nước thường vô hình",
        "Hơi nước thường vô hình. Những chấm xanh chỉ là hình minh họa.",
        "context",
        "invisible",
        "vô hình",
        "Các chấm minh họa mờ dần; áo và không gian vẫn rõ, không dựng mây hơi nhìn thấy.",
    ),
    (
        "Không cần nước sôi",
        "Bay hơi không cần nước sôi. Áo trong nhà vẫn có thể khô.",
        "example",
        "room",
        "không cần nước sôi",
        "Không gian trong nhà với áo và cốc nước thường; bề mặt không có bọt sôi hoặc khói.",
    ),
    (
        "Nhiệt độ có ảnh hưởng",
        "Nơi ấm thường giúp nước bay hơi nhanh hơn. Nhưng còn một yếu tố nữa!",
        "explain",
        "warm",
        "Nơi ấm",
        "Ánh sáng ấm tăng nhẹ; áo và dòng phân tử sơ đồ vẫn liên tục, không đổi màu áo.",
    ),
    (
        "Gió giúp như thế nào?",
        "Gió đưa không khí ẩm quanh áo đi, giúp nước tiếp tục bay hơi.",
        "explain",
        "wind",
        "không khí ẩm",
        "Bốn luồng khí cong đi qua áo; chấm sơ đồ rời vùng sát vải theo hướng gió.",
    ),
    (
        "Khi không khí quá ẩm",
        "Không khí quá ẩm thường làm áo lâu khô hơn, ngay cả khi trời nóng.",
        "explain",
        "humidity",
        "quá ẩm",
        "So hai vùng không khí ít ẩm/nhiều ẩm; mật độ chấm khác nhau được ghi là minh họa.",
    ),
    (
        "Trải áo rộng, treo nơi thoáng",
        "Trải áo rộng, treo nơi thoáng, để nhiều bề mặt tiếp xúc với không khí.",
        "example",
        "spread",
        "Trải áo rộng",
        "So cùng áo gấp và trải; vẽ mép vải, khe gấp và mũi tên diện tích tiếp xúc.",
    ),
    (
        "Nước vẫn ở quanh ta",
        "Nước không biến mất: nó chuyển vào không khí. Bạn thử quan sát chiếc khăn ướt nhé!",
        "payoff",
        "dry",
        "không biến mất",
        "Trở về đúng chiếc áo xanh đã khô; gió nhẹ tiếp diễn; kết ngay sau lời, không giữ im lặng dài.",
    ),
]
INK, BLUE, GOLD, CORAL = "#173D33", "#55ADBE", "#F3BE57", "#DF886E"
FONT = Path(__file__).resolve().parents[1] / "assets/fonts/NotoSans-Bold.ttf"


def prepare(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    scenes = []
    for title, narration, role, template, emphasis, action in STORY:
        scenes.append(
            {
                "title": title,
                "narration": narration,
                "role": role,
                "template": template,
                "caption_emphasis": emphasis,
                "visual_description": action,
                "reveal_order": action.split(";"),
                "source_refs": [],
                "fact_flags": [
                    "Sơ đồ phân tử phóng đại, không mô phỏng vật lý định lượng."
                ],
                "begin": action.split(";")[0],
                "middle": action,
                "end": "Nối hình nhẹ sang ý tiếp; lời theo audio thực.",
            }
        )
    (root / "story.json").write_text(
        json.dumps(
            {"title": "Áo khô: nước đã đi đâu?", "profile": "family", "scenes": scenes},
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


@functools.lru_cache(maxsize=24)
def face(size):
    return ImageFont.truetype(str(FONT), size)


class Art:
    def __init__(self, width, height, art_dir, template, supersample=2):
        self.width, self.height, self.ss = width, height, supersample
        self.landscape, self.template = width > height, template
        self.scale = width / (1920 if self.landscape else 1080)
        self.unit = self.scale * supersample
        self.size = (width * supersample, height * supersample)
        top = np.array((227, 244, 239), dtype=float)
        bottom = np.array((251, 238, 212), dtype=float)
        if template == "warm":
            top = np.array((251, 238, 206), dtype=float)
        gradient = np.linspace(0, 1, self.size[1])[:, None]
        pixels = np.repeat(
            (top * (1 - gradient) + bottom * gradient)[:, None, :], self.size[0], axis=1
        ).astype(np.uint8)
        self.base = Image.fromarray(pixels).convert("RGBA")
        d = ImageDraw.Draw(self.base)
        d.ellipse(
            self.box(-500, 900 if not self.landscape else 530, 2600, 2300),
            fill="#D4E8D7",
        )
        d.ellipse(
            self.box(-400, 1420 if not self.landscape else 860, 2500, 2400),
            fill="#C3DEC9",
        )
        target_width = round((1300 if self.landscape else 1600) * self.unit)
        self.shirts = []
        for name in ("wet", "dry"):
            with Image.open(art_dir / f"{name}.png") as image:
                if image.mode != "RGBA" or image.getextrema()[3][0] != 0:
                    raise ValueError(
                        "Use original transparent Blender renders, not rectangular background images."
                    )
                self.shirts.append(
                    image.resize(
                        (
                            target_width,
                            round(image.height * target_width / image.width),
                        ),
                        Image.Resampling.LANCZOS,
                    )
                )
        self.rng = random.Random(20261030)
        self.particles = [
            (
                self.rng.uniform(-0.9, 0.9),
                self.rng.uniform(0.1, 0.9),
                self.rng.random() * math.tau,
            )
            for _ in range(45)
        ]

    def box(self, *coords):
        return tuple(round(v * self.unit) for v in coords)

    def text(self, draw, xy, text, size=42, color=INK, anchor=None):
        draw.text(
            self.box(*xy),
            text,
            font=face(max(12, round(size * self.unit))),
            fill=color,
            anchor=anchor,
        )

    def line(self, draw, points, color=INK, width=5):
        draw.line(
            [self.box(*p) for p in points],
            fill=color,
            width=max(1, round(width * self.unit)),
            joint="curve",
        )

    def arrow(self, draw, a, b, color=BLUE, width=7):
        self.line(draw, [a, b], color, width)
        angle = math.atan2(b[1] - a[1], b[0] - a[0])
        pts = [b] + [
            (b[0] - 24 * math.cos(angle + q), b[1] - 24 * math.sin(angle + q))
            for q in (-0.55, 0.55)
        ]
        draw.polygon([self.box(*p) for p in pts], fill=color)

    def shirt(self, frame, t, dry=False, mini=False):
        source = self.shirts[1 if dry else 0]
        x, y = (-80, -25) if self.landscape else (-260, 170)
        if mini:
            source = source.resize(
                (round(source.width * 0.49), round(source.height * 0.49)),
                Image.Resampling.LANCZOS,
            )
            x, y = (1040, 150) if self.landscape else (400, 610)
        # Half-pixel positioning through supersampling; no integer resize zoom on each frame.
        frame.alpha_composite(source, self.box(x, y))

    def circle_area(self):
        return (1350, 490, 285) if self.landscape else (540, 830, 390)

    def weave(self, draw, p, t):
        cx, cy, radius = self.circle_area()
        draw.ellipse(
            self.box(cx - radius, cy - radius, cx + radius, cy + radius),
            fill="#F5F6E4",
            outline=INK,
            width=round(6 * self.unit),
        )
        span = radius * 0.68
        for i in range(9):
            x = cx - span + i * span / 4
            end = max(0, min(1, p * 2.2 - i * 0.055))
            ys = np.linspace(cy - span, cy - span + 2 * span * end, 50)
            self.line(
                draw,
                [(x + 8 * math.sin((yy - cy) / 70 + i), yy) for yy in ys],
                "#68A8AF",
                24,
            )
        for i in range(9):
            y = cy - span + i * span / 4
            end = max(0, min(1, p * 2.2 - 0.35 - i * 0.045))
            xs = np.linspace(cx - span, cx - span + 2 * span * end, 50)
            self.line(
                draw,
                [(xx, y + 8 * math.sin((xx - cx) / 70 + i)) for xx in xs],
                "#94C6C2",
                18,
            )
        for i in range(12):
            x = cx + math.sin(i * 7) * span * 0.85
            y = cy + math.cos(i * 5) * span * 0.8 + math.sin(t + i) * 3
            r = 13 + i % 3 * 3
            draw.ellipse(
                self.box(x - r, y - r, x + r, y + r),
                fill="#409DB7",
                outline="#237D92",
                width=round(3 * self.unit),
            )
        self.text(
            draw, (cx, cy + radius + 30), "Nước giữa các sợi vải", 42, anchor="mt"
        )

    def molecular(self, frame, draw, p, t, invisible=False):
        cx, cy = (1330, 530) if self.landscape else (540, 900)
        w, h = (750, 240) if self.landscape else (850, 270)
        draw.rounded_rectangle(
            self.box(cx - w / 2, cy, cx + w / 2, cy + h),
            radius=round(30 * self.unit),
            fill="#7AC5CE",
            outline="#358E9E",
            width=round(5 * self.unit),
        )
        self.line(draw, [(cx - w / 2, cy), (cx + w / 2, cy)], "#237D92", 8)
        for x, y, phase in self.particles:
            px = cx + x * w * 0.44 + math.sin(t * 2 + phase) * 5
            py = cy + y * h * 0.9 + math.cos(t * 2 + phase) * 5
            draw.ellipse(
                self.box(px - 9, py - 9, px + 9, py + 9),
                fill="#E5F8F3",
                outline="#2B8296",
                width=round(2 * self.unit),
            )
        if self.template != "molecules":
            layer = Image.new("RGBA", self.size)
            d = ImageDraw.Draw(layer)
            for i in range(7):
                phase = (t * 0.32 + i * 0.137) % 1
                px = cx + (i - 3) * w / 8 + math.sin(phase * math.pi) * 35
                py = cy - 420 * phase
                opacity = int(220 * math.sin(math.pi * phase))
                if invisible:
                    opacity = round(opacity * max(0, 1 - p * 1.6))
                d.ellipse(
                    self.box(px - 12, py - 12, px + 12, py + 12),
                    fill=(47, 140, 166, opacity),
                )
            frame.alpha_composite(layer)
            self.arrow(
                draw,
                (cx - w * 0.42, cy - 10),
                (cx - w * 0.42 + 35, cy - 220),
                "#4B94A1",
            )
        self.text(draw, (cx, cy - 360), "Không khí", 42, anchor="mt")
        self.text(draw, (cx, cy + h + 20), "Phóng đại minh họa", 34, anchor="mt")

    def frame(self, t, duration):
        p = t / max(0.01, duration)
        frame = self.base.copy()
        d = ImageDraw.Draw(frame)
        kind = self.template
        if kind in {"shirt", "dry", "warm", "wind", "room", "invisible"}:
            self.shirt(frame, t, dry=kind in {"dry", "invisible"})
        if kind in {"weave", "molecules", "escape", "evaporation"}:
            if self.landscape:
                self.shirt(frame, t)
            if kind == "weave":
                self.weave(d, p, t)
            else:
                self.molecular(frame, d, p, t)
        if kind == "invisible":
            if self.landscape:
                self.text(d, (1350, 330), "Hơi nước thường vô hình", 44, anchor="mt")
            layer = Image.new("RGBA", self.size)
            dots = ImageDraw.Draw(layer)
            for i in range(12):
                x = (1250 + i % 4 * 100) if self.landscape else 260 + i % 4 * 180
                y = (480 + i // 4 * 80) if self.landscape else 500 + i // 4 * 90
                a = round(200 * max(0, 1 - p * 1.8))
                dots.ellipse(
                    self.box(x - 12, y - 12, x + 12, y + 12), fill=(40, 130, 160, a)
                )
            frame.alpha_composite(layer)
        if kind in {"warm", "dry", "shirt"}:
            sx, sy = (1650, 250) if self.landscape else (890, 430)
            for i in range(12):
                a = i * math.tau / 12 + t * 0.07
                self.line(
                    d,
                    [
                        (sx + 95 * math.cos(a), sy + 95 * math.sin(a)),
                        (sx + 125 * math.cos(a), sy + 125 * math.sin(a)),
                    ],
                    GOLD,
                    8,
                )
            d.ellipse(
                self.box(sx - 70, sy - 70, sx + 70, sy + 70),
                fill=GOLD,
                outline="#CE9F41",
                width=round(4 * self.unit),
            )
        if kind in {"wind", "dry"}:
            for j in range(4):
                y = (340 + j * 100) if self.landscape else 600 + j * 150
                x0 = 40 if not self.landscape else 1000
                length = 950 if not self.landscape else 780
                points = [
                    (x0 + i * length / 80, y + 24 * math.sin(i / 10 - t * 2 + j))
                    for i in range(81)
                ]
                self.line(d, points, "#528F99", 7)
                for k in range(3):
                    u = (t * 0.23 + k * 0.31 + j * 0.09) % 1
                    x = x0 + u * length
                    y1 = y + 24 * math.sin(u * 8 - t * 2 + j)
                    self.arrow(d, (x - 18, y1), (x + 16, y1), "#397D8E", 6)
            self.text(
                d,
                (1350, 790) if self.landscape else (540, 1240),
                "Không khí được trao đổi",
                38,
                anchor="mt",
            )
        if kind == "room":
            x, y = (1260, 420) if self.landscape else (750, 960)
            d.rounded_rectangle(
                self.box(x - 110, y, x + 110, y + 220),
                radius=round(25 * self.unit),
                fill="#C0E3DE",
                outline=INK,
                width=round(6 * self.unit),
            )
            d.ellipse(
                self.box(x - 110, y - 35, x + 110, y + 35),
                fill="#64B2C4",
                outline=INK,
                width=round(5 * self.unit),
            )
            if self.landscape:
                self.text(d, (1350, 260), "Nước chưa sôi vẫn bay hơi", 40, anchor="mt")
        if kind == "humidity":
            for panel, (label, count) in enumerate([("Ít ẩm", 12), ("Nhiều ẩm", 40)]):
                cx = (580 + panel * 800) if self.landscape else 290 + panel * 500
                cy = 510 if self.landscape else 850
                r = 290 if self.landscape else 225
                d.rounded_rectangle(
                    self.box(cx - r, cy - 300, cx + r, cy + 300),
                    radius=round(35 * self.unit),
                    fill="#E8F4EC",
                    outline="#7AA79D",
                    width=round(4 * self.unit),
                )
                for i in range(count):
                    x = cx + math.sin(i * 17) * r * 0.75 + math.sin(t + i) * 3
                    y = cy + math.cos(i * 23) * 210 + math.cos(t + i) * 3
                    d.ellipse(self.box(x - 9, y - 9, x + 9, y + 9), fill="#4FABC2")
                self.text(d, (cx, cy + 330), label, 44, anchor="mt")
            self.text(
                d,
                (960, 160) if self.landscape else (540, 410),
                "Mật độ chấm: minh họa",
                34,
                anchor="mt",
            )
        if kind == "spread":
            self.shirt(frame, t, dry=True, mini=True)
            x, y = (500, 540) if self.landscape else (260, 910)
            for j in range(4):
                d.rounded_rectangle(
                    self.box(
                        x - 175 + j * 6,
                        y - 80 + j * 20,
                        x + 175 - j * 6,
                        y + 80 + j * 20,
                    ),
                    radius=round(18 * self.unit),
                    fill="#65B3C3",
                    outline="#348398",
                    width=round(4 * self.unit),
                )
            self.text(d, (x, y + 210), "Gấp lại", 42, anchor="mt")
            self.text(
                d,
                (1460, 770) if self.landscape else (780, 1220),
                "Trải rộng",
                42,
                anchor="mt",
            )
            self.arrow(d, (x + 190, y - 130), (x + 300, y - 150), CORAL, 7)
        image = frame.convert("RGB").resize(
            (self.width, self.height), Image.Resampling.LANCZOS
        )
        # Continuous camera transform after antialiasing, never integer-size resize steps.
        zoom = 1 + 0.012 * p * p * (3 - 2 * p)
        return image.transform(
            image.size,
            Image.Transform.AFFINE,
            (
                1 / zoom,
                0,
                self.width * (1 - 1 / zoom) / 2,
                0,
                1 / zoom,
                self.height * (1 - 1 / zoom) / 2,
            ),
            Image.Resampling.BICUBIC,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output_dir)
