"""
AttendAI — Face Detection Module
=================================
High-accuracy face detection using YOLOv8-face with OpenCV DNN / Cascade fallback.
Outputs structured DetectedFace objects with bounding boxes, confidence scores,
and cropped face regions.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import cv2
import numpy as np
import structlog

from ai_service.config.ai_config import ai_settings
from ai_service.pipeline.preprocessing import crop_face, normalize_bbox

logger = structlog.get_logger(__name__)


@dataclass
class DetectedFace:
    """Dataclass representing a detected face in a video frame."""

    bbox: Tuple[int, int, int, int]  # Absolute (x1, y1, x2, y2)
    normalized_bbox: Tuple[float, float, float, float]  # (nx1, ny1, nx2, ny2) in [0, 1]
    confidence: float
    cropped_face: np.ndarray  # BGR crop
    landmarks: Optional[np.ndarray] = None  # 5-point facial landmarks if available


class FaceDetector:
    """
    Multi-backend Face Detector.

    Tries YOLOv8-face / Ultralytics first if available.
    Falls back to OpenCV Haar Cascade / DNN detector for CPU or offline modes.
    """

    def __init__(
        self,
        confidence_threshold: float = None,
        device: str = "cpu",
    ):
        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None else ai_settings.face_detection_confidence
        )
        self.device = device
        self.backend = "unknown"
        self._model = None
        self._cascade = None

        self._initialize_detector()

    def _initialize_detector(self) -> None:
        """Initialize YOLOv8 detector or fallback to OpenCV Haar Cascade."""
        try:
            from ultralytics import YOLO
            import os

            model_path = os.path.join(ai_settings.models_dir, ai_settings.yolo_face_model)
            if os.path.exists(model_path):
                self._model = YOLO(model_path)
                self.backend = "yolov8"
                logger.info("Loaded YOLOv8 face detection model", path=model_path)
                return
        except Exception as e:
            logger.debug("YOLOv8 face model load skipped", reason=str(e))

        # Fallback to OpenCV Haar Cascade (built-in, lightweight)
        try:
            cascade_cls = getattr(cv2, "CascadeClassifier", None)
            haarcascades_dir = getattr(getattr(cv2, "data", None), "haarcascades", None)
            if cascade_cls is not None and haarcascades_dir is not None:
                cascade_path = haarcascades_dir + "haarcascade_frontalface_default.xml"
                cascade = cascade_cls(cascade_path)
                if hasattr(cascade, "empty") and not cascade.empty():
                    self._cascade = cascade
                    self.backend = "opencv_cascade"
                    logger.info("Loaded OpenCV Haar Cascade face detector (fallback)")
                    return
            logger.debug("OpenCV Haar Cascade not available in this build — running in headless/mock mode")
            self.backend = "none"
        except Exception as e:
            logger.debug("OpenCV Haar Cascade initialization skipped", reason=str(e))
            self.backend = "none"

    def detect_faces(self, frame_bgr: np.ndarray) -> List[DetectedFace]:
        """
        Detect faces in a BGR frame.

        Returns:
            List[DetectedFace]
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return []

        h, w = frame_bgr.shape[:2]
        detected: List[DetectedFace] = []

        if self.backend == "yolov8" and self._model is not None:
            results = self._model(frame_bgr, conf=self.confidence_threshold, verbose=False)
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    conf = float(box.conf[0])
                    if conf < self.confidence_threshold:
                        continue
                    xyxy = box.xyxy[0].cpu().numpy().astype(int)
                    x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                    bbox = (max(0, x1), max(0, y1), min(w, x2), min(h, y2))
                    norm_box = normalize_bbox(bbox, w, h)
                    crop, _ = crop_face(frame_bgr, bbox)

                    detected.append(
                        DetectedFace(
                            bbox=bbox,
                            normalized_bbox=norm_box,
                            confidence=conf,
                            cropped_face=crop,
                        )
                    )

        elif self.backend == "opencv_cascade" and self._cascade is not None:
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            faces = self._cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
            )

            for (x, y, fw, fh) in faces:
                x1, y1, x2, y2 = x, y, x + fw, y + fh
                bbox = (x1, y1, x2, y2)
                norm_box = normalize_bbox(bbox, w, h)
                crop, _ = crop_face(frame_bgr, bbox)
                # Assign a synthetic confidence for cascade detections
                conf = 0.85

                detected.append(
                    DetectedFace(
                        bbox=bbox,
                        normalized_bbox=norm_box,
                        confidence=conf,
                        cropped_face=crop,
                    )
                )

        return detected
