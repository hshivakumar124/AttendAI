"""
AttendAI — FaceDetector Tests
"""

import numpy as np
from ai_service.ingest.stream_reader import StreamReader
from ai_service.pipeline.face_detector import FaceDetector, DetectedFace


def test_face_detector_initialization():
    detector = FaceDetector()
    assert detector.backend in ("yolov8", "opencv_cascade", "none")


def test_face_detector_on_synthetic_classroom():
    reader = StreamReader(source="synthetic", target_size=(1280, 720))
    reader.open()
    _, frame, _ = reader.read_frame()
    reader.close()

    detector = FaceDetector(confidence_threshold=0.5)
    faces = detector.detect_faces(frame)

    assert isinstance(faces, list)
    # Synthetic frame contains 2 simulated faces
    if detector.backend == "opencv_cascade":
        assert len(faces) >= 1
        face = faces[0]
        assert isinstance(face, DetectedFace)
        assert len(face.bbox) == 4
        assert len(face.normalized_bbox) == 4
        assert face.confidence > 0.0
        assert face.cropped_face is not None
        assert face.cropped_face.size > 0
