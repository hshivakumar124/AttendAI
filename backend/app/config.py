"""
AttendAI — Application Configuration
=====================================
All settings loaded from environment variables via pydantic-settings.
Never hardcode secrets. Use .env for local development.
"""

from functools import lru_cache
from typing import Any, Literal

from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Application ──────────────────────────────────────────────
    app_name: str = "AttendAI"
    app_version: str = "1.0.0"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    secret_key: str = "change-this-in-production"

    # ─── Backend API ──────────────────────────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(item) for item in v]
        return v

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env == "production":
            insecure = [
                "change-this-in-production",
                "change-this-jwt-secret",
                "dev_insecure_jwt_secret_change_in_production",
                "attendai_super_secret_jwt_key_production_2026",
            ]
            if self.secret_key in insecure or len(self.secret_key) < 32:
                raise ValueError("In production (APP_ENV=production), SECRET_KEY must be set to a cryptographically secure key of at least 32 characters.")
            if self.jwt_secret_key in insecure or len(self.jwt_secret_key) < 32:
                raise ValueError("In production (APP_ENV=production), JWT_SECRET_KEY must be set to a cryptographically secure key of at least 32 characters.")
        return self

    # ─── Database ─────────────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "attendai"
    postgres_user: str = "attendai_user"
    postgres_password: str = "attendai_pass"
    database_url: str = "postgresql+asyncpg://attendai_user:attendai_pass@localhost:5432/attendai"

    # ─── Redis ────────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_url: str = "redis://localhost:6379"

    # ─── JWT Authentication ───────────────────────────────────────
    jwt_secret_key: str = "change-this-jwt-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # ─── AI Service ───────────────────────────────────────────────
    ai_service_host: str = "localhost"
    ai_service_port: int = 8001
    ai_service_url: str = "http://localhost:8001"

    # ─── GPU Configuration ────────────────────────────────────────
    cuda_available: str = "auto"  # auto | true | false
    cuda_device: int = 0

    # ─── AI Pipeline Thresholds ───────────────────────────────────
    default_processing_fps: int = 10
    face_detection_interval: int = 3
    recognition_interval: int = 30
    device_detection_interval: int = 10
    engagement_window_seconds: int = 30

    face_detection_confidence: float = 0.7
    face_recognition_confidence: float = 0.6
    drowsiness_ear_threshold: float = 0.25
    drowsiness_consecutive_frames: int = 20
    device_detection_confidence: float = 0.5
    device_event_duration_seconds: int = 5

    # ─── Security ─────────────────────────────────────────────────
    bcrypt_rounds: int = 12
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    embeddings_encryption_key: str = "change-this-32-byte-encryption!!"

    # ─── Storage ──────────────────────────────────────────────────
    face_samples_dir: str = "./data/face_samples"
    reports_dir: str = "./data/reports"
    models_dir: str = "./ai_service/models"

    # ─── Logging ──────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "text"

    # ─── Email (optional) ─────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@attendai.local"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    Use dependency injection: Depends(get_settings)
    """
    return Settings()


# Module-level instance for direct imports
settings = get_settings()
