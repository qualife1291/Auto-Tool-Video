"""Transparent, cheap pre-apply visual signals for local image candidates.

These probes flag potential empty/primitive imagery; they cannot judge beauty,
Vietnamese semantic alignment, scientific correctness or creator acceptance.
They are deliberately advisory and preserve the user's right to keep stylized art.
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

POLICY = "candidate-visual-advisory-1"
SAMPLE = 192
GRID = 8


def inspect_candidate_visual(image: Image.Image) -> dict:
    """Compute bounded, reproducible evidence using actual image pixels."""
    if image.width < 1 or image.height < 1:
        raise ValueError("Candidate image must have nonzero dimensions")
    rgb = np.asarray(
        image.convert("RGB").resize((SAMPLE, SAMPLE), Image.Resampling.BILINEAR),
        dtype=np.uint8,
    )
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 55, 120) > 0
    cells = edges.reshape(GRID, SAMPLE // GRID, GRID, SAMPLE // GRID)
    cell_edge_pixels = cells.sum(axis=(1, 3))
    active_cell_fraction = float(np.count_nonzero(cell_edge_pixels >= 8) / GRID**2)
    edge_fraction = float(edges.mean())
    # Coarse palette prevents pixel-scale JPEG noise from inflating diversity.
    palette_bins = int(
        np.unique((rgb // 32).reshape((-1, 3)), axis=0).shape[0]
    )
    warnings: list[dict[str, str]] = []
    if edge_fraction < 0.004:
        warnings.append(
            {
                "code": "nearly_no_structure",
                "message": (
                    "Ảnh gần như không có cấu trúc/đường nét quan sát được. "
                    "Kiểm hình gốc và nội dung vật thể trước khi chọn."
                ),
            }
        )
    elif active_cell_fraction < 0.24 and palette_bins < 48:
        warnings.append(
            {
                "code": "sparse_simple_art",
                "message": (
                    "Chi tiết tập trung ở vùng nhỏ, bảng màu đơn giản. "
                    "Xem ảnh toàn màn hình: bổ sung bối cảnh, chất liệu và hành động nếu cần."
                ),
            }
        )
    return {
        "policy": POLICY,
        "method": "Canny grayscale 192x192; 8x8 occupied tiles; RGB 32-level palette",
        "width": image.width,
        "height": image.height,
        "edge_fraction": round(edge_fraction, 5),
        "occupied_tile_fraction": round(active_cell_fraction, 5),
        "coarse_palette_bins": palette_bins,
        "warnings": warnings,
        "semantic_review": "not_performed",
        "aesthetic_review": "not_performed",
        "human_approval": "pending",
    }
