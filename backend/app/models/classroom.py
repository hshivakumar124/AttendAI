"""
AttendAI — Classroom & Camera Models
======================================
Classrooms are physical rooms with associated cameras.
Cameras are the video input sources for the AI pipeline.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CameraType(str, enum.Enum):
    WEBCAM = "webcam"
    IP_CAMERA = "ip_camera"
    RTSP = "rtsp"
    USB = "usb"
    LOCAL_TEST = "local_test"   # For development with a local video file


class CameraStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    STREAMING = "streaming"


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    building: Mapped[str | None] = mapped_column(String(100), nullable=True)
    floor: Mapped[str | None] = mapped_column(String(20), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    institution: Mapped["Institution"] = relationship(  # noqa: F821
        "Institution", back_populates="classrooms"
    )
    cameras: Mapped[list["Camera"]] = relationship(
        "Camera", back_populates="classroom", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["ClassSession"]] = relationship(  # noqa: F821
        "ClassSession", back_populates="classroom"
    )

    def __repr__(self) -> str:
        return f"<Classroom {self.name} [{self.building}]>"


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    camera_type: Mapped[CameraType] = mapped_column(Enum(CameraType), nullable=False)
    stream_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # For webcam: integer index (0, 1, 2...)
    device_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # For local test: path to video file
    local_video_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[CameraStatus] = mapped_column(
        Enum(CameraStatus), default=CameraStatus.INACTIVE, nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # JSON config: resolution, fps, etc.
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=lambda: {
        "resolution": "1280x720",
        "fps": 30,
        "processing_fps": 10,
    })

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="cameras")

    def __repr__(self) -> str:
        return f"<Camera {self.name} [{self.camera_type}] → {self.stream_url or self.device_index}>"
