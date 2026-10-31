"""
AttendAI — DeviceDetector Tests
"""

import numpy as np
from ai_service.pipeline.device_detector import DeviceDetector, DetectedDevice


def test_device_detector_initialization():
    detector = DeviceDetector()
    assert detector.backend in ("yolov8_coco", "heuristic_detector")


def test_device_spatial_association():
    detector = DeviceDetector()
    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    # Simulated student tracks
    student_tracks = [
        {"track_id": "track_1", "bbox": (100, 100, 200, 200)},
        {"track_id": "track_2", "bbox": (800, 400, 900, 500)},
    ]

    # Create a detected device near track_1 (e.g. bbox at 120, 150, 180, 220)
    devices = [
        DetectedDevice(
            class_id=67,
            label="cell phone",
            confidence=0.88,
            bbox=(120, 150, 180, 220),
            normalized_bbox=(0.1, 0.1, 0.2, 0.2),
        )
    ]

    detector._associate_devices_with_tracks(devices, student_tracks)
    assert devices[0].associated_track_id == "track_1"
