"""
AttendAI — Preprocessing Utilities Tests
"""

import numpy as np
from ai_service.pipeline.preprocessing import (
    crop_face,
    denormalize_bbox,
    letterbox_image,
    normalize_bbox,
)


def test_letterbox_image():
    dummy = np.zeros((480, 640, 3), dtype=np.uint8)
    padded, scale, (pad_left, pad_top) = letterbox_image(dummy, target_shape=(640, 640))
    assert padded.shape == (640, 640, 3)
    assert scale == 1.0
    assert pad_left == 0
    assert pad_top == 80


def test_crop_face():
    dummy = np.zeros((500, 500, 3), dtype=np.uint8)
    bbox = (100, 100, 200, 200)
    crop, adj_box = crop_face(dummy, bbox, margin_percent=0.10)
    assert crop.ndim == 3
    assert crop.shape[2] == 3
    # Height and width should include margins
    assert crop.shape[0] > 100
    assert crop.shape[1] > 100


def test_normalize_and_denormalize_bbox():
    w, h = 1920, 1080
    bbox = (192, 108, 960, 540)
    norm = normalize_bbox(bbox, w, h)
    assert norm == (0.1, 0.1, 0.5, 0.5)

    denorm = denormalize_bbox(norm, w, h)
    assert denorm == bbox
