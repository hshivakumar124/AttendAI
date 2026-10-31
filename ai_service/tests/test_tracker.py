"""
AttendAI — ByteTrack Tracker Tests
"""

import numpy as np
from ai_service.pipeline.face_detector import DetectedFace
from ai_service.pipeline.tracker import ByteTrackTracker, compute_iou


def test_compute_iou():
    box1 = (100, 100, 200, 200)
    box2 = (100, 100, 200, 200)
    assert abs(compute_iou(box1, box2) - 1.0) < 1e-5

    box3 = (300, 300, 400, 400)
    assert compute_iou(box1, box3) == 0.0

    box4 = (150, 100, 250, 200)  # Half overlap
    iou = compute_iou(box1, box4)
    assert 0.3 < iou < 0.4


def test_tracker_id_persistence_and_matching():
    tracker = ByteTrackTracker(iou_threshold=0.3, max_missing_frames=5)
    dummy_crop = np.zeros((50, 50, 3), dtype=np.uint8)

    # Frame 1: One face at (100, 100, 200, 200)
    det1 = DetectedFace(bbox=(100, 100, 200, 200), normalized_bbox=(0.1, 0.1, 0.2, 0.2), confidence=0.9, cropped_face=dummy_crop)
    tracks1 = tracker.update([det1])

    assert len(tracks1) == 1
    initial_id = tracks1[0].track_id
    assert tracks1[0].age_frames == 1

    # Frame 2: Same face slightly moved to (105, 102, 205, 202)
    det2 = DetectedFace(bbox=(105, 102, 205, 202), normalized_bbox=(0.105, 0.102, 0.205, 0.202), confidence=0.92, cropped_face=dummy_crop)
    tracks2 = tracker.update([det2])

    assert len(tracks2) == 1
    assert tracks2[0].track_id == initial_id  # Same track ID retained!
    assert tracks2[0].age_frames == 2


def test_tracker_multiple_faces_and_pruning():
    tracker = ByteTrackTracker(max_missing_frames=2)
    dummy_crop = np.zeros((50, 50, 3), dtype=np.uint8)

    det_a = DetectedFace(bbox=(50, 50, 100, 100), normalized_bbox=(0.05, 0.05, 0.1, 0.1), confidence=0.88, cropped_face=dummy_crop)
    det_b = DetectedFace(bbox=(500, 500, 600, 600), normalized_bbox=(0.5, 0.5, 0.6, 0.6), confidence=0.91, cropped_face=dummy_crop)

    tracks = tracker.update([det_a, det_b])
    assert len(tracks) == 2

    # Frame without detections -> tracks become missing
    tracks_empty = tracker.update([])
    assert len(tracks_empty) == 0

    # Two more frames without detections -> dead tracks should be pruned
    tracker.update([])
    tracker.update([])
    assert len(tracker.active_tracks) == 0
