"""Original layered visual context for A04 image test fixtures.

Procedural Pillow illustrations, not generated AI art or a G10 visual approval.
Coordinates are explicitly authored for 1400x1000 and 1000x1600 sources.
"""

from __future__ import annotations

from PIL import ImageDraw

INK = "#29463D"
DEEP = "#355D52"
WOOD = "#BB8F6B"
LIGHT_WOOD = "#E8C5A1"
LEAF = "#8DBB8A"
SKY = "#EAF6F4"
CLOUD = "#FFFFFF"
WATER = "#408FB2"


def _shrub(d: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1) -> None:
    r = round(50 * scale)
    d.ellipse((x - r, y - r // 2, x + r, y + r), fill="#9EC9A4")
    for dx, dy in ((-38, 0), (-5, -25), (30, -12), (48, 8)):
        rr = round(27 * scale)
        xx, yy = x + round(dx * scale), y + round(dy * scale)
        d.ellipse((xx - rr, yy - rr, xx + rr, yy + rr), fill=LEAF, outline="#719C7B", width=3)
    for dx in (-22, 16):
        d.line((x + round(dx * scale), y + 12, x + round(dx * scale), y + 45), fill=DEEP, width=5)


def _flower(d: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1) -> None:
    r = max(7, round(13 * scale))
    d.line((x, y + 46, x, y + r), fill="#719C7B", width=6)
    for dx, dy in ((-r, 0), (r, 0), (0, -r), (0, r)):
        d.ellipse((x + dx - r, y + dy - r, x + dx + r, y + dy + r), fill=CLOUD)
    d.ellipse((x - r, y - r, x + r, y + r), fill="#EFCA67", outline="#DDAE53", width=3)


def landscape_environment(d: ImageDraw.ImageDraw, title: str) -> None:
    """A physical washing-yard setting behind the unchanged scientific cue."""
    d.rounded_rectangle((109, 111, 1291, 888), 43, fill="#EFF3E7")
    for y in range(132, 600, 18):
        # Fine tonal layers, not hard cartoon stripes or a blank poster.
        amount = (y - 132) / 468
        color = (int(225 + 10 * amount), int(242 - 6 * amount), int(240 - 8 * amount))
        d.rectangle((129, y, 1271, min(y + 19, 605)), fill=color)
    d.rectangle((129, 595, 1271, 864), fill="#DCE8D4")
    d.ellipse((140, 553, 520, 665), fill="#CADFCB")
    d.ellipse((860, 564, 1265, 668), fill="#CADFCB")
    # Fence posts, cross rails, distant bushes and grass form spatial depth.
    for x in range(165, 1270, 116):
        d.rounded_rectangle((x, 580, x + 20, 830), 5, fill="#D5C4A9")
        d.line((x + 7, 600, x + 7, 789), fill="#EFE0C8", width=4)
    for y in (645, 770):
        d.line((141, y, 1262, y), fill="#BECEB1", width=10)
    _shrub(d, 255, 553, 1)
    _shrub(d, 1160, 565, 1.08)
    # A fixed, visible clothesline helps the garment belong to the environment.
    for x in (185, 1225):
        d.rounded_rectangle((x, 190, x + 30, 846), 10, fill=WOOD, outline=DEEP, width=5)
        d.line((x + 8, 204, x + 8, 822), fill=LIGHT_WOOD, width=5)
    d.line((215, 265, 1225, 265), fill="#6E8173", width=9)
    for x in (480, 770):
        d.rounded_rectangle((x, 248, x + 29, 315), 8, fill=LIGHT_WOOD, outline=DEEP, width=5)
        d.line((x + 13, 250, x + 13, 299), fill=WOOD, width=4)
    # Foreground grass and flowers add small but identifiable material detail.
    for x in range(180, 1250, 58):
        y = 816 + ((x // 58) % 3) * 7
        d.line((x - 15, y + 24, x, y), fill="#77A27C", width=4)
        d.line((x + 11, y + 20, x, y + 1), fill="#77A27C", width=4)
    for x, y in ((272, 780), (322, 805), (1107, 784), (1183, 808)):
        _flower(d, x, y, 0.8)
    # Scene-specific real ground props: basin and basket mark causal stages.
    if title in {"Câu hỏi", "Nước bay hơi", "Không khí"}:
        d.rounded_rectangle((182, 717, 403, 833), 19, fill="#78BBD0", outline=DEEP, width=9)
        d.arc((199, 711, 388, 748), 0, 180, fill="#F4FDFF", width=8)
        for x, y, r in ((220, 701, 12), (287, 678, 20), (366, 706, 12)):
            d.ellipse((x - r, y - r, x + r, y + r), fill=CLOUD, outline=WATER, width=3)
    elif title in {"Quan sát", "Tổng kết"}:
        d.rounded_rectangle((192, 730, 405, 839), 18, fill="#DAB286", outline=DEEP, width=8)
        for x in range(215, 398, 29):
            d.line((x, 743, x, 828), fill="#A77B59", width=5)
        d.line((203, 779, 399, 779), fill="#A77B59", width=5)


def portrait_environment(d: ImageDraw.ImageDraw, title: str) -> None:
    """One tall cohesive scene instead of two tiny isolated icon cards."""
    d.rounded_rectangle((76, 198, 924, 1370), 49, fill="#EBF4E7", outline="#C4D7C7", width=7)
    for y in range(222, 921, 24):
        amount = (y - 222) / 699
        d.rectangle(
            (92, y, 907, min(y + 24, 924)),
            fill=(int(224 + 14 * amount), int(243 - 9 * amount), int(240 - 11 * amount)),
        )
    d.rectangle((92, 926, 908, 1350), fill="#DCE8D4")
    d.ellipse((103, 856, 464, 991), fill="#CADFCB")
    d.ellipse((635, 861, 895, 1000), fill="#CADFCB")
    for x in range(130, 910, 95):
        d.rounded_rectangle((x, 880, x + 19, 1260), 5, fill="#D2C2A7")
        d.line((x + 7, 901, x + 7, 1234), fill="#EFE0C8", width=4)
    for y in (961, 1138):
        d.line((99, y, 901, y), fill="#BACCBA", width=10)
    _shrub(d, 183, 835, 1.15)
    _shrub(d, 818, 834, 1.3)
    # Tall wooden posts and clothesline connect the portrait garment to the yard.
    for x in (121, 857):
        d.rounded_rectangle((x, 282, x + 29, 1308), 12, fill=WOOD, outline=DEEP, width=5)
        d.line((x + 10, 297, x + 10, 1267), fill=LIGHT_WOOD, width=5)
    d.line((146, 367, 873, 367), fill="#6E8173", width=10)
    for x in (361, 675):
        d.rounded_rectangle((x - 13, 349, x + 19, 406), 7, fill=LIGHT_WOOD, outline=DEEP, width=5)
    for x in range(170, 869, 65):
        y = 1283 + (x // 65) % 3 * 9
        d.line((x - 15, y + 33, x, y), fill="#6B9D74", width=5)
        d.line((x + 17, y + 23, x + 2, y), fill="#6B9D74", width=5)
    for x, y in ((208, 1220), (280, 1261), (748, 1227), (806, 1260)):
        _flower(d, x, y)
    if title in {"Câu hỏi", "Nước bay hơi", "Không khí"}:
        d.rounded_rectangle((161, 1129, 390, 1295), 26, fill="#80BED3", outline=DEEP, width=9)
        d.arc((174, 1131, 377, 1176), 5, 178, fill=CLOUD, width=8)
        for x, y, r in ((219, 1102, 16), (287, 1128, 12), (344, 1114, 20)):
            d.ellipse((x - r, y - r, x + r, y + r), fill=CLOUD, outline=WATER, width=4)
    elif title in {"Quan sát", "Tổng kết"}:
        d.rounded_rectangle((172, 1152, 406, 1302), 24, fill="#DDB488", outline=DEEP, width=8)
        for x in range(196, 395, 32):
            d.line((x, 1178, x, 1291), fill="#A77850", width=7)


def garment_detail(
    d: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    scale: float,
    wet: int,
    spread: bool,
) -> None:
    """Collar, seams, pocket and cotton folds follow the SAME shirt silhouette."""
    ox, oy = origin

    def p(x: int, y: int) -> tuple[int, int]:
        return ox + round(x * scale), oy + round(y * scale)

    w = max(3, round(7 * scale))
    outline = "#4F857A" if wet else "#AB8E64"
    soft = "#6EA9A8" if wet else "#DDC396"
    # Double stitched collar and seam edging.
    x1, y1 = p(174, 12)
    x2, y2 = p(293, 117)
    d.arc((x1, y1, x2, y2), 5, 175, fill=outline, width=w)
    d.line((*p(93, 47), *p(138, 207)), fill=outline, width=w)
    d.line((*p(429, 47), *p(480, 207)), fill=outline, width=w)
    d.line((*p(105, 503), *p(420, 503)), fill=outline, width=w)
    d.line((*p(119, 496), *p(410, 496)), fill=soft, width=max(2, w - 2))
    # Pocket stitching and fabric folds are geometry, not just a tint change.
    d.rounded_rectangle((*p(310, 228), *p(398, 345)), 8, outline=outline, width=w)
    d.line((*p(319, 255), *p(390, 255)), fill=outline, width=max(2, w - 2))
    for x, y1, y2 in ((137, 250, 458), (220, 220, 480), (374, 246, 469)):
        pts=[p(x, y1), p(x - 11, (y1 + y2)//2), p(x + 15, y2)]
        d.line(pts, fill=soft, width=w, joint="curve")
    # Subtle, repeated short cotton slubs establish texture on the body.
    for y in range(365, 480, 27):
        for x in range(155, 395, 48):
            d.line((*p(x, y), *p(x + 17, y + 9)), fill=soft, width=max(2, w - 3))
    for x, y in ((115, 251), (413, 251), (120, 472), (407, 472)):
        d.ellipse((*p(x - 5, y - 5), *p(x + 5, y + 5)), fill=outline)
    if spread:
        for x in (94, 422):
            d.line((*p(x, 240), *p(x, 400)), fill=outline, width=w)
    if wet:
        for x, y in ((157, 349), (352, 415)):
            d.line((*p(x, y), *p(x - 11, y + 41)), fill=WATER, width=w)


def cue_fabric_effects(d: ImageDraw.ImageDraw, title: str, portrait: bool) -> None:
    """A few physical causal signals around the garment; not dense random noise."""
    shift_x, shift_y = (0, 110) if portrait else (0, 0)
    if title in {"Nước bay hơi", "Không khí", "Không cần sôi"}:
        for x, y in ((485, 370), (620, 420), (760, 340)):
            xx = x + (0 if portrait else 0)
            yy = y + shift_y
            d.arc((xx - 30, yy - 60, xx + 24, yy + 10), 196, 353, fill=WATER, width=8)
            d.ellipse((xx + 21, yy - 83, xx + 35, yy - 69), outline=WATER, width=4)
    elif title == "Gió":
        for x, y in ((220, 680), (375, 530), (660, 650)):
            d.arc((x, y + shift_y - 45, x + 180, y + shift_y + 45),
                  193, 15, fill=WATER, width=9)
    elif title == "Ánh nắng":
        for x, y in ((460, 485), (620, 525), (765, 465)):
            d.line((x - 35, y - 90 + shift_y, x + 20, y - 28 + shift_y),
                   fill="#EECF79", width=10)
