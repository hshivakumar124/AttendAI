"""
AttendAI — Classroom & Session API
=====================================
CRUD for classrooms, cameras, courses, and class sessions.
"""

import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, SessionNotActiveException
from app.core.permissions import get_current_active_user, require_admin_or_above, require_faculty_or_above
from app.database import get_db
from app.models.classroom import Camera, Classroom
from app.models.course import Course
from app.models.session import ClassSession, SessionStatus
from app.models.user import User, UserRole
from app.schemas.classroom import (
    CameraCreate, CameraResponse,
    ClassroomCreate, ClassroomResponse, ClassroomUpdate,
    CourseCreate, CourseResponse,
    SessionCreate, SessionResponse, SessionStartResponse,
)

logger = structlog.get_logger(__name__)

classrooms_router = APIRouter()
sessions_router = APIRouter()
courses_router = APIRouter()


# ─── Courses ──────────────────────────────────────────────────────────────────

@courses_router.get("", response_model=list[CourseResponse])
async def list_courses(
    department_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_faculty_or_above()),
):
    query = select(Course)
    if department_id:
        query = query.where(Course.department_id == department_id)
    result = await db.execute(query)
    return result.scalars().all()


@courses_router.post("", response_model=CourseResponse, status_code=201)
async def create_course(
    body: CourseCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_or_above()),
):
    course = Course(**body.model_dump())
    db.add(course)
    await db.flush()
    return course


# ─── Classrooms ───────────────────────────────────────────────────────────────

@classrooms_router.get("", response_model=list[ClassroomResponse])
async def list_classrooms(
    institution_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_faculty_or_above()),
):
    query = select(Classroom)
    if institution_id:
        query = query.where(Classroom.institution_id == institution_id)
    result = await db.execute(query)
    return result.scalars().all()


@classrooms_router.post("", response_model=ClassroomResponse, status_code=201)
async def create_classroom(
    body: ClassroomCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_or_above()),
):
    classroom = Classroom(**body.model_dump())
    db.add(classroom)
    await db.flush()
    return classroom


@classrooms_router.get("/{classroom_id}", response_model=ClassroomResponse)
async def get_classroom(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_faculty_or_above()),
):
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    if not classroom:
        raise NotFoundException("Classroom", str(classroom_id))
    return classroom


@classrooms_router.post("/{classroom_id}/cameras", response_model=CameraResponse, status_code=201)
async def add_camera(
    classroom_id: uuid.UUID,
    body: CameraCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_or_above()),
):
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    if not result.scalar_one_or_none():
        raise NotFoundException("Classroom", str(classroom_id))

    camera = Camera(classroom_id=classroom_id, **body.model_dump())
    db.add(camera)
    await db.flush()
    return camera


# ─── Sessions ─────────────────────────────────────────────────────────────────

@sessions_router.post("", response_model=SessionResponse, status_code=201,
                       summary="Schedule a new class session")
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_faculty_or_above()),
):
    session = ClassSession(
        course_id=body.course_id,
        classroom_id=body.classroom_id,
        faculty_id=current_user.id,
        camera_id=body.camera_id,
        scheduled_start=body.scheduled_start,
        scheduled_end=body.scheduled_end,
        topic=body.topic,
    )
    db.add(session)
    await db.flush()
    logger.info("Session created", session_id=str(session.id), faculty=str(current_user.id))
    return session


@sessions_router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_faculty_or_above()),
):
    result = await db.execute(select(ClassSession).where(ClassSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundException("ClassSession", str(session_id))
    return session


@sessions_router.post("/{session_id}/start", response_model=SessionStartResponse,
                       summary="Start a class session (activates AI pipeline)")
async def start_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_faculty_or_above()),
):
    result = await db.execute(select(ClassSession).where(ClassSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundException("ClassSession", str(session_id))

    if session.status == SessionStatus.ACTIVE:
        raise ConflictException("Session is already active")
    if session.status == SessionStatus.COMPLETED:
        raise ConflictException("Session is already completed")

    session.status = SessionStatus.ACTIVE
    session.actual_start = datetime.utcnow()
    await db.flush()

    logger.info("Session started", session_id=str(session_id), faculty=str(current_user.id))
    return SessionStartResponse(
        session_id=str(session_id),
        status="active",
        actual_start=session.actual_start,
        message="Session started. AI pipeline will activate shortly.",
    )


@sessions_router.post("/{session_id}/end", response_model=SessionResponse,
                       summary="End a class session")
async def end_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_faculty_or_above()),
):
    result = await db.execute(select(ClassSession).where(ClassSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundException("ClassSession", str(session_id))

    if session.status != SessionStatus.ACTIVE:
        raise SessionNotActiveException()

    session.status = SessionStatus.COMPLETED
    session.actual_end = datetime.utcnow()
    await db.flush()

    logger.info("Session ended", session_id=str(session_id))
    return session


@sessions_router.get("/{session_id}/live-stats", summary="Get live session statistics")
async def get_live_stats(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_faculty_or_above()),
):
    """Returns current live stats for an active session (polling fallback)."""
    result = await db.execute(select(ClassSession).where(ClassSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundException("ClassSession", str(session_id))

    return {
        "session_id": str(session_id),
        "status": session.status,
        "total_present": session.total_present,
        "total_registered": session.total_registered,
        "avg_engagement_score": session.avg_engagement_score,
        "device_events": session.total_device_events,
        "drowsiness_events": session.total_drowsiness_events,
        "actual_start": session.actual_start,
    }
