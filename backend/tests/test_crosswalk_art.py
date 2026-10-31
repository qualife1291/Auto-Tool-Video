"""Regression for zebra-crossing paint leaking beyond the road edge."""

import importlib.util
import io
from pathlib import Path

import pytest
from PIL import Image, ImageColor


@pytest.mark.parametrize("title", ("Vạch đi bộ", "Đi chậm", "Người lớn"))
def test_crosswalk_stripes_stay_inside_road(title):
    path = Path(__file__).resolve().parents[2] / "scripts" / "qa_semantic_art.py"
    spec = importlib.util.spec_from_file_location("qa_semantic_art", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    art = module.semantic_visual("traffic-45s", title)
    image = Image.open(io.BytesIO(art)).convert("RGB")
    # Road ends at x=1255; the white stripe must not paint outside its edge.
    assert image.getpixel((1270, 650)) == ImageColor.getrgb("#F8F5E9")
