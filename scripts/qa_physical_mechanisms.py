"""Original physical closeups for A04 engineering illustrations, not live AI art.

The six details are schematic explanatory visuals. Invisible water vapour is
indicated by colored dots/diffusion traces, NOT photorealistic rising steam.
No source images, logos, third-party model weights or fonts are reused.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

MECHANISM_CUES = (
    "Nước bay hơi",
    "Không khí",
    "Gió",
    "Ánh nắng",
    "Bóng râm",
    "Quan sát",
)

INK = "#294C49"
WATER = "#4E99B4"
THREAD = "#72AEB8"
GOLD = "#F3C76C"


def _weave(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, dry: bool) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 + 6, y1 + 14, x2 + 18, y2 + 20), 30, fill="#9FB9AC")
    draw.rounded_rectangle(
        box,
        29,
        fill="#DCCBA6" if dry else "#9ACFD5",
        outline=INK,
        width=7,
    )
    shade = "#B29C75" if dry else THREAD
    bright = "#F4E5BF" if dry else "#C7E7E8"
    for y in range(y1 + 22, y2 - 13, 20):
        draw.line((x1 + 18, y, x2 - 18, y - 3), fill=bright, width=5)
        draw.line((x1 + 22, y + 6, x2 - 21, y + 4), fill=shade, width=3)
    for x in range(x1 + 27, x2 - 13, 22):
        coords = [(x + round(3 * math.sin(y / 12)), y) for y in range(y1 + 16, y2 - 13, 10)]
        draw.line(coords, fill=shade, width=3, joint="curve")
    draw.arc((x1 + 15, y1 + 11, x2 - 15, y1 + 49), 0, 180, fill=bright, width=5)


def _bead(draw: ImageDraw.ImageDraw, x: int, y: int, radius: int = 14) -> None:
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill="#428DAF",
        outline="#2C6383",
        width=3,
    )
    draw.ellipse((x - radius // 2, y - radius // 2, x, y), fill="#E0F6F4")


def _air(draw: ImageDraw.ImageDraw, y: int, *, start: int = 50, end: int = 550) -> None:
    pts = [(x, round(y + 18 * math.sin((x - start) / 73))) for x in range(start, end, 9)]
    draw.line(pts, fill="#5BA9B3", width=8, joint="curve")
    draw.line([(x, yy + 7) for x, yy in pts], fill="#D6EEF0", width=3)


def _stages(draw: ImageDraw.ImageDraw) -> None:
    for i, x in enumerate((45, 233, 421)):
        _weave(draw, (x, 240, x + 152, 461), dry=i == 2)
        for j in range((5, 2, 0)[i]):
            _bead(draw, x + 38 + (j % 2) * 54, 310 + (j // 2) * 54, 11)
        if i < 2:
            _air(draw, 176 + i * 11, start=x + 40, end=x + 155)
    draw.line((197, 337, 228, 337), fill="#6C9C96", width=9)
    draw.polygon([(230, 337), (217, 326), (217, 348)], fill="#6C9C96")
    draw.line((386, 337, 418, 337), fill="#6C9C96", width=9)
    draw.polygon([(420, 337), (407, 326), (407, 348)], fill="#6C9C96")


def render_mechanism_detail(title: str) -> Image.Image:
    """Draw one 310×265 material-focused still for a recognized A04 narration cue."""
    if title not in MECHANISM_CUES:
        raise ValueError(f"No authored physical detail for cue: {title!r}")
    image = Image.new("RGB", (620, 530), "#EAF3E9")
    d = ImageDraw.Draw(image)
    for y in range(530):
        t = y / 529
        d.line(
            (0, y, 620, y),
            fill=(round(232 - 26 * t), round(246 - 15 * t), round(239 - 24 * t)),
        )
    d.ellipse((14, 427, 607, 558), fill="#D1DFD1")

    if title == "Quan sát":
        _stages(d)
    else:
        if title == "Gió":
            # Fabric is lifted diagonally rather than lying in a rigid icon box.
            d.polygon(
                [(69, 280), (549, 238), (565, 453), (90, 486)],
                fill="#9ACFD5",
                outline=INK,
                width=7,
            )
            for i in range(12):
                x = 105 + i * 37
                d.line((x, 288 - i * 3, x + 22, 450 - i * 2), fill="#70ACB9", width=4)
            for y in (92, 158, 225):
                _air(d, y)
            for x, y in ((90, 201), (503, 105), (457, 210)):
                d.ellipse(
                    (x - 17, y - 7, x + 17, y + 7),
                    fill="#89B880",
                    outline="#5E916F",
                    width=3,
                )
                d.line((x - 20, y + 12, x + 18, y - 12), fill="#578968", width=3)
        else:
            _weave(d, (42, 239, 571, 476), dry=False)

        if title == "Nước bay hơi":
            for x, y, r in ((170, 351, 17), (307, 392, 13), (441, 329, 16), (529, 404, 10)):
                _bead(d, x, y, r)
            # Gas is invisible: particles indicate diffusion, NOT visible boiling steam.
            for i, x in enumerate((172, 285, 410, 525)):
                for j in range(4):
                    y = 196 - j * 39 - i % 2 * 12
                    r = 7 - j
                    d.ellipse(
                        (x + j * 7 - r, y - r, x + j * 7 + r, y + r),
                        fill="#7DBBBF",
                    )
            for x in (160, 388):
                d.arc((x - 28, 90, x + 60, 225), 245, 350, fill="#8ABBB7", width=6)

        elif title == "Không khí":
            for y in (90, 157, 215):
                _air(d, y)
            for x, y in ((135, 330), (302, 360), (474, 350)):
                _bead(d, x, y, 13)
            for i in range(6):
                x = 104 + i * 82
                y = 76 + (i % 3) * 36
                d.ellipse(
                    (x - 9, y - 9, x + 9, y + 9),
                    fill="#91C6C6",
                    outline="#619AA1",
                    width=3,
                )

        elif title == "Ánh nắng":
            d.ellipse((456, 21, 574, 139), fill=GOLD, outline="#BCA25F", width=7)
            for x in (205, 325, 445, 558):
                d.polygon([(497, 135), (x - 32, 298), (x + 19, 300)], fill="#F7DF9B")
            for x, y in ((170, 330), (330, 345), (484, 365)):
                d.line((x - 28, y + 19, x + 21, y - 31), fill="#FFF3C9", width=12)
                d.line((x - 35, y + 35, x + 28, y + 35), fill="#83B5B2", width=5)
            d.arc((58, 117, 228, 286), 195, 312, fill="#C4A15C", width=8)

        elif title == "Bóng râm":
            d.polygon(
                [(0, 0), (620, 0), (620, 114), (502, 155), (388, 98), (255, 165), (142, 121), (0, 175)],
                fill="#81AE89",
            )
            for x, y in ((70, 127), (193, 116), (348, 94), (487, 119), (571, 156)):
                d.ellipse(
                    (x - 70, y - 68, x + 70, y + 48),
                    fill="#95BC90",
                    outline="#6E9A77",
                    width=5,
                )
            d.rounded_rectangle(
                (42, 242, 571, 467),
                29,
                fill="#9FC3C6",
                outline=INK,
                width=7,
            )
            for x in range(65, 545, 20):
                d.line((x, 265, x + 13, 446), fill="#81ADB0", width=3)
            for y in (192, 232):
                _air(d, y, start=136, end=512)
            d.ellipse((95, 318, 262, 405), fill="#87AF9C", outline="#749E8C", width=4)

    return image.resize((310, 265), Image.Resampling.LANCZOS)
