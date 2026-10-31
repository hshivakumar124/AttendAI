"""
AttendAI — AI Pipeline Orchestrator
=====================================
The central controller that manages all AI modules.
Handles GPU/CPU device selection, model loading, and pipeline execution.
Each module is independently replaceable.
"""

import asyncio
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class PipelineOrchestrator:
    """
    Manages the full AI processing pipeline lifecycle.
    Initialized once at service startup, runs continuously during sessions.

    Pipeline:
    Video Frame → Face Detection → ByteTrack → Recognition (periodic) →
    Head Pose + Eye State + Drowsiness → Device Detection →
    Engagement Estimation → Event Generation → Redis Publish
    """

    def __init__(self):
        self.device: str = "cpu"
        self.models_loaded: bool = False
        self._active_sessions: dict[str, Any] = {}

        # AI modules (initialized in initialize())
        self.face_detector = None
        self.face_recognizer = None
        self.tracker = None
        self.head_pose = None
        self.eye_state = None
        self.drowsiness = None
        self.device_detector = None
        self.engagement_estimator = None

    async def initialize(self) -> None:
        """
        Detect GPU availability and load AI models (FaceDetector, etc.).
        Falls back gracefully if weights/GPU are not present.
        """
        # Initialize Face Detector, Recognizer, Tracker, HeadPose, EyeState, Device, Engagement & EventPublisher modules
        from ai_service.pipeline.face_detector import FaceDetector
        from ai_service.pipeline.face_recognizer import FaceRecognizer
        from ai_service.pipeline.tracker import ByteTrackTracker
        from ai_service.pipeline.head_pose import HeadPoseEstimator
        from ai_service.pipeline.eye_state import EyeStateEstimator, TemporalDrowsinessDetector
        from ai_service.pipeline.device_detector import DeviceDetector
        from ai_service.pipeline.engagement import EngagementEstimator
        from ai_service.events.event_publisher import EventPublisher

        self.face_detector = FaceDetector(device=self.device)
        self.face_recognizer = FaceRecognizer(device=self.device)
        self.tracker = ByteTrackTracker()
        self.head_pose = HeadPoseEstimator()
        self.eye_state = EyeStateEstimator()
        self.drowsiness = TemporalDrowsinessDetector()
        self.device_detector = DeviceDetector(device=self.device)
        self.engagement_estimator = EngagementEstimator()
        self.event_publisher = EventPublisher()
        await self.event_publisher.connect()

        logger.info(
            "AI pipeline modules initialized",
            detector_backend=self.face_detector.backend,
            recognizer_backend=self.face_recognizer.backend,
            device_backend=self.device_detector.backend,
        )
        self.models_loaded = True

    async def start_session_stream(self, session_id: str, source: Any = "synthetic") -> None:
        """Start an active processing session for a camera stream."""
        from ai_service.ingest.stream_reader import StreamReader
        from ai_service.pipeline.tracker import ByteTrackTracker
        from ai_service.pipeline.eye_state import TemporalDrowsinessDetector

        reader = StreamReader(source=source)
        if not reader.open():
            logger.error("Failed to open stream reader for session", session_id=session_id)
            return

        self._active_sessions[session_id] = {
            "reader": reader,
            "tracker": ByteTrackTracker(),
            "drowsiness": TemporalDrowsinessDetector(),
            "status": "running",
            "frame_count": 0,
            "faces_detected": 0,
        }
        logger.info("Session stream started", session_id=session_id, source=source)

    async def process_next_frame(self, session_id: str) -> dict:
        """Process the next single frame from a session stream."""
        session = self._active_sessions.get(session_id)
        if not session or session["status"] != "running":
            return {"status": "error", "message": "Session not running"}

        reader = session["reader"]
        session_tracker = session.get("tracker", self.tracker)
        session_drowsiness = session.get("drowsiness", self.drowsiness)

        success, frame, timestamp = reader.read_frame()
        if not success or frame is None:
            return {"status": "no_frame", "timestamp": timestamp}

        session["frame_count"] += 1
        faces = self.face_detector.detect_faces(frame) if self.face_detector else []
        session["faces_detected"] += len(faces)

        # Multi-object tracking update
        tracked_faces = session_tracker.update(faces) if session_tracker else []

        # Device / distraction detection
        devices = self.device_detector.detect_devices(
            frame, student_tracks=[{"track_id": f"track_{t.track_id}", "bbox": t.bbox} for t in tracked_faces]
        ) if self.device_detector else []

        distracted_track_ids = {d.associated_track_id for d in devices if d.associated_track_id}

        h, w = frame.shape[:2]
        processed_tracks = []

        for t in tracked_faces:
            tid_str = f"track_{t.track_id}"

            # 1. Evaluate Head Pose
            pose = self.head_pose.estimate_pose((h, w), bbox=t.bbox) if self.head_pose else None

            # 2. Evaluate Eye State & Drowsiness
            eye_res = self.eye_state.evaluate_eye_state() if self.eye_state else None
            is_drowsy, closed_count = (
                session_drowsiness.update_track(tid_str, eye_res.is_eye_open if eye_res else True)
                if session_drowsiness
                else (False, 0)
            )

            has_distraction = tid_str in distracted_track_ids

            # 3. Calculate Visual Engagement Score
            eng_res = (
                self.engagement_estimator.calculate_engagement(
                    head_orientation=pose.orientation_label if pose else "attentive",
                    is_eye_open=eye_res.is_eye_open if eye_res else True,
                    detection_confidence=t.confidence,
                    has_device_distraction=has_distraction,
                )
                if self.engagement_estimator
                else None
            )

            processed_tracks.append({
                "track_id": tid_str,
                "bbox": t.bbox,
                "normalized_bbox": t.normalized_bbox,
                "confidence": round(t.confidence, 4),
                "age_frames": t.age_frames,
                "student_id": t.student_id,
                "head_pose": {
                    "pitch": pose.pitch if pose else 0.0,
                    "yaw": pose.yaw if pose else 0.0,
                    "roll": pose.roll if pose else 0.0,
                    "orientation": pose.orientation_label if pose else "attentive",
                    "is_attentive": pose.is_attentive if pose else True,
                },
                "eye_state": {
                    "ear": eye_res.avg_ear if eye_res else 0.32,
                    "is_open": eye_res.is_eye_open if eye_res else True,
                    "drowsy_alert": is_drowsy,
                    "closed_frames": closed_count,
                },
                "engagement": {
                    "score": eng_res.score if eng_res else 85.0,
                    "label": eng_res.label if eng_res else "High",
                    "breakdown": eng_res.breakdown if eng_res else {},
                },
                "has_device_distraction": has_distraction,
            })

        return {
            "status": "ok",
            "session_id": session_id,
            "frame_number": session["frame_count"],
            "timestamp": timestamp,
            "detected_faces_count": len(faces),
            "tracked_faces_count": len(tracked_faces),
            "devices_detected_count": len(devices),
            "tracks": processed_tracks,
        }

    def process_direct_frame(self, frame: Any, enrolled_gallery: dict = None) -> dict:
        """
        Process a direct live video frame (e.g. from browser webcam WebSocket).
        Executes face detection, ArcFace vector recognition matching, ByteTrack tracking,
        3D Head Pose, EAR eye state drowsiness, device detection, and engagement scoring.
        """
        import time
        if frame is None:
            return {"status": "error", "message": "Invalid frame"}

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        faces = self.face_detector.detect_faces(frame) if self.face_detector else []
        tracked_faces = self.tracker.update(faces) if self.tracker else []

        # Device detection
        devices = self.device_detector.detect_devices(
            frame, student_tracks=[{"track_id": f"track_{t.track_id}", "bbox": t.bbox} for t in tracked_faces]
        ) if self.device_detector else []
        distracted_track_ids = {d.associated_track_id for d in devices if d.associated_track_id}

        h, w = frame.shape[:2]
        processed_tracks = []

        for t in tracked_faces:
            tid_str = f"track_{t.track_id}"
            x1, y1, x2, y2 = t.bbox
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            face_crop = frame[y1:y2, x1:x2]

            # Face Recognition matching against enrolled gallery
            # Detection is not recognition.  A face remains unknown unless it
            # matches an enrolled embedding above the configured threshold.
            student_id = None
            student_name = "Unknown face"
            score = 0.0

            if self.face_recognizer and face_crop.size > 0 and enrolled_gallery:
                query_emb = self.face_recognizer.extract_embedding(face_crop)
                matched_id, match_score = self.face_recognizer.match_face(query_emb, enrolled_gallery)
                if matched_id:
                    student_id = matched_id
                    student_name = matched_id
                    score = match_score

            # Head Pose & Eye State
            pose = self.head_pose.estimate_pose((h, w), bbox=t.bbox) if self.head_pose else None
            eye_res = self.eye_state.evaluate_eye_state() if self.eye_state else None
            is_drowsy, closed_count = self.drowsiness.update_track(tid_str, eye_res.is_eye_open if eye_res else True) if self.drowsiness else (False, 0)
            has_distraction = tid_str in distracted_track_ids

            # Engagement Calculation
            eng_res = self.engagement_estimator.calculate_engagement(
                head_orientation=pose.orientation_label if pose else "attentive",
                is_eye_open=eye_res.is_eye_open if eye_res else True,
                detection_confidence=t.confidence,
                has_device_distraction=has_distraction,
            ) if self.engagement_estimator else None

            processed_tracks.append({
                "track_id": tid_str,
                "bbox": t.bbox,
                "normalized_bbox": t.normalized_bbox,
                "confidence": round(score, 4),
                "student_id": student_id,
                "student_name": student_name,
                "head_pose": {
                    "orientation": pose.orientation_label if pose else "attentive",
                },
                "eye_state": {
                    "ear": eye_res.avg_ear if eye_res else 0.32,
                    "is_open": eye_res.is_eye_open if eye_res else True,
                    "drowsy_alert": is_drowsy,
                },
                "engagement_score": eng_res.score if eng_res else 95.0,
                "has_device_distraction": has_distraction,
            })

        return {
            "status": "ok",
            "timestamp": timestamp,
            "detected_faces_count": len(faces),
            "tracked_faces_count": len(tracked_faces),
            "devices_detected_count": len(devices),
            "tracks": processed_tracks,
        }

    async def _detect_device(self) -> str:
        """Detect if CUDA GPU is available, fall back to CPU."""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                logger.info("CUDA GPU detected", gpu=gpu_name)
                return "cuda:0"
        except ImportError:
            logger.warning("PyTorch not installed — GPU detection skipped")
        logger.info("Using CPU for inference")
        return "cpu"

    def get_device_info(self) -> dict:
        """Returns current device information."""
        info = {"device": self.device, "models_loaded": self.models_loaded}
        try:
            import torch
            if torch.cuda.is_available():
                info["gpu_name"] = torch.cuda.get_device_name(0)
                info["gpu_memory_total"] = f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB"
                info["gpu_memory_used"] = f"{torch.cuda.memory_allocated(0) / 1e9:.2f} GB"
        except ImportError:
            pass
        return info

    async def shutdown(self) -> None:
        """Gracefully stop all active sessions and release resources."""
        for session_id in list(self._active_sessions.keys()):
            await self.stop_session(session_id)
        logger.info("All AI sessions stopped")

    async def stop_session(self, session_id: str) -> None:
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            logger.info("AI session stopped", session_id=session_id)
