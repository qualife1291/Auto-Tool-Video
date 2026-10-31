"""Match flat whiteboard illustration borders to the render paper color."""

from __future__ import annotations

import numpy as np
from PIL import Image

PAPER_RGB = (255, 248, 235)


def normalize_paper(source: Image.Image) -> Image.Image:
    """Recolor only near-uniform, bright, neutral illustration backgrounds.

    The border is used as evidence; dark, textured, photographic and colorful
    edges are left untouched. Subject pixels sufficiently unlike the border
    are preserved rather than multiplied by a global brightness correction.
    """
    image = source.convert("RGB")
    pixels = np.asarray(image, dtype=np.uint8)
    height, width = pixels.shape[:2]
    band = max(2, min(32, min(height, width) // 50))
    ring = np.concatenate(
        (
            pixels[:band].reshape(-1, 3),
            pixels[-band:].reshape(-1, 3),
            pixels[:, :band].reshape(-1, 3),
            pixels[:, -band:].reshape(-1, 3),
        ),
        axis=0,
    ).astype(np.float32)
    background = np.median(ring, axis=0)
    if (
        np.max(np.std(ring, axis=0)) > 8
        or np.min(background) < 225
        or np.max(background) - np.min(background) > 24
    ):
        return image
    values = pixels.astype(np.float32)
    distance = np.max(np.abs(values - background), axis=2)
    weight = np.clip(1 - distance / 65, 0, 1)[..., None]
    shift = np.asarray(PAPER_RGB, dtype=np.float32) - background
    adjusted = np.clip(np.rint(values + shift * weight), 0, 255).astype(np.uint8)
    return Image.fromarray(adjusted, "RGB")
