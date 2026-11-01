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


def inspect_candidate_visual(
    image: Image.Image, *, expected_aspect: str | None = None
) -> dict:
    """Compute bounded, advisory evidence using actual image pixels."""
    if image.width < 1 or image.height < 1:
        raise ValueError("Candidate image must have nonzero dimensions")
    if expected_aspect is not None and expected_aspect not in {"portrait", "landscape"}:
        raise ValueError("Expected aspect must be portrait or landscape")
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
    laplacian_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    tonal_range = float(np.percentile(gray, 95) - np.percentile(gray, 5))
    # Coarse palette prevents pixel-scale JPEG noise from inflating diversity.
    palette_bins = int(np.unique((rgb // 32).reshape((-1, 3)), axis=0).shape[0])
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
    if expected_aspect is not None:
        target_ratio = 9 / 16 if expected_aspect == "portrait" else 16 / 9
        actual_ratio = image.width / image.height
        if abs(actual_ratio / target_ratio - 1) > 0.12:
            warnings.append(
                {
                    "code": "aspect_mismatch",
                    "message": (
                        "Tỷ lệ ảnh nguồn khác khung hình dự án, dễ tạo viền trống "
                        "hoặc cắt mất vật thể. Xem trước cả khung và vùng chữ."
                    ),
                }
            )
        # Standard Comfy sources are 768x1344 / 1344x768; never require
        # native FullHD here. Warn only for substantially smaller candidates.
        if min(image.size) < 512 or max(image.size) < 896:
            warnings.append(
                {
                    "code": "low_source_resolution",
                    "message": (
                        "Ảnh nguồn quá nhỏ để tin cậy khi xuất FullHD. "
                        "Mở ảnh gốc, kiểm độ nét và chi tiết trước khi chọn."
                    ),
                }
            )
    # This is an advisory proxy, not a perceptual blur score. Restrict it
    # to distributed, high-contrast structure so blank art uses its own warning.
    if (
        laplacian_variance < 40
        and tonal_range > 35
        and active_cell_fraction >= 0.24
        and edge_fraction >= 0.004
    ):
        warnings.append(
            {
                "code": "possible_soft_focus",
                "message": (
                    "Đường nét có thể bị nhòe hoặc thiếu chi tiết nhỏ. "
                    "Mở ảnh gốc ở 100% để kiểm chủ thể, chất liệu và chữ."
                ),
            }
        )
    return {
        "policy": POLICY,
        "method": "Canny/Laplacian grayscale 192x192; 8x8 occupied tiles; RGB 32-level palette",
        "width": image.width,
        "height": image.height,
        "edge_fraction": round(edge_fraction, 5),
        "occupied_tile_fraction": round(active_cell_fraction, 5),
        "coarse_palette_bins": palette_bins,
        "laplacian_variance": round(laplacian_variance, 3),
        "expected_aspect": expected_aspect,
        "warnings": warnings,
        "semantic_review": "not_performed",
        "aesthetic_review": "not_performed",
        "human_approval": "pending",
    }
