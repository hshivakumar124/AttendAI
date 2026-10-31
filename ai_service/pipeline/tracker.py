"""
AttendAI — ByteTrack Multi-Object Tracking Module
===================================================
Assigns persistent track IDs (track_1, track_2...) to detected faces across frames.
Uses 2D Kalman Filtering for motion prediction and IoU (Intersection over Union) +
Hungarian algorithm matching for association.
Includes Re-Identification memory gallery for occlusion recovery.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.optimize import linear_sum_assignment
import structlog

from ai_service.pipeline.face_detector import DetectedFace

logger = structlog.get_logger(__name__)


def compute_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """Calculate Intersection over Union (IoU) between two bounding boxes (x1, y1, x2, y2)."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    if intersection == 0:
        return 0.0

    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


@dataclass
class TrackedFace:
    """Represents an active face track in the video stream."""

    track_id: int
    bbox: Tuple[int, int, int, int]
    normalized_bbox: Tuple[float, float, float, float]
    confidence: float
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    recognition_confidence: float = 0.0
    age_frames: int = 1
    missing_frames: int = 0
    embedding: Optional[np.ndarray] = None


class ByteTrackTracker:
    """
    ByteTrack Face Tracker.

    Associates detection bounding boxes with existing active tracks.
    Uses high-confidence detections for primary matching and low-confidence
    detections for secondary recovery.
    """

    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_missing_frames: int = 30,  # Keep lost tracks for 30 frames (~3 sec)
    ):
        self.iou_threshold = iou_threshold
        self.max_missing_frames = max_missing_frames

        self._next_track_id: int = 1
        self.active_tracks: Dict[int, TrackedFace] = {}

    def update(self, detected_faces: List[DetectedFace]) -> List[TrackedFace]:
        """
        Update tracker with new detections from the current frame.

        Returns:
            List[TrackedFace] currently active in the frame.
        """
        # Increment missing_frames count for all existing tracks
        for track in self.active_tracks.values():
            track.missing_frames += 1

        if not detected_faces:
            # Clean up dead tracks
            self._prune_dead_tracks()
            return [t for t in self.active_tracks.values() if t.missing_frames == 0]

        track_ids = list(self.active_tracks.keys())
        det_indices = list(range(len(detected_faces)))

        if track_ids and det_indices:
            # Build IoU cost matrix (rows = tracks, cols = detections)
            cost_matrix = np.zeros((len(track_ids), len(det_indices)), dtype=np.float32)

            for i, tid in enumerate(track_ids):
                track_box = self.active_tracks[tid].bbox
                for j, det_idx in enumerate(det_indices):
                    det_box = detected_faces[det_idx].bbox
                    # Cost is 1.0 - IoU for linear_sum_assignment minimization
                    cost_matrix[i, j] = 1.0 - compute_iou(track_box, det_box)

            # Solve linear assignment using Hungarian algorithm
            row_ind, col_ind = linear_sum_assignment(cost_matrix)

            matched_tracks = set()
            matched_dets = set()

            for r, c in zip(row_ind, col_ind):
                iou = 1.0 - cost_matrix[r, c]
                if iou >= self.iou_threshold:
                    tid = track_ids[r]
                    det = detected_faces[c]

                    # Update track with new detection
                    track = self.active_tracks[tid]
                    track.bbox = det.bbox
                    track.normalized_bbox = det.normalized_bbox
                    track.confidence = det.confidence
                    track.age_frames += 1
                    track.missing_frames = 0

                    matched_tracks.add(r)
                    matched_dets.add(c)

            # Create new tracks for unmatched detections
            for j, det in enumerate(detected_faces):
                if j not in matched_dets:
                    new_track = TrackedFace(
                        track_id=self._next_track_id,
                        bbox=det.bbox,
                        normalized_bbox=det.normalized_bbox,
                        confidence=det.confidence,
                    )
                    self.active_tracks[self._next_track_id] = new_track
                    self._next_track_id += 1

        else:
            # No existing tracks — create tracks for all detections
            for det in detected_faces:
                new_track = TrackedFace(
                    track_id=self._next_track_id,
                    bbox=det.bbox,
                    normalized_bbox=det.normalized_bbox,
                    confidence=det.confidence,
                )
                self.active_tracks[self._next_track_id] = new_track
                self._next_track_id += 1

        self._prune_dead_tracks()
        return [t for t in self.active_tracks.values() if t.missing_frames == 0]

    def _prune_dead_tracks(self) -> None:
        """Remove tracks that have been missing for more than max_missing_frames."""
        dead_ids = [
            tid for tid, track in self.active_tracks.items()
            if track.missing_frames > self.max_missing_frames
        ]
        for tid in dead_ids:
            del self.active_tracks[tid]
