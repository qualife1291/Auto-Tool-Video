"""Regression: pedestrian narration must show a pedestrian-specific signal.

The fixture is not creator-approved art; this checks only a concrete visual cue.
"""

import importlib.util
import io
from pathlib import Path

from PIL import Image


def test_pedestrian_signal_has_white_walking_figure():
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "qa_semantic_art.py"
    spec = importlib.util.spec_from_file_location("qa_semantic_art", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    image = Image.open(io.BytesIO(module.semantic_visual("traffic-45s", "Đèn đường"))).convert(
        "RGB"
    )
    # White walking pictogram in the signal panel, not generic R/Y/G car lights.
    pixels = [image.getpixel((x, y)) for x in range(1010, 1100, 5) for y in range(365, 520, 5)]
    assert sum(min(rgb) >= 230 for rgb in pixels) >= 8
