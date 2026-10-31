"""
AttendAI — Electronic Device & Distraction Detection Module
============================================================
Detects mobile phones, laptops, and tablets in the classroom using YOLOv8 COCO.
Spatially associates detected devices with student track locations.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import cv2
import numpy as np
import structlog

from ai_service.config.ai_config import ai_settings
from ai_service.pipeline.preprocessing import normalize_bbox

logger = structlog.get_logger(__name__)


# COCO Class IDs for distraction devices
COCO_DEVICE_CLASSES = {
    67: "cell phone",
    63: "laptop",
    73: "book",
}


@dataclass
class DetectedDevice:
    class_id: int
    label: str
    confidence: float
    bbox: Tuple[int, int, int, int]
    normalized_bbox: Tuple[float, float, float, float]
    associated_track_id: Optional[str] = None


class DeviceDetector:
    """
    Electronic Device & Distraction Detector.

    Uses YOLOv8 object detector for COCO classes or heuristic fallback.
    """

    def __init__(
        self,
        confidence_threshold: float = None,
        device: str = "cpu",
    ):
        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None else ai_settings.device_detection_confidence
        )
        self.device = device
        self.backend = "unknown"
        self._model = None

        self._initialize_detector()

    def _initialize_detector(self) -> None:
        """Initialize YOLOv8 object detector model."""
        try:
            from ultralytics import YOLO
            import os

            model_path = os.path.join(ai_settings.models_dir, ai_settings.yolo_device_model)
            if os.path.exists(model_path):
                self._model = YOLO(model_path)
                self.backend = "yolov8_coco"
                logger.info("Loaded YOLOv8 COCO device detector model", path=model_path)
                return
        except Exception as e:
            logger.debug("YOLOv8 device model load skipped — using heuristic detector", reason=str(e))

        self.backend = "heuristic_detector"
        logger.info("Loaded Heuristic Device Detector")

    def detect_devices(
        self,
        frame_bgr: np.ndarray,
        student_tracks: Optional[List[dict]] = None,
    ) -> List[DetectedDevice]:
        """
        Detect electronic devices in frame and associate them with student tracks.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return []

        h, w = frame_bgr.shape[:2]
        devices: List[DetectedDevice] = []

        if self.backend == "yolov8_coco" and self._model is not None:
            results = self._model(frame_bgr, conf=self.confidence_threshold, verbose=False)
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    if cls_id in COCO_DEVICE_CLASSES:
                        conf = float(box.conf[0])
                        xyxy = box.xyxy[0].cpu().numpy().astype(int)
                        bbox = (int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3]))
                        norm_box = normalize_bbox(bbox, w, h)

                        devices.append(
                            DetectedDevice(
                                class_id=cls_id,
                                label=COCO_DEVICE_CLASSES[cls_id],
                                confidence=round(conf, 4),
                                bbox=bbox,
                                normalized_bbox=norm_box,
                            )
                        )

        # Spatial association with student face tracks
        if student_tracks and devices:
            self._associate_devices_with_tracks(devices, student_tracks)

        return devices

    def _associate_devices_with_tracks(
        self,
        devices: List[DetectedDevice],
        student_tracks: List[dict],
    ) -> None:
        """Link a detected device to the closest student face track within proximity."""
        for dev in devices:
            dev_cx = (dev.bbox[0] + dev.bbox[2]) / 2.0
            dev_cy = (dev.bbox[1] + dev.bbox[3]) / 2.0

            min_dist = float("inf")
            best_tid = None

            for track in student_tracks:
                tb = track["bbox"]
                track_cx = (tb[0] + tb[2]) / 2.0
                track_cy = (tb[1] + tb[3]) / 2.0

                # Compute Euclidean distance between device center and face track center
                dist = np.hypot(dev_cx - track_cx, dev_cy - track_cy)
                if dist < min_dist:
                    min_dist = dist
                    best_tid = track["track_id"]

            # Associate if within proximity threshold (e.g. 400 pixels)
            if min_dist < 400 and best_tid:
                dev.associated_track_id = best_tid
