"""Geometry shared by compositing and QC. Coordinates are native output pixels."""

from __future__ import annotations

from PIL import Image


def boxes(width: int, height: int, layout: str = "board") -> dict:
    landscape = width > height
    scale = width / (1920 if landscape else 1080)
    image = (0, 0, 1920, 1080) if landscape else (0, 0, 1080, 1920)
    if layout != "full_frame":
        image = (240, 230, 1440, 580) if landscape else (90, 420, 810, 850)
    caption = (240, 860, 1440, 150) if landscape else (90, 1335, 810, 170)
    return {
        "image": tuple(round(v * scale) for v in image),
        "caption": tuple(round(v * scale) for v in caption),
        "scale": scale,
    }


def image_transform(
    source: tuple[int, int],
    target: tuple[int, int],
    fit: str,
    focal: tuple[float, float],
    zoom: float = 1,
) -> tuple[float, ...]:
    sw, sh = source
    tw, th = target
    ratio = (max(tw / sw, th / sh) if fit == "cover" else min(tw / sw, th / sh)) * zoom
    fx, fy = focal
    offset_x = (tw - sw * ratio) * fx
    offset_y = (th - sh * ratio) * fy
    return (1 / ratio, 0.0, -offset_x / ratio, 0.0, 1 / ratio, -offset_y / ratio)


def fitted_image(
    source: Image.Image,
    target: tuple[int, int],
    fit: str,
    focal: tuple[float, float],
    zoom: float = 1,
) -> Image.Image:
    return source.transform(
        target,
        Image.Transform.AFFINE,
        image_transform(source.size, target, fit, focal, zoom),
        Image.Resampling.BICUBIC,
        fillcolor="#FFF8EB",
    )
