"""
AttendAI — User Management API
================================
Admin endpoints for managing users, face enrollment consent,
and user activation/deactivation.
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.core.permissions import get_current_active_user, require_admin_or_above, require_faculty_or_above
from app.core.security import hash_password
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import MessageResponse
from app.schemas.user import UserCreateRequest, UserListResponse, UserResponse, UserUpdateRequest

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("", response_model=UserListResponse, summary="List users (admin)")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: str | None = Query(None),
    institution_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_above()),
):
    query = select(User)
    if role:
        query = query.where(User.role == UserRole(role))
    if institution_id:
        query = query.where(User.institution_id == institution_id)
    # Non-super-admins can only see their own institution's users
    if current_user.role != UserRole.SUPER_ADMIN and current_user.institution_id:
        query = query.where(User.institution_id == current_user.institution_id)

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    result = await db.execute(query.offset(skip).limit(limit))
    items = result.scalars().all()
    return UserListResponse(total=total, items=items)


@router.post("", response_model=UserResponse, status_code=201, summary="Create user (admin)")
async def create_user(
    body: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_above()),
):
    # Only super admin can create other admins
    if body.role in ("super_admin", "admin") and current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException("Only Super Admin can create admin accounts")

    existing = await db.execute(select(User).where(User.email == body.email.lower()))
    if existing.scalar_one_or_none():
        raise ConflictException(f"Email '{body.email}' already registered")

    user = User(
        email=body.email.lower().strip(),
        hashed_password=hash_password(body.password),
        full_name=body.full_name.strip(),
        role=UserRole(body.role),
        institution_id=body.institution_id,
        department_id=body.department_id,
        is_active=True,
        is_verified=True,  # Admin-created users are pre-verified
    )
    db.add(user)
    await db.flush()
    logger.info("User created by admin", new_user_id=str(user.id), by=str(current_user.id))
    return user


@router.get("/me", response_model=UserResponse, summary="Get my full profile")
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
):
    return current_user


@router.put("/me", response_model=UserResponse, summary="Update my profile")
async def update_my_profile(
    body: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    updates = body.model_dump(exclude_none=True)
    # Users cannot change their own active status
    updates.pop("is_active", None)
    for field, value in updates.items():
        setattr(current_user, field, value)
    await db.flush()
    return current_user


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID (admin)")
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_or_above()),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User", str(user_id))
    return user


@router.put("/{user_id}", response_model=UserResponse, summary="Update user (admin)")
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_above()),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User", str(user_id))

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    await db.flush()
    return user


@router.post("/{user_id}/grant-biometric-consent", response_model=MessageResponse)
async def grant_biometric_consent(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    A student grants their own biometric (face enrollment) consent.
    Only the user themselves OR an admin can record consent.
    """
    if current_user.id != user_id and current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
        raise ForbiddenException("You can only grant consent for your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User", str(user_id))

    user.consent_biometric = True
    await db.flush()
    logger.info("Biometric consent granted", user_id=str(user_id), by=str(current_user.id))
    return MessageResponse(message="Biometric consent recorded successfully")


@router.delete("/{user_id}/biometric-data", response_model=MessageResponse)
async def delete_biometric_data(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Right to deletion: remove all face embeddings for a user."""
    if current_user.id != user_id and current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
        raise ForbiddenException("You can only delete your own biometric data")

    from app.models.face_embedding import FaceEmbedding
    from sqlalchemy import delete

    await db.execute(delete(FaceEmbedding).where(FaceEmbedding.user_id == user_id))

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.consent_biometric = False

    await db.flush()
    logger.info("Biometric data deleted (right to erasure)", user_id=str(user_id))
    return MessageResponse(message="All biometric data deleted successfully")
