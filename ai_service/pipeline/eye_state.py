"""
AttendAI — Eye State (EAR) & Temporal Drowsiness Engine
=========================================================
Calculates Eye Aspect Ratio (EAR) to determine eye open/closed state.
Tracks consecutive frames of eye closure to detect temporal drowsiness.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import numpy as np
import structlog

from ai_service.config.ai_config import ai_settings

logger = structlog.get_logger(__name__)


def calculate_ear(eye_points: np.ndarray) -> float:
    """
    Calculate Eye Aspect Ratio (EAR) for a 6-point eye landmark array.

    Points:
        p1 (left corner), p4 (right corner)
        p2, p3 (top vertical points), p6, p5 (bottom vertical points)
    """
    if eye_points is None or len(eye_points) < 6:
        return 0.35  # Default open eye EAR if points unavailable

    p1, p2, p3, p4, p5, p6 = eye_points[:6]

    v1 = np.linalg.norm(p2 - p6)
    v2 = np.linalg.norm(p3 - p5)
    h = np.linalg.norm(p1 - p4)

    if h == 0:
        return 0.35

    return float((v1 + v2) / (2.0 * h))


@dataclass
class EyeStateResult:
    left_ear: float
    right_ear: float
    avg_ear: float
    is_eye_open: bool


class EyeStateEstimator:
    """
    Evaluates Eye Aspect Ratio (EAR) for left & right eyes.
    Threshold default: EAR < 0.25 indicates eyes closed.
    """

    def __init__(self, ear_threshold: float = None):
        self.ear_threshold = ear_threshold if ear_threshold is not None else ai_settings.drowsiness_ear_threshold

    def evaluate_eye_state(
        self,
        left_eye_points: Optional[np.ndarray] = None,
        right_eye_points: Optional[np.ndarray] = None,
        face_crop_bgr: Optional[np.ndarray] = None,
    ) -> EyeStateResult:
        """
        Evaluate eye open/closed state.
        """
        if left_eye_points is not None and right_eye_points is not None:
            left_ear = calculate_ear(left_eye_points)
            right_ear = calculate_ear(right_eye_points)
            avg_ear = (left_ear + right_ear) / 2.0
        elif face_crop_bgr is not None and face_crop_bgr.size > 0:
            # Estimate EAR based on image brightness/gradient of upper face
            avg_ear = self._estimate_ear_from_crop(face_crop_bgr)
            left_ear = right_ear = avg_ear
        else:
            avg_ear = 0.32
            left_ear = right_ear = avg_ear

        is_open = avg_ear >= self.ear_threshold
        return EyeStateResult(
            left_ear=round(left_ear, 3),
            right_ear=round(right_ear, 3),
            avg_ear=round(avg_ear, 3),
            is_eye_open=is_open,
        )

    def _estimate_ear_from_crop(self, crop: np.ndarray) -> float:
        """Heuristic EAR estimator based on face crop eye region gradient."""
        h, w = crop.shape[:2]
        eye_region = crop[int(h * 0.2) : int(h * 0.5), :]
        if eye_region.size == 0:
            return 0.32

        gray = np.mean(eye_region, axis=2)
        std_dev = float(np.std(gray))
        # Open eyes present high contrast/gradients (std dev > 30), closed eyes present low contrast
        ear = 0.15 + min(0.25, (std_dev / 120.0))
        return round(ear, 3)


class TemporalDrowsinessDetector:
    """
    Tracks consecutive frames of eye closure per track_id.
    Triggers drowsiness alert when closed frames >= consecutive_threshold.
    """

    def __init__(self, consecutive_frames_threshold: int = None):
        self.threshold = (
            consecutive_frames_threshold
            if consecutive_frames_threshold is not None
            else ai_settings.drowsiness_consecutive_frames
        )
        self._track_closed_counters: Dict[str, int] = {}

    def update_track(self, track_id: str, is_eye_open: bool) -> Tuple[bool, int]:
        """
        Update eye state for a track ID.

        Returns:
            (is_drowsy_alert_triggered, consecutive_closed_frames)
        """
        if is_eye_open:
            self._track_closed_counters[track_id] = 0
            return False, 0

        counter = self._track_closed_counters.get(track_id, 0) + 1
        self._track_closed_counters[track_id] = counter

        is_alert = counter >= self.threshold
        if is_alert:
            logger.info("Drowsiness alert triggered", track_id=track_id, consecutive_frames=counter)

        return is_alert, counter
