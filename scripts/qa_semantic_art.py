"""Scene-specific offline Pillow illustrations for technical regression videos.

Engineering pictograms only: never claim human approval or final AI art quality.
"""

from __future__ import annotations

import io

from PIL import Image, ImageDraw

INK = "#224739"
BLUE = "#499CC1"
PALE = "#BDE4F1"
YELLOW = "#F4C45B"
GREEN = "#7FBA8C"
RED = "#D76F64"

# Every cue has explicit visible-object intent, not merely a different PNG hash.
EXPECTED_OBJECTS: dict[str, dict[str, tuple[str, ...]]] = {
    "water-12s": {
        "Giọt nước": ("drop",),
        "Bay hơi": ("water", "upward_vapor"),
        "Mây trắng": ("cloud", "upward_vapor"),
        "Mưa xuống": ("cloud", "rain", "water"),
    },
    "shirt-30s": {
        "Áo ướt": ("shirt", "water_drops"),
        "Ánh nắng": ("shirt", "sun"),
        "Gió thổi": ("shirt", "wind"),
        "Bay hơi": ("shirt", "upward_vapor"),
        "Trải rộng": ("spread_shirt", "wind"),
        "Áo khô": ("shirt", "dry_state"),
    },
    "traffic-45s": {
        "Dừng lại": ("sidewalk", "pedestrian"),
        "Quan sát": ("pedestrian", "look_both_ways"),
        "Lắng nghe": ("pedestrian", "vehicle", "sound_waves"),
        "Đèn đường": ("pedestrian_signal", "pedestrian"),
        "Vạch đi bộ": ("zebra_crossing", "pedestrian"),
        "Đi chậm": ("zebra_crossing", "walking_person"),
        "Tập trung": ("zebra_crossing", "pedestrian", "vehicle"),
        "Người lớn": ("adult", "child", "zebra_crossing"),
        "An toàn": ("pedestrian", "zebra_crossing", "safety_check"),
    },
    "energy-60s": {
        "Bắt đầu": ("lamp", "fan", "refrigerator"),
        "Bật đèn": ("lamp", "light_rays"),
        "Ánh sáng": ("window", "sun"),
        "Quạt mát": ("fan", "power_off"),
        "Máy lạnh": ("air_conditioner", "closed_door"),
        "Thiết bị": ("lamp", "fan", "phone"),
        "Sạc điện": ("phone", "unplugged_charger"),
        "Nấu ăn": ("pot", "lid"),
        "Tủ lạnh": ("refrigerator", "closed_door"),
        "Gia đình": ("adult", "child", "lamp"),
        "Việc nhỏ": ("switch", "safety_check"),
        "Tổng kết": ("lamp", "fan", "refrigerator", "safety_check"),
    },
}


def _drop(d: ImageDraw.ImageDraw, x: int, y: int, size: int = 90) -> None:
    d.polygon(
        [
            (x, y - size),
            (x - size * 2 // 3, y + size // 3),
            (x - size // 3, y + size),
            (x + size // 3, y + size),
            (x + size * 2 // 3, y + size // 3),
        ],
        fill=BLUE,
        outline=INK,
        width=7,
    )
    d.ellipse(
        (x - size * 2 // 3, y, x + size * 2 // 3, y + size * 4 // 3),
        fill=BLUE,
        outline=INK,
        width=7,
    )


def _arrow(
    d: ImageDraw.ImageDraw, x: int, y: int, dx: int, dy: int, color: str = BLUE
) -> None:
    d.line((x, y, x + dx, y + dy), fill=color, width=17, joint="curve")
    if abs(dx) > abs(dy):
        side = -1 if dx > 0 else 1
        d.polygon(
            [
                (x + dx, y + dy),
                (x + dx + side * 40, y + dy - 23),
                (x + dx + side * 40, y + dy + 23),
            ],
            fill=color,
        )
    else:
        side = -1 if dy > 0 else 1
        d.polygon(
            [
                (x + dx, y + dy),
                (x + dx - 23, y + dy + side * 40),
                (x + dx + 23, y + dy + side * 40),
            ],
            fill=color,
        )


def _sun(d: ImageDraw.ImageDraw, x: int, y: int, r: int = 100) -> None:
    d.ellipse((x - r, y - r, x + r, y + r), fill=YELLOW, outline=INK, width=8)
    for dx, dy in [
        (0, -1),
        (0, 1),
        (-1, 0),
        (1, 0),
        (-1, -1),
        (1, 1),
        (-1, 1),
        (1, -1),
    ]:
        d.line(
            (
                x + dx * (r + 17),
                y + dy * (r + 17),
                x + dx * (r + 55),
                y + dy * (r + 55),
            ),
            fill=YELLOW,
            width=17,
        )


def _cloud(d: ImageDraw.ImageDraw, x: int = 690, y: int = 390) -> None:
    for bx, by, radius in [
        (x - 170, y + 20, 98),
        (x - 70, y - 55, 130),
        (x + 90, y - 50, 118),
        (x + 185, y + 23, 92),
    ]:
        d.ellipse(
            (bx - radius, by - radius, bx + radius, by + radius),
            fill=PALE,
            outline=INK,
            width=8,
        )
    d.rounded_rectangle(
        (x - 245, y + 10, x + 258, y + 117),
        radius=50,
        fill=PALE,
        outline=INK,
        width=8,
    )


def _shirt(d: ImageDraw.ImageDraw, wet: int = 0, spread: bool = False) -> None:
    left, right = (270, 1110) if spread else (350, 1030)
    shape = [
        (500, 260),
        (590, 228),
        (640, 297),
        (740, 297),
        (800, 228),
        (890, 260),
        (right, 480),
        (right - 155, 550),
        (right - 155, 788),
        (left + 155, 788),
        (left + 155, 550),
        (left, 480),
    ]
    d.polygon(shape, fill="#A7D6BF" if wet else "#F2CF94", outline=INK, width=15)
    d.arc((598, 226, 776, 360), 0, 180, fill=INK, width=12)
    for i in range(wet):
        _drop(d, 530 + (i % 3) * 120, 490 + (i // 3) * 165, 30)


def _person(d: ImageDraw.ImageDraw, x: int, y: int, adult: bool = True) -> None:
    h = 105 if adult else 72
    d.ellipse(
        (x - 46, y - h - 95, x + 46, y - h - 3), fill="#F2C5A0", outline=INK, width=9
    )
    d.line((x, y - h + 4, x, y + 100), fill=INK, width=22)
    d.line((x, y - 20, x - 88, y + 50), fill=INK, width=19)
    d.line((x, y - 20, x + 88, y + 50), fill=INK, width=19)
    d.line((x, y + 100, x - 72, y + 208), fill=INK, width=20)
    d.line((x, y + 100, x + 72, y + 208), fill=INK, width=20)


def _crossing(d: ImageDraw.ImageDraw) -> None:
    d.rectangle((145, 490, 1255, 835), fill="#AEBFC3", outline=INK, width=9)
    # Leave a margin inside the road's x=1255 right edge; x=1195 overran it.
    for x in range(205, 1150, 165):
        d.rectangle((x, 540, x + 100, 800), fill="#FFFFFF")


def _car(d: ImageDraw.ImageDraw, x: int = 870, y: int = 430) -> None:
    d.rounded_rectangle(
        (x - 190, y, x + 190, y + 130), 35, fill="#E7A668", outline=INK, width=10
    )
    d.polygon(
        [(x - 120, y), (x - 70, y - 95), (x + 110, y - 95), (x + 145, y)], fill=PALE
    )
    for px in (x - 115, x + 120):
        d.ellipse((px - 40, y + 85, px + 40, y + 165), fill=INK)


def _lamp(d: ImageDraw.ImageDraw, x: int, y: int, on: bool = False) -> None:
    d.line((x, y - 210, x, y - 110), fill=INK, width=14)
    d.polygon(
        [(x - 130, y + 50), (x - 80, y - 110), (x + 80, y - 110), (x + 130, y + 50)],
        fill=YELLOW,
        outline=INK,
        width=12,
    )
    if on:
        for delta in (-1, 0, 1):
            _arrow(d, x + delta * 120, y + 85, delta * 45, 85, YELLOW)


def _fan(d: ImageDraw.ImageDraw, x: int, y: int) -> None:
    d.line((x, y + 50, x, y + 285), fill=INK, width=20)
    d.line((x - 120, y + 285, x + 120, y + 285), fill=INK, width=22)
    for dx, dy in [(-160, -80), (160, -80), (-40, 165)]:
        d.ellipse(
            (x + dx - 70, y + dy - 55, x + dx + 70, y + dy + 55),
            fill=PALE,
            outline=INK,
            width=7,
        )
    d.ellipse((x - 55, y - 55, x + 55, y + 55), fill=YELLOW, outline=INK, width=8)
    d.ellipse((x - 220, y - 220, x + 220, y + 220), outline=INK, width=10)


def _fridge(d: ImageDraw.ImageDraw, x: int, y: int) -> None:
    d.rounded_rectangle(
        (x - 160, y - 295, x + 160, y + 320), 25, fill="#C0DBE1", outline=INK, width=13
    )
    d.line((x - 155, y - 20, x + 155, y - 20), fill=INK, width=10)
    for py in (-130, 80):
        d.line((x + 94, y + py, x + 94, y + py + 84), fill=INK, width=15)


def _check(d: ImageDraw.ImageDraw, x: int = 1085, y: int = 330) -> None:
    d.ellipse((x - 85, y - 85, x + 85, y + 85), fill="#D8F1DA", outline=GREEN, width=14)
    d.line((x - 52, y, x - 8, y + 45), fill=GREEN, width=20)
    d.line((x - 8, y + 45, x + 68, y - 46), fill=GREEN, width=20)


def _phone(d: ImageDraw.ImageDraw, x: int, y: int) -> None:
    d.rounded_rectangle(
        (x - 135, y - 210, x + 135, y + 260), 30, fill="#C3E3DD", outline=INK, width=16
    )
    d.line((x - 60, y + 200, x + 60, y + 200), fill=INK, width=11)
    d.rectangle((x - 65, y - 60, x + 65, y + 80), outline=GREEN, width=10)


def _draw_water(d: ImageDraw.ImageDraw, title: str) -> None:
    if title == "Giọt nước":
        _drop(d, 700, 410, 195)
    else:
        d.ellipse((310, 735, 1090, 855), fill=PALE, outline=BLUE, width=12)
        if title in {"Mây trắng", "Mưa xuống"}:
            _cloud(d)
        if title == "Mưa xuống":
            for x in (460, 610, 760, 910):
                _drop(d, x, 690, 32)
                _arrow(d, x, 520, 0, 82)
        else:
            for x in (505, 685, 865):
                _arrow(d, x, 665, 0, -190)



def _laundry_setting(d: ImageDraw.ImageDraw, title: str) -> None:
    """Original layered laundry-yard scene, not a reused flat topic pictogram.

    All large shapes stay inside the 1400x1000 authored source's inner border.
    The shirt remains the focal object; these elements establish its context.
    """
    d.rounded_rectangle((162, 142, 1238, 832), 42, fill="#EAF2E5")
    # Far garden: soft sky, a fence and grass rather than an empty flat panel.
    d.rounded_rectangle((170, 151, 1230, 640), 36, fill="#E5F1F1")
    for x, y, r in ((300, 295, 96), (1080, 320, 116), (230, 415, 68)):
        d.ellipse((x - r, y - r, x + r, y + r), fill="#C7DFC9")
        d.ellipse((x - r + 17, y - r + 24, x + r - 12, y + r - 10), outline="#8FB69B", width=9)
    d.rectangle((169, 632, 1231, 823), fill="#DBE5CF")
    for x in range(188, 1230, 98):
        d.line((x, 632, x, 805), fill="#C0CEB7", width=8)
    d.line((170, 687, 1230, 687), fill="#B6C9B2", width=9)
    # Foreground clothesline and two timber posts: stable across all six cues.
    for x in (225, 1170):
        d.rounded_rectangle((x - 17, 255, x + 17, 820), 11, fill="#B77F59", outline=INK, width=6)
        d.line((x - 7, 284, x - 7, 770), fill="#E7B18E", width=6)
    d.line((242, 261, 1153, 261), fill="#53685A", width=10)
    # Foreground daisies establish a near plane and distinct drawn strokes.
    for x, y in ((280, 754), (1088, 765), (1146, 746)):
        d.line((x, y + 54, x, y), fill="#6A9D73", width=8)
        for dx, dy in ((-15, 0), (15, 0), (0, -15), (0, 15)):
            d.ellipse((x + dx - 13, y + dy - 13, x + dx + 13, y + dy + 13), fill="#FFFFFF")
        d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=YELLOW)

    if title == "Áo ướt":
        # Basin, bubbles, water surface and droplets show *recent washing*.
        d.rounded_rectangle((172, 682, 475, 806), 27, fill="#77BED1", outline=INK, width=11)
        d.arc((186, 680, 463, 718), 0, 180, fill="#E9F9FB", width=12)
        for x, y, r in ((235, 667, 16), (298, 648, 22), (356, 675, 14), (417, 650, 20)):
            d.ellipse((x - r, y - r, x + r, y + r), fill="#FFFFFF", outline="#69A9B8", width=5)
        for x in (605, 730, 855):
            _drop(d, x, 831, 17)
    elif title == "Ánh nắng":
        _sun(d, 1110, 245, 88)
        for x in (530, 700, 870):
            d.line((x - 80, 342, x + 35, 470), fill="#F6D989", width=14)
        d.ellipse((1010, 700, 1180, 743), fill="#E3D5AC")
    elif title == "Gió thổi":
        for y, width in ((345, 13), (500, 18), (677, 13)):
            d.arc((168, y - 65, 402, y + 62), 205, 30, fill=BLUE, width=width)
            d.line((355, y + 18, 417, y + 18), fill=BLUE, width=width)
        for x, y in ((1025, 385), (1095, 535), (980, 710)):
            d.ellipse((x - 15, y - 6, x + 22, y + 9), fill="#77AD72")
            d.line((x, y, x + 24, y - 24), fill=INK, width=5)
    elif title == "Bay hơi":
        # Rising curved strokes visualize a schematic explanation of evaporation.
        for x in (542, 700, 860):
            d.line(
                ((x, 415), (x - 35, 370), (x + 27, 325), (x - 8, 284)),
                fill="#4B9DB7",
                width=16,
                joint="curve",
            )
            d.ellipse((x - 31, 252, x + 31, 278), outline="#6BB5C8", width=8)
        for x, y in ((1035, 424), (1090, 477), (1020, 555)):
            d.ellipse((x - 25, y - 25, x + 25, y + 25), outline=BLUE, width=8)
    elif title == "Trải rộng":
        for x, y in ((290, 410), (1110, 480), (252, 590)):
            _arrow(d, x, y, 110, 0, BLUE)
        for x, y in ((1080, 340), (1150, 560)):
            d.arc((x - 55, y - 35, x + 55, y + 35), 170, 355, fill=BLUE, width=11)
    elif title == "Áo khô":
        # Clean wicker basket and blue sky differentiate the end state.
        d.rounded_rectangle((1002, 695, 1196, 800), 17, fill="#DDAB75", outline=INK, width=10)
        for x in range(1032, 1190, 31):
            d.line((x, 709, x, 784), fill="#A77551", width=7)
        d.line((1020, 744, 1180, 744), fill="#A77551", width=7)


def _laundry_fabric_detail(d: ImageDraw.ImageDraw, wet: int, spread: bool) -> None:
    """Add visible stitching, collar thickness, creases and cotton texture."""
    # Broad seams remain legible after the source shrinks to a phone preview.
    d.arc((580, 223, 805, 366), 5, 176, fill="#4F786B", width=9)
    d.arc((611, 243, 783, 355), 6, 170, fill="#E8F2DC", width=10)
    d.line((520, 279, 475, 414), fill="#4E8274", width=8)
    d.line((865, 279, 910, 414), fill="#4E8274", width=8)
    for y in (710, 735, 758):
        d.arc((545, y - 17, 833, y + 19), 3, 177, fill="#689B86", width=7)
    # Subtle curved fabric folds are more informative than a solid polygon.
    for x, top, end in ((570, 375, 645), (690, 347, 700), (814, 370, 645)):
        d.line(((x, top), (x - 19, (top + end) // 2), (x + 10, end)), fill="#659B8A", width=7)
    d.rounded_rectangle((746, 432, 840, 548), 10, outline="#508473", width=8)
    d.line((762, 459, 825, 459), fill="#508473", width=7)
    # Stitch marks on sleeves and under the hem.
    for x, y in ((420, 466), (974, 468), (570, 780), (700, 780), (828, 780)):
        d.line((x - 18, y - 9, x + 18, y + 9), fill="#E4E9D7", width=6)
    if wet:
        for x, y in ((609, 570), (802, 617)):
            d.line((x, y, x - 22, y + 60), fill="#4485A2", width=8)
    if spread:
        d.line((355, 475, 465, 481), fill="#4E8274", width=10)
        d.line((915, 482, 1020, 475), fill="#4E8274", width=10)


def _laundry_clothespins(d: ImageDraw.ImageDraw, spread: bool) -> None:
    # These pegs visibly attach the shoulder seams to the actual line.
    for x in ((510, 880) if spread else (535, 852)):
        d.rounded_rectangle((x - 17, 235, x + 17, 299), 8, fill="#DAA46B", outline=INK, width=7)
        d.line((x, 241, x, 289), fill="#F7D9A5", width=6)


def _draw_shirt(d: ImageDraw.ImageDraw, title: str) -> None:
    wet = {
        "Áo ướt": 5,
        "Ánh nắng": 3,
        "Gió thổi": 3,
        "Bay hơi": 2,
        "Trải rộng": 1,
        "Áo khô": 0,
    }[title]
    spread = title == "Trải rộng"
    _laundry_setting(d, title)
    # A faint shadow under the garment anchors it in the authored space.
    d.ellipse((415, 786, 989, 826), fill="#B4C4B0")
    _shirt(d, wet=wet, spread=spread)
    _laundry_fabric_detail(d, wet=wet, spread=spread)
    _laundry_clothespins(d, spread=spread)
    if title == "Ánh nắng":
        _sun(d, 1130, 245, 78)
    if title in {"Gió thổi", "Trải rộng"}:
        for y in (380, 555, 710):
            _arrow(d, 130, y, 160, 0)
    if title == "Bay hơi":
        for x in (550, 700, 850):
            _arrow(d, x, 430, 0, -155)
    if title == "Áo khô":
        _check(d)


def _draw_traffic(d: ImageDraw.ImageDraw, title: str) -> None:
    if title in {"Vạch đi bộ", "Đi chậm", "Tập trung", "Người lớn", "An toàn"}:
        _crossing(d)
    else:
        d.rectangle((120, 720, 1280, 833), fill="#AEBFC3", outline=INK, width=8)
    if title == "Người lớn":
        _person(d, 520, 375)
        _person(d, 830, 415, adult=False)
    else:
        _person(d, 470 if title not in {"Đi chậm", "An toàn"} else 710, 360)
    if title == "Quan sát":
        _arrow(d, 640, 265, -170, 0)
        _arrow(d, 700, 265, 170, 0)
    if title in {"Lắng nghe", "Tập trung"}:
        _car(d, 1010, 570)
    if title == "Lắng nghe":
        for radius in (60, 120, 180):
            d.arc(
                (450 - radius, 150 - radius, 450 + radius, 150 + radius),
                -60,
                65,
                fill=YELLOW,
                width=11,
            )
    if title == "Đèn đường":
        # Pedestrian-specific WALK signal; a vehicle R/Y/G light is misleading.
        d.rounded_rectangle((960, 175, 1145, 620), 30, fill=INK)
        d.rounded_rectangle((995, 338, 1110, 550), 12, fill="#247D58")
        # High-contrast walking human: head, torso, arms and separated legs.
        white = "#FFFFFF"
        d.ellipse((1037, 366, 1067, 396), fill=white)
        d.line((1052, 400, 1052, 465), fill=white, width=13)
        d.line((1050, 421, 1018, 448), fill=white, width=12)
        d.line((1053, 421, 1086, 444), fill=white, width=12)
        d.line((1052, 463, 1023, 507), fill=white, width=13)
        d.line((1052, 463, 1085, 506), fill=white, width=13)
    if title == "An toàn":
        _check(d, 1050, 255)


def _draw_energy(d: ImageDraw.ImageDraw, title: str) -> None:
    if title in {"Bắt đầu", "Thiết bị", "Tổng kết"}:
        _lamp(d, 390, 440, on=title == "Bắt đầu")
        _fan(d, 740, 470)
        if title == "Thiết bị":
            _phone(d, 1100, 490)
        else:
            _fridge(d, 1100, 485)
    elif title == "Bật đèn":
        _lamp(d, 700, 440, on=True)
    elif title == "Ánh sáng":
        d.rectangle((390, 235, 950, 760), fill=PALE, outline=INK, width=17)
        d.line((670, 240, 670, 755), fill=INK, width=12)
        _sun(d, 670, 445, 105)
    elif title == "Quạt mát":
        _fan(d, 700, 470)
        _check(d, 1100, 330)
    elif title == "Máy lạnh":
        d.rounded_rectangle((355, 220, 1045, 445), 30, fill=PALE, outline=INK, width=14)
        d.line((400, 350, 1000, 350), fill=INK, width=12)
        for x in (500, 700, 900):
            _arrow(d, x, 470, 0, 125)
        d.rectangle((1120, 420, 1250, 810), outline=INK, width=18)
    elif title == "Sạc điện":
        _phone(d, 680, 400)
        d.line((790, 690, 970, 690, 970, 510), fill=INK, width=18)
        _check(d, 1070, 330)
    elif title == "Nấu ăn":
        d.rounded_rectangle(
            (430, 395, 1000, 740), 40, fill="#BFD5D9", outline=INK, width=17
        )
        d.line((380, 470, 1040, 470), fill=INK, width=20)
        d.arc((540, 230, 890, 470), 180, 360, fill=INK, width=15)
        for x in (560, 700, 840):
            _arrow(d, x, 335, 0, -85)
    elif title == "Tủ lạnh":
        _fridge(d, 700, 480)
        _check(d, 1090, 320)
    elif title == "Gia đình":
        _person(d, 470, 390)
        _person(d, 850, 430, adult=False)
        _lamp(d, 1100, 430, on=True)
    elif title == "Việc nhỏ":
        d.rounded_rectangle((450, 270, 880, 680), 40, fill=PALE, outline=INK, width=13)
        d.ellipse((570, 385, 760, 575), fill=GREEN, outline=INK, width=13)
        _check(d, 1050, 355)
    if title == "Tổng kết":
        _check(d, 1150, 250)


def semantic_visual(scenario_key: str, title: str) -> bytes:
    """Render one cue, rejecting unknown image mappings rather than generic fallback."""
    if title not in EXPECTED_OBJECTS.get(scenario_key, {}):
        raise ValueError(f"Unknown semantic illustration: {scenario_key}/{title}")
    image = Image.new("RGB", (1400, 1000), "#FFF8EB")
    d = ImageDraw.Draw(image)
    d.rounded_rectangle(
        (100, 95, 1300, 880),
        60,
        fill="#F8F5E9",
        outline="#DDE2D6",
        width=10,
    )
    d.line((175, 855, 1225, 855), fill=INK, width=12)
    if scenario_key == "water-12s":
        _draw_water(d, title)
    elif scenario_key == "shirt-30s":
        _draw_shirt(d, title)
    elif scenario_key == "traffic-45s":
        _draw_traffic(d, title)
    elif scenario_key == "energy-60s":
        _draw_energy(d, title)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
