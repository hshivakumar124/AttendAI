"""
AttendAI — EngagementEstimator Tests
"""

from ai_service.pipeline.engagement import EngagementEstimator, EngagementResult


def test_engagement_score_attentive():
    estimator = EngagementEstimator()
    # Fully attentive: head forward, eyes open, no phone
    result = estimator.calculate_engagement(
        head_orientation="attentive",
        is_eye_open=True,
        detection_confidence=0.9,
        has_device_distraction=False,
    )
    assert isinstance(result, EngagementResult)
    assert result.score == 100.0
    assert result.label == "High"
    assert result.breakdown["head_pose_points"] == 35.0
    assert result.breakdown["eye_state_points"] == 30.0
    assert result.breakdown["no_distraction_points"] == 15.0


def test_engagement_score_looking_down_with_phone():
    estimator = EngagementEstimator()
    # Looking down at phone
    result = estimator.calculate_engagement(
        head_orientation="looking_down",
        is_eye_open=True,
        detection_confidence=0.9,
        has_device_distraction=True,
    )
    assert result.score < 70.0
    assert result.label in ("Moderate", "Low")
    assert result.breakdown["no_distraction_points"] == 0.0


def test_engagement_score_drowsy():
    estimator = EngagementEstimator()
    # Eyes closed
    result = estimator.calculate_engagement(
        head_orientation="attentive",
        is_eye_open=False,
        detection_confidence=0.9,
        has_device_distraction=False,
    )
    assert result.score == 70.0  # 100 - 30 (eye score is 0)
    assert result.breakdown["eye_state_points"] == 0.0
