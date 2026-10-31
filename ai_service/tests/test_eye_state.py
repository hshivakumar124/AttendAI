"""
AttendAI — EyeState & Drowsiness Tests
"""

import numpy as np
from ai_service.pipeline.eye_state import (
    EyeStateEstimator,
    TemporalDrowsinessDetector,
    calculate_ear,
)


def test_calculate_ear_open_vs_closed():
    # 6 landmark points for an open eye (high vertical distance)
    open_eye = np.array([
        [10.0, 20.0], # p1
        [20.0, 10.0], # p2
        [30.0, 10.0], # p3
        [40.0, 20.0], # p4
        [30.0, 30.0], # p5
        [20.0, 30.0], # p6
    ], dtype=np.float32)

    ear_open = calculate_ear(open_eye)
    assert ear_open > 0.30

    # 6 landmark points for a closed eye (very small vertical distance)
    closed_eye = np.array([
        [10.0, 20.0], # p1
        [20.0, 19.5], # p2
        [30.0, 19.5], # p3
        [40.0, 20.0], # p4
        [30.0, 20.5], # p5
        [20.0, 20.5], # p6
    ], dtype=np.float32)

    ear_closed = calculate_ear(closed_eye)
    assert ear_closed < 0.15


def test_temporal_drowsiness_detector():
    detector = TemporalDrowsinessDetector(consecutive_frames_threshold=3)
    track_id = "track_101"

    # Frame 1: eye open -> no alert
    alert, count = detector.update_track(track_id, is_eye_open=True)
    assert alert is False
    assert count == 0

    # Frame 2: eye closed (count=1) -> no alert
    alert, count = detector.update_track(track_id, is_eye_open=False)
    assert alert is False
    assert count == 1

    # Frame 3: eye closed (count=2) -> no alert
    alert, count = detector.update_track(track_id, is_eye_open=False)
    assert alert is False
    assert count == 2

    # Frame 4: eye closed (count=3 >= threshold) -> ALERT!
    alert, count = detector.update_track(track_id, is_eye_open=False)
    assert alert is True
    assert count == 3

    # Frame 5: eye opens -> count resets
    alert, count = detector.update_track(track_id, is_eye_open=True)
    assert alert is False
    assert count == 0
