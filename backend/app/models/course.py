"""
AttendAI — Course Model
========================
Courses belong to departments and are associated with class sessions.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    credits: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    semester: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "2024-Spring"
    academic_year: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. "2024-25"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="courses")  # noqa: F821
    sessions: Mapped[list["ClassSession"]] = relationship(  # noqa: F821
        "ClassSession", back_populates="course"
    )

    def __repr__(self) -> str:
        return f"<Course {self.code}: {self.name}>"
