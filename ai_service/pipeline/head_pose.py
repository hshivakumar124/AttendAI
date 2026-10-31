"""
AttendAI — 3D Head Pose Estimation Module
===========================================
Estimates 3D Head Orientation (Yaw, Pitch, Roll angles in degrees)
using facial landmarks and OpenCV solvePnP (Perspective-n-Point) solver.

Detects observable visual attention signals:
- ATTENTIVE (looking forward at board/screen)
- LOOKING_AWAY (head turned left or right)
- LOOKING_DOWN (head tilted down)
- LOOKING_UP (head tilted up)
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import cv2
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class HeadPoseResult:
    pitch: float  # Up (-) / Down (+) in degrees
    yaw: float    # Left (-) / Right (+) in degrees
    roll: float   # Tilt left/right in degrees
    orientation_label: str  # "attentive", "looking_away", "looking_down", "looking_up"
    is_attentive: bool


# 3D Model reference points for a generic human face (in mm)
MODEL_3D_POINTS = np.array([
    (0.0, 0.0, 0.0),          # Nose tip
    (0.0, -330.0, -65.0),     # Chin
    (-225.0, 170.0, -135.0),  # Left eye left corner
    (225.0, 170.0, -135.0),   # Right eye right corner
    (-150.0, -150.0, -125.0), # Left mouth corner
    (150.0, -150.0, -125.0),  # Right mouth corner
], dtype=np.float64)


class HeadPoseEstimator:
    """
    3D Head Pose Estimator using solvePnP.
    """

    def __init__(
        self,
        yaw_threshold: float = 25.0,
        pitch_down_threshold: float = 20.0,
        pitch_up_threshold: float = -20.0,
    ):
        self.yaw_threshold = yaw_threshold
        self.pitch_down_threshold = pitch_down_threshold
        self.pitch_up_threshold = pitch_up_threshold

    def estimate_pose(
        self,
        image_shape: Tuple[int, int],
        landmarks_2d: Optional[np.ndarray] = None,
        bbox: Optional[Tuple[int, int, int, int]] = None,
    ) -> HeadPoseResult:
        """
        Estimate Head Pose angles (Pitch, Yaw, Roll).

        Args:
            image_shape: (height, width)
            landmarks_2d: Array of shape (6, 2) corresponding to 3D model points
            bbox: (x1, y1, x2, y2) bounding box used to approximate points if 2D landmarks missing
        """
        h, w = image_shape[:2]

        if landmarks_2d is None or len(landmarks_2d) < 6:
            landmarks_2d = self._approximate_landmarks_from_bbox(bbox, w, h)

        # Camera intrinsic matrix approximation
        focal_length = w
        center = (w / 2.0, h / 2.0)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1],
        ], dtype=np.float64)

        dist_coeffs = np.zeros((4, 1), dtype=np.float64)  # Assume no lens distortion

        success, rvec, tvec = cv2.solvePnP(
            MODEL_3D_POINTS,
            landmarks_2d.astype(np.float64),
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )

        if not success:
            return HeadPoseResult(0.0, 0.0, 0.0, "attentive", True)

        # Convert rotation vector to rotation matrix & Euler angles
        rmat, _ = cv2.Rodrigues(rvec)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

        pitch = float(angles[0])
        yaw = float(angles[1])
        roll = float(angles[2])

        # Determine orientation label
        if abs(yaw) > self.yaw_threshold:
            label = "looking_away"
            is_attentive = False
        elif pitch > self.pitch_down_threshold:
            label = "looking_down"
            is_attentive = False
        elif pitch < self.pitch_up_threshold:
            label = "looking_up"
            is_attentive = False
        else:
            label = "attentive"
            is_attentive = True

        return HeadPoseResult(
            pitch=round(pitch, 2),
            yaw=round(yaw, 2),
            roll=round(roll, 2),
            orientation_label=label,
            is_attentive=is_attentive,
        )

    def _approximate_landmarks_from_bbox(
        self,
        bbox: Optional[Tuple[int, int, int, int]],
        frame_w: int,
        frame_h: int,
    ) -> np.ndarray:
        """Derive 6 key landmark points from face bounding box when explicit landmarks unavailable."""
        if bbox is None:
            x1, y1, x2, y2 = frame_w * 0.3, frame_h * 0.3, frame_w * 0.7, frame_h * 0.7
        else:
            x1, y1, x2, y2 = bbox

        box_w = x2 - x1
        box_h = y2 - y1

        nose = (x1 + box_w * 0.5, y1 + box_h * 0.55)
        chin = (x1 + box_w * 0.5, y1 + box_h * 0.90)
        left_eye = (x1 + box_w * 0.3, y1 + box_h * 0.35)
        right_eye = (x1 + box_w * 0.7, y1 + box_h * 0.35)
        left_mouth = (x1 + box_w * 0.35, y1 + box_h * 0.75)
        right_mouth = (x1 + box_w * 0.65, y1 + box_h * 0.75)

        return np.array([nose, chin, left_eye, right_eye, left_mouth, right_mouth], dtype=np.float32)
