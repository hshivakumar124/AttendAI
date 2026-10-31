"""
AttendAI — AI Configuration
=============================
Settings for the AI inference service.
Thresholds, model paths, GPU config, pipeline intervals.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    # GPU
    cuda_available: str = "auto"
    cuda_device: int = 0

    # Pipeline
    default_processing_fps: int = 10
    face_detection_interval: int = 3
    recognition_interval: int = 30
    device_detection_interval: int = 10
    engagement_window_seconds: int = 30

    # Thresholds
    face_detection_confidence: float = 0.7
    face_recognition_confidence: float = 0.6
    drowsiness_ear_threshold: float = 0.25
    drowsiness_consecutive_frames: int = 20
    device_detection_confidence: float = 0.5
    device_event_duration_seconds: int = 5

    # Engagement weights (must sum to 1.0)
    engagement_weight_head_pose: float = 0.35
    engagement_weight_eye_state: float = 0.30
    engagement_weight_face_visibility: float = 0.20
    engagement_weight_looking_away: float = 0.15

    # Model paths
    models_dir: str = "./models"
    yolo_face_model: str = "yolov8n-face.pt"
    yolo_device_model: str = "yolov8n.pt"
    arcface_model: str = "buffalo_l"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Backend API
    backend_api_url: str = "http://localhost:8000/api/v1"


ai_settings = AISettings()
