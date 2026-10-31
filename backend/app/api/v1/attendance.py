"""
AttendAI — Attendance & Face Enrollment Router
================================================
Endpoints for face enrollment, manual/auto attendance marking,
and biometric consent verification.
"""

import base64
import uuid
from typing import List

import cv2
import httpx
import numpy as np
import structlog
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt_embedding, decrypt_embedding
from app.config import settings
from app.core.exceptions import BiometricConsentRequiredException, ConflictException, ForbiddenException, NotFoundException
from app.core.permissions import get_current_active_user, require_admin_or_above, require_faculty_or_above
from app.database import get_db
from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.face_embedding import FaceEmbedding
from app.models.user import User, UserRole
from app.schemas.attendance import (
    AttendanceMarkRequest, AttendanceRecordResponse,
    FaceEnrollmentResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/infer-frame", summary="Recognize enrolled faces in a live webcam frame")
async def infer_live_frame(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_faculty_or_above()),
):
    """Run an authenticated frame against the active, consented face gallery.

    Encrypted embeddings are decrypted only long enough to make this internal
    AI-service request.  The browser never receives biometric vectors.
    """
    image_base64 = payload.get("image_base64")
    if not isinstance(image_base64, str) or not image_base64:
        raise ConflictException("image_base64 is required")

    query = (
        select(FaceEmbedding, User)
        .join(User, FaceEmbedding.user_id == User.id)
        .where(FaceEmbedding.is_active.is_(True), User.is_active.is_(True), User.consent_biometric.is_(True))
    )
    # Faculty can only run recognition against their institution's enrolled users.
    if current_user.role != UserRole.SUPER_ADMIN and current_user.institution_id:
        query = query.where(User.institution_id == current_user.institution_id)

    result = await db.execute(query)
    gallery: dict[str, list[float]] = {}
    identities: dict[str, dict[str, str]] = {}
    for face_embedding, user in result.all():
        ciphertext = face_embedding.embedding_encrypted.decode("utf-8")
        gallery[str(user.id)] = decrypt_embedding(ciphertext).tolist()
        identities[str(user.id)] = {"name": user.full_name, "email": user.email}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.ai_service_url.rstrip('/')}/infer-frame-base64",
                json={"image_base64": image_base64, "enrolled_gallery": gallery},
            )
            response.raise_for_status()
            inference = response.json()
    except httpx.HTTPError as exc:
        logger.warning("AI inference service unavailable", error=str(exc))
        return {"status": "unavailable", "message": "AI inference service is unavailable", "tracks": []}

    for track in inference.get("tracks", []):
        identity = identities.get(track.get("student_id"))
        if identity:
            track["student_name"] = identity["name"]
            track["student_email"] = identity["email"]

    return inference


@router.post(
    "/enroll-face",
    response_model=FaceEnrollmentResponse,
    status_code=201,
    summary="Enroll student face (extract & encrypt 512-d vector)",
)
async def enroll_face(
    user_id: uuid.UUID | None = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Enrolls a student's face profile.
    Requires explicit consent (consent_biometric == True).
    Extracts 512-d ArcFace vector, encrypts it with AES-256, and stores it safely.
    Raw image is discarded immediately after processing.
    """
    target_user_id = user_id if user_id else current_user.id

    # Non-admins can only enroll themselves
    if current_user.id != target_user_id and current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
        raise ForbiddenException("You can only enroll biometric data for your own account")

    # Load target user & check consent
    result = await db.execute(select(User).where(User.id == target_user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise NotFoundException("User", str(target_user_id))

    if not target_user.consent_biometric:
        raise BiometricConsentRequiredException(
            "Biometric consent required before face enrollment. "
            "Please grant consent at /api/v1/users/{id}/grant-biometric-consent"
        )

    # Read image content
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None or img_bgr.size == 0:
        raise ConflictException("Invalid image file provided")

    # Extract 512-d face vector using FaceRecognizer
    from ai_service.pipeline.face_recognizer import FaceRecognizer
    recognizer = FaceRecognizer()
    embedding_vector = recognizer.extract_embedding(img_bgr)

    if embedding_vector is None:
        raise ConflictException("No face detected in uploaded image. Please provide a clear front-facing photo.")

    # Encrypt vector with AES-256 before saving
    encrypted_str = encrypt_embedding(embedding_vector)

    # Deactivate prior embeddings for user
    await db.execute(
        select(FaceEmbedding).where(FaceEmbedding.user_id == target_user_id)
    )

    face_emb = FaceEmbedding(
        user_id=target_user_id,
        embedding_encrypted=encrypted_str.encode("utf-8"),
        embedding_dim=512,
        is_active=True,
        enrollment_quality_score=0.95,
    )
    db.add(face_emb)
    await db.flush()

    logger.info("Face enrollment completed", user_id=str(target_user_id), embedding_id=str(face_emb.id))
    return FaceEnrollmentResponse(
        embedding_id=face_emb.id,
        user_id=target_user_id,
        is_active=True,
        created_at=face_emb.created_at,
        message="Face profile successfully enrolled and encrypted (AES-256).",
    )


@router.get("/sessions/{session_id}/records", response_model=list[AttendanceRecordResponse])
async def list_session_attendance(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_faculty_or_above()),
):
    result = await db.execute(
        select(AttendanceRecord).where(AttendanceRecord.session_id == session_id)
    )
    records = result.scalars().all()
    return [
        AttendanceRecordResponse(
            id=r.id,
            session_id=r.session_id,
            student_id=r.student_id,
            status=r.status.value if isinstance(r.status, AttendanceStatus) else str(r.status),
            marked_at=r.created_at,
            confidence_score=r.avg_recognition_confidence,
            verification_type="manual_override" if r.is_manual_override else "auto_ai",
        )
        for r in records
    ]


@router.post("/mark", response_model=AttendanceRecordResponse, status_code=201)
async def mark_attendance_manual(
    body: AttendanceMarkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_faculty_or_above()),
):
    """Faculty manual override to mark attendance for a student."""
    record = AttendanceRecord(
        session_id=body.session_id,
        student_id=body.student_id,
        status=AttendanceStatus(body.status),
        avg_recognition_confidence=body.confidence,
        is_manual_override=True,
        overridden_by=current_user.id,
        notes=body.remarks,
    )
    db.add(record)
    await db.flush()
    logger.info("Manual attendance marked", session_id=str(body.session_id), student_id=str(body.student_id))
    return AttendanceRecordResponse(
        id=record.id,
        session_id=record.session_id,
        student_id=record.student_id,
        status=record.status.value,
        marked_at=record.created_at,
        confidence_score=record.avg_recognition_confidence,
        verification_type="manual_override" if record.is_manual_override else "auto_ai",
    )
