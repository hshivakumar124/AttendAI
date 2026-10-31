"""
AttendAI — HeadPoseEstimator Tests
"""

import numpy as np
from ai_service.pipeline.head_pose import HeadPoseEstimator, HeadPoseResult


def test_head_pose_estimator_attentive():
    estimator = HeadPoseEstimator(yaw_threshold=25.0, pitch_down_threshold=20.0)
    # Estimate pose with front-facing bounding box
    result = estimator.estimate_pose((720, 1280), bbox=(500, 200, 700, 400))

    assert isinstance(result, HeadPoseResult)
    assert isinstance(result.pitch, float)
    assert isinstance(result.yaw, float)
    assert isinstance(result.roll, float)
    assert result.orientation_label in ("attentive", "looking_away", "looking_down", "looking_up")


def test_head_pose_custom_landmarks_looking_away():
    estimator = HeadPoseEstimator(yaw_threshold=20.0)
    # 2D landmarks simulating head turned right (yaw > 20 deg)
    landmarks_turned = np.array([
        (750.0, 300.0), # Nose shifted far right
        (650.0, 450.0), # Chin
        (550.0, 250.0), # Left eye
        (700.0, 250.0), # Right eye
        (580.0, 400.0), # Left mouth
        (680.0, 400.0), # Right mouth
    ], dtype=np.float32)

    result = estimator.estimate_pose((720, 1280), landmarks_2d=landmarks_turned)
    assert isinstance(result, HeadPoseResult)
    assert result.orientation_label in ("looking_away", "looking_down", "attentive")
