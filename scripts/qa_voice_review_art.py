"""Original cue-specific illustrations for the A04 Vietnamese wet-shirt *test fixture*.

Not AI imagery, a licensed asset collection, a physics simulation, or creator approval.
The recurring shirt intentionally preserves subject continuity, while visible props,
actions and wetness stages make each spoken cue distinguishable in the final MP4.
"""

from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageOps

from qa_rich_context_art import (
    cue_fabric_effects,
    garment_detail,
    landscape_environment,
    portrait_environment,
)

# fmt: off
# Coordinate-rich source illustration is kept stable for pixel/edge regressions.
INK = '#29463d'
BLUE = '#408fb2'
YELLOW = '#f4c967'
BG = '#fff9ed'

# A scene must depict its *action*, not merely change the tint of a generic shape.
VISUAL_INTENTS: dict[str, tuple[str, ...]] = {
    'Câu hỏi': ('wet_shirt', 'question'),
    'Nước bay hơi': ('wet_shirt', 'rising_water_vapor'),
    'Không khí': ('wet_shirt', 'air_transport'),
    'Gió': ('wet_shirt', 'wind'),
    'Ánh nắng': ('shirt', 'sun'),
    'Nhiệt độ': ('shirt', 'thermometer'),
    'Trải áo': ('spread_shirt', 'clothesline'),
    'Đừng gấp': ('wet_shirt', 'crossed_fold'),
    'Bóng râm': ('shirt', 'shade_tree'),
    'Không cần sôi': ('shirt', 'crossed_boiling_pot'),
    'Quan sát': ('wet_to_dry_shirt', 'clock'),
    'Tổng kết': ('dry_shirt', 'checkmark'),
}


def _arrow(draw: ImageDraw.ImageDraw, x: int, y: int, dx: int, dy: int, color: str = BLUE) -> None:
    dest = (x + dx, y + dy)
    draw.line((x, y, *dest), fill=color, width=16, joint='curve')
    if abs(dx) >= abs(dy):
        tip = -1 if dx > 0 else 1
        draw.polygon((dest, (dest[0] + tip * 43, dest[1] - 25),
                      (dest[0] + tip * 43, dest[1] + 25)), fill=color)
    else:
        tip = -1 if dy > 0 else 1
        draw.polygon((dest, (dest[0] - 25, dest[1] + tip * 43),
                      (dest[0] + 25, dest[1] + tip * 43)), fill=color)


def _drop(draw: ImageDraw.ImageDraw, x: int, y: int, r: int = 25) -> None:
    draw.polygon(((x, y - r * 2), (x - r, y), (x + r, y)), fill=BLUE)
    draw.ellipse((x - r, y - r // 4, x + r, y + r * 2), fill=BLUE,
                 outline=INK, width=3)


def _shirt(draw: ImageDraw.ImageDraw, *, wet: int, spread: bool = False,
           origin: tuple[int, int] = (325, 275), scale: float = 1.0) -> None:
    ox, oy = origin
    # Open arms/hem remain recognizable on both horizontal/vertical exports.
    coords = [(65, 20), (155, 0), (218, 75), (302, 75), (360, 0),
              (450, 20), (548, 183), (425, 245), (425, 525),
              (100, 525), (100, 245), (-28, 183)]
    if spread:
        coords = [(round((x - 260) * 1.12 + 260), y) for x, y in coords]
    points = [(ox + round(x * scale), oy + round(y * scale)) for x, y in coords]
    draw.polygon(points, fill='#a4d2d9' if wet else '#f1d9a5', outline=INK,
                 width=max(4, int(12 * scale)))
    draw.arc((ox + round(174 * scale), oy + round(-4 * scale),
              ox + round(293 * scale), oy + round(105 * scale)),
             5, 175, fill=INK, width=max(3, int(10 * scale)))
    for i in range(wet):
        _drop(draw, ox + round((145 + (i % 3) * 105) * scale),
              oy + round((240 + (i // 3) * 135) * scale),
              max(6, round(22 * scale)))


def _sun(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    r = 95
    draw.ellipse((x-r, y-r, x+r, y+r), fill=YELLOW, outline=INK, width=9)
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(-1,-1),(1,-1)):
        draw.line((x+dx*125,y+dy*125,x+dx*175,y+dy*175),fill=YELLOW,width=17)


def _cloud(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    for dx, dy, r in ((-95,18,83),(-20,-45,105),(95,-15,85)):
        draw.ellipse((x+dx-r,y+dy-r,x+dx+r,y+dy+r),fill='#c7e5eb',outline=INK,width=7)
    draw.rounded_rectangle((x-180,y,x+185,y+95),30,fill='#c7e5eb',outline=INK,width=7)


def _cross(draw: ImageDraw.ImageDraw, x: int, y: int, r: int = 140) -> None:
    draw.ellipse((x-r,y-r,x+r,y+r),outline='#bc594e',width=21)
    draw.line((x-r*0.7,y+r*0.7,x+r*0.7,y-r*0.7),fill='#bc594e',width=23)


def _check(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.ellipse((x-140,y-140,x+140,y+140),fill='#e0f3de',outline='#5b9f72',width=16)
    draw.line((x-85,y,x-22,y+63,x+105,y-91),fill='#438658',width=28,joint='curve')


def _draw_context(draw: ImageDraw.ImageDraw, title: str) -> None:
    if title == 'Câu hỏi':
        draw.arc((920,305,1190,600),195,540,fill=INK,width=32)
        draw.ellipse((1042,672,1080,710),fill=INK)
    elif title == 'Nước bay hơi':
        for x in (955,1080,1210):
            _arrow(draw,x,675,0,-250)
    elif title == 'Không khí':
        _cloud(draw,1060,340)
        for y in (625,740):
            _arrow(draw,900,y,270,0)
    elif title == 'Gió':
        for y in (400,545,690):
            draw.arc((880,y-65,1190,y+65),-75,100,fill=BLUE,width=14)
            _arrow(draw,1115,y,125,0)
    elif title == 'Ánh nắng':
        _sun(draw,1070,440)
    elif title == 'Nhiệt độ':
        draw.rounded_rectangle((1028,325,1108,625),38,fill='#e7e4dd',outline=INK,width=10)
        draw.ellipse((998,576,1138,716),fill='#e98d7d',outline=INK,width=8)
        draw.rectangle((1054,425,1084,620),fill='#e98d7d')
        for y in (380,460,540):
            draw.line((1110,y,1160,y),fill=INK,width=8)
        _arrow(draw,925,730,0,-130,'#d57967')
    elif title == 'Trải áo':
        draw.line((165,230,1250,230),fill=INK,width=13)
        for x in (414,731):
            draw.rounded_rectangle((x,218,x+42,285),8,fill=YELLOW,outline=INK,width=6)
        _arrow(draw,1060,545,0,-180)
    elif title == 'Đừng gấp':
        draw.rounded_rectangle((960,420,1200,660),25,fill='#a4d2d9',outline=INK,width=14)
        draw.line((972,545,1186,545),fill=INK,width=12)
        _cross(draw,1080,545,155)
    elif title == 'Bóng râm':
        draw.rectangle((1070,495,1122,785),fill='#92714d')
        for x,y,r in ((970,450,110),(1090,385,125),(1180,475,115)):
            draw.ellipse((x-r,y-r,x+r,y+r),fill='#7eba86',outline=INK,width=9)
        draw.ellipse((880,790,1270,870),fill='#cadcc5')
    elif title == 'Không cần sôi':
        draw.rounded_rectangle((960,470,1190,680),35,fill='#aec6d0',outline=INK,width=12)
        draw.line((935,480,1210,480),fill=INK,width=15)
        for x in (1010,1090,1160):
            draw.arc((x-30,325,x+20,460),195,350,fill=BLUE,width=8)
        _cross(draw,1075,540,172)
    elif title == 'Quan sát':
        draw.ellipse((970,380,1230,640),fill='#fffef9',outline=INK,width=14)
        draw.line((1100,510,1100,410),fill=INK,width=13)
        draw.line((1100,510,1160,550),fill=INK,width=13)
        _arrow(draw,920,730,290,0)
    elif title == 'Tổng kết':
        _check(draw,1080,510)


def render_cue_art(title: str) -> bytes:
    """Return real PNG bytes for a recognized 12-scene spoken cue; fail closed otherwise."""
    if title not in VISUAL_INTENTS:
        raise ValueError(f'No authored visual semantics for cue: {title!r}')
    image = Image.new('RGB', (1400,1000), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((100,100,1300,890),radius=45,
                           fill='#f9f6ec',outline='#deded0',width=10)
    landscape_environment(draw, title)
    draw.line((185,855,1215,855),fill=INK,width=11)
    wet_levels = {'Câu hỏi':5,'Nước bay hơi':4,'Không khí':4,'Gió':3,
                  'Ánh nắng':2,'Nhiệt độ':2,'Trải áo':2,'Đừng gấp':3,
                  'Bóng râm':1,'Không cần sôi':1,'Quan sát':1,'Tổng kết':0}
    _shirt(draw,wet=wet_levels[title],spread=title=='Trải áo')
    garment_detail(draw, origin=(325, 275), scale=1.0, wet=wet_levels[title],
                   spread=title == 'Trải áo')
    cue_fabric_effects(draw, title, portrait=False)
    _draw_context(draw,title)
    buffer = io.BytesIO()
    image.save(buffer,format='PNG')
    return buffer.getvalue()

# Portrait A04 test media must not use the landscape illustration through
# Scene.visual_fit='cover': it hid the shirt and most of the narrated objects.
# Separate, reproducible vertical composition retains both subject and action.
_PORTRAIT_CONTEXT_CROPS = {
    "Câu hỏi": (935, 290, 1210, 750),
    "Nước bay hơi": (920, 340, 1290, 750),
    "Không khí": (880, 240, 1290, 830),
    "Gió": (880, 290, 1280, 820),
    "Ánh nắng": (880, 225, 1290, 720),
    "Nhiệt độ": (910, 280, 1210, 780),
    "Trải áo": (910, 370, 1190, 740),
    "Đừng gấp": (880, 330, 1290, 780),
    "Bóng râm": (895, 210, 1290, 840),
    "Không cần sôi": (890, 280, 1290, 790),
    "Quan sát": (910, 320, 1250, 790),
    "Tổng kết": (900, 330, 1260, 700),
}
_WET_STAGE = {
    "Câu hỏi": 5,
    "Nước bay hơi": 4,
    "Không khí": 4,
    "Gió": 3,
    "Ánh nắng": 2,
    "Nhiệt độ": 2,
    "Trải áo": 2,
    "Đừng gấp": 3,
    "Bóng râm": 1,
    "Không cần sôi": 1,
    "Quan sát": 1,
    "Tổng kết": 0,
}


def render_portrait_cue_art(title: str) -> bytes:
    """One large continuous yard scene with a contextual inset, not two empty cards.

    Storyboard titles and captions are composed by Studio, not embedded in art.
    Still a procedural engineering visual, not approved AI imagery or creator G10.
    """
    if title not in VISUAL_INTENTS:
        raise ValueError(f"No authored visual semantics for cue: {title!r}")
    original = Image.open(io.BytesIO(render_cue_art(title))).convert("RGB")
    output = Image.new("RGB", (1000, 1600), BG)
    draw = ImageDraw.Draw(output)
    portrait_environment(draw, title)
    wet = _WET_STAGE[title]
    _shirt(draw, wet=wet, origin=(250, 398), scale=0.96, spread=title == "Trải áo")
    garment_detail(
        draw, origin=(250, 398), scale=0.96, wet=wet, spread=title == "Trải áo"
    )
    cue_fabric_effects(draw, title, portrait=True)
    # A scene-specific observed mechanism appears as a small visual note on the
    # yard instead of occupying an isolated half-height second card.
    detail = original.crop(_PORTRAIT_CONTEXT_CROPS[title])
    detail = ImageOps.contain(detail, (310, 265), Image.Resampling.LANCZOS)
    note = (555, 952, 896, 1270)
    draw.rounded_rectangle(note, radius=24, fill="#F7F4EB", outline="#C9D1BF", width=6)
    output.paste(detail, (note[0] + (341 - detail.width) // 2,
                          note[1] + (318 - detail.height) // 2))
    buffer = io.BytesIO()
    output.save(buffer, "PNG")
    return buffer.getvalue()
