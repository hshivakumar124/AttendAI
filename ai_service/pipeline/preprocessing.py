"""
AttendAI — Image & Frame Preprocessing Utilities
=================================================
Functions for frame resizing, aspect-ratio letterboxing,
face alignment, and bounding box normalization.
"""

from typing import List, Tuple, Union
import cv2
import numpy as np


def letterbox_image(
    image: np.ndarray,
    target_shape: Tuple[int, int] = (640, 640),
    color: Tuple[int, int, int] = (114, 114, 114),
) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    """
    Resize image to target shape with padding to preserve aspect ratio.

    Returns:
        (padded_image, scale_ratio, (pad_left, pad_top))
    """
    h, w = image.shape[:2]
    target_w, target_h = target_shape

    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    pad_left = (target_w - new_w) // 2
    pad_top = (target_h - new_h) // 2

    canvas = np.full((target_h, target_w, 3), color, dtype=np.uint8)
    canvas[pad_top : pad_top + new_h, pad_left : pad_left + new_w] = resized

    return canvas, scale, (pad_left, pad_top)


def crop_face(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    margin_percent: float = 0.15,
) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    """
    Crop face from image using bounding box (x1, y1, x2, y2) with optional safety margin.

    Returns:
        (cropped_face_bgr, adjusted_bbox)
    """
    h, w = image.shape[:2]
    x1, y1, x2, y2 = bbox

    box_w = x2 - x1
    box_h = y2 - y1

    margin_w = int(box_w * margin_percent)
    margin_h = int(box_h * margin_percent)

    crop_x1 = max(0, x1 - margin_w)
    crop_y1 = max(0, y1 - margin_h)
    crop_x2 = min(w, x2 + margin_w)
    crop_y2 = min(h, y2 + margin_h)

    crop = image[crop_y1:crop_y2, crop_x1:crop_x2]
    return crop, (crop_x1, crop_y1, crop_x2, crop_y2)


def normalize_bbox(
    bbox: Tuple[int, int, int, int],
    frame_width: int,
    frame_height: int,
) -> Tuple[float, float, float, float]:
    """Convert absolute pixel coordinates (x1, y1, x2, y2) to normalized [0.0, 1.0]."""
    x1, y1, x2, y2 = bbox
    return (
        round(x1 / frame_width, 4),
        round(y1 / frame_height, 4),
        round(x2 / frame_width, 4),
        round(y2 / frame_height, 4),
    )


def denormalize_bbox(
    norm_bbox: Tuple[float, float, float, float],
    frame_width: int,
    frame_height: int,
) -> Tuple[int, int, int, int]:
    """Convert normalized [0.0, 1.0] bbox back to absolute pixel coordinates."""
    nx1, ny1, nx2, ny2 = norm_bbox
    return (
        int(nx1 * frame_width),
        int(ny1 * frame_height),
        int(nx2 * frame_width),
        int(ny2 * frame_height),
    )
