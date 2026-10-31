"""
AttendAI — Face Embedding Model
=================================
Stores encrypted face embeddings for registered students.
Raw face images are NOT stored unless explicitly required.
Consent must be recorded before enrollment.

Privacy: Embeddings are AES-256 encrypted at rest.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, LargeBinary, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Encrypted embedding bytes (AES-256)
    embedding_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    # Dimension of the original embedding vector (e.g., 512 for ArcFace)
    embedding_dim: Mapped[int] = mapped_column(Integer, default=512, nullable=False)
    # Which AI model generated this embedding
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="arcface_r100")
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")

    # Quality metrics of the enrollment sample
    enrollment_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    num_samples_used: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Consent tracking (required before enrollment)
    consent_recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="face_embeddings")  # noqa: F821

    def __repr__(self) -> str:
        return f"<FaceEmbedding user={self.user_id} model={self.model_name} active={self.is_active}>"
