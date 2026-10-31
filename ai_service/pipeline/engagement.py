"""
AttendAI — Explainable Visual Engagement Engine
=================================================
Calculates an explainable 0.0 – 100.0 Visual Engagement Score for each student.

Formula (Weighted Signal Aggregation):
- Head Pose (35%): Attentive = 100, Looking Down = 40, Looking Away = 20
- Eye State (30%): Open = 100, Closed/Drowsy = 0
- Face Visibility (20%): Fully visible (conf >= 0.8) = 100, Partial = 60
- No Distractions (15%): No active phone/device detected = 100, Device present = 0

All signals are observable AI estimates — NOT direct measurements of mental focus.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import structlog

from ai_service.config.ai_config import ai_settings

logger = structlog.get_logger(__name__)


@dataclass
class EngagementResult:
    score: float  # 0.0 to 100.0
    label: str    # "High", "Moderate", "Low"
    breakdown: Dict[str, float]  # Component breakdown for UI transparency


class EngagementEstimator:
    """
    Explainable Visual Engagement Score Engine.
    """

    def __init__(
        self,
        weight_head_pose: float = None,
        weight_eye_state: float = None,
        weight_face_visibility: float = None,
        weight_distraction: float = None,
    ):
        self.w_head = weight_head_pose or ai_settings.engagement_weight_head_pose
        self.w_eye = weight_eye_state or ai_settings.engagement_weight_eye_state
        self.w_vis = weight_face_visibility or ai_settings.engagement_weight_face_visibility
        self.w_dist = weight_distraction or ai_settings.engagement_weight_looking_away

    def calculate_engagement(
        self,
        head_orientation: str = "attentive",
        is_eye_open: bool = True,
        detection_confidence: float = 0.90,
        has_device_distraction: bool = False,
    ) -> EngagementResult:
        """
        Calculate visual engagement score and full explainable breakdown.
        """
        # 1. Head Pose Score (0 - 100)
        if head_orientation == "attentive":
            head_score = 100.0
        elif head_orientation == "looking_down":
            head_score = 40.0
        elif head_orientation == "looking_away":
            head_score = 20.0
        elif head_orientation == "looking_up":
            head_score = 60.0
        else:
            head_score = 50.0

        # 2. Eye State Score (0 - 100)
        eye_score = 100.0 if is_eye_open else 0.0

        # 3. Face Visibility Score (0 - 100)
        if detection_confidence >= 0.80:
            visibility_score = 100.0
        elif detection_confidence >= 0.60:
            visibility_score = 70.0
        else:
            visibility_score = 50.0

        # 4. No Distraction Score (0 - 100)
        distraction_score = 0.0 if has_device_distraction else 100.0

        # Calculate weighted composite score (0.0 to 100.0)
        final_score = (
            (self.w_head * head_score)
            + (self.w_eye * eye_score)
            + (self.w_vis * visibility_score)
            + (self.w_dist * distraction_score)
        )
        final_score = round(max(0.0, min(100.0, final_score)), 1)

        # Categorize label
        if final_score >= 75.0:
            label = "High"
        elif final_score >= 45.0:
            label = "Moderate"
        else:
            label = "Low"

        breakdown = {
            "head_pose_points": round(self.w_head * head_score, 1),
            "eye_state_points": round(self.w_eye * eye_score, 1),
            "face_visibility_points": round(self.w_vis * visibility_score, 1),
            "no_distraction_points": round(self.w_dist * distraction_score, 1),
        }

        return EngagementResult(
            score=final_score,
            label=label,
            breakdown=breakdown,
        )
