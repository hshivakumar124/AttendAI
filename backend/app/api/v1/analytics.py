"""
AttendAI — Analytics & Reporting Router
==========================================
API Endpoints for session intelligence summaries and CSV attendance export downloads.
"""

import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_roles
from app.database import get_db
from app.models.user import UserRole
from app.services.reporting_service import ReportingService

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get(
    "/sessions/{session_id}/summary",
    response_model=dict,
    dependencies=[Depends(require_roles(UserRole.FACULTY, UserRole.ADMIN, UserRole.SUPER_ADMIN))],
)
async def get_session_summary(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated analytics summary for a classroom session.
    """
    service = ReportingService(db)
    try:
        return await service.get_session_summary(session_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/sessions/{session_id}/export/csv",
    dependencies=[Depends(require_roles(UserRole.FACULTY, UserRole.ADMIN, UserRole.SUPER_ADMIN))],
)
async def export_attendance_csv(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Download session attendance report in CSV format.
    """
    service = ReportingService(db)
    try:
        csv_content = await service.generate_attendance_csv(session_id)
        filename = f"session_{session_id}_attendance.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error("Failed to generate CSV export", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="CSV generation failed")
