"""
AttendAI — Institution API Router
===================================
CRUD for Institutions and Departments.
Only Super Admin and Admin can manage institutions.
"""

import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.core.permissions import require_admin_or_above, require_faculty_or_above
from app.database import get_db
from app.models.institution import Institution, Department
from app.models.user import User
from app.schemas.institution import (
    InstitutionCreate, InstitutionUpdate, InstitutionResponse,
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


# ─── Institutions ─────────────────────────────────────────────────────────────

@router.get("", response_model=list[InstitutionResponse], summary="List all institutions")
async def list_institutions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_faculty_or_above()),
):
    result = await db.execute(select(Institution).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("", response_model=InstitutionResponse, status_code=201, summary="Create institution")
async def create_institution(
    body: InstitutionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_or_above()),
):
    existing = await db.execute(select(Institution).where(Institution.code == body.code.upper()))
    if existing.scalar_one_or_none():
        raise ConflictException(f"Institution code '{body.code}' already exists")

    institution = Institution(
        name=body.name,
        code=body.code.upper(),
        address=body.address,
        contact_email=body.contact_email,
        contact_phone=body.contact_phone,
    )
    db.add(institution)
    await db.flush()
    logger.info("Institution created", id=str(institution.id), code=institution.code)
    return institution


@router.get("/{institution_id}", response_model=InstitutionResponse)
async def get_institution(
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_faculty_or_above()),
):
    result = await db.execute(select(Institution).where(Institution.id == institution_id))
    institution = result.scalar_one_or_none()
    if not institution:
        raise NotFoundException("Institution", str(institution_id))
    return institution


@router.put("/{institution_id}", response_model=InstitutionResponse)
async def update_institution(
    institution_id: uuid.UUID,
    body: InstitutionUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_or_above()),
):
    result = await db.execute(select(Institution).where(Institution.id == institution_id))
    institution = result.scalar_one_or_none()
    if not institution:
        raise NotFoundException("Institution", str(institution_id))

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(institution, field, value)
    await db.flush()
    return institution


# ─── Departments ──────────────────────────────────────────────────────────────

@router.get("/{institution_id}/departments", response_model=list[DepartmentResponse])
async def list_departments(
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_faculty_or_above()),
):
    result = await db.execute(
        select(Department).where(Department.institution_id == institution_id)
    )
    return result.scalars().all()


@router.post("/{institution_id}/departments", response_model=DepartmentResponse, status_code=201)
async def create_department(
    institution_id: uuid.UUID,
    body: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_or_above()),
):
    inst = await db.execute(select(Institution).where(Institution.id == institution_id))
    if not inst.scalar_one_or_none():
        raise NotFoundException("Institution", str(institution_id))

    dept = Department(
        institution_id=institution_id,
        name=body.name,
        code=body.code.upper(),
        description=body.description,
    )
    db.add(dept)
    await db.flush()
    return dept
