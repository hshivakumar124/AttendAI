"""
AttendAI — API v1 Router
=========================
Aggregates all v1 API sub-routers.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.institutions import router as institutions_router
from app.api.v1.classrooms import classrooms_router, sessions_router, courses_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.websocket import router as ws_router
from app.api.v1.analytics import router as analytics_router

router = APIRouter()


# ─── Health ──────────────────────────────────────────────────────────────────
@router.get("/ping", tags=["Health"])
async def ping():
    return {"message": "AttendAI API v1 is running ✅"}


# ─── Auth ─────────────────────────────────────────────────────────────────────
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# ─── Users ────────────────────────────────────────────────────────────────────
router.include_router(users_router, prefix="/users", tags=["Users"])

# ─── Institutions ─────────────────────────────────────────────────────────────
router.include_router(institutions_router, prefix="/institutions", tags=["Institutions"])

# ─── Courses ──────────────────────────────────────────────────────────────────
router.include_router(courses_router, prefix="/courses", tags=["Courses"])

# ─── Classrooms ───────────────────────────────────────────────────────────────
router.include_router(classrooms_router, prefix="/classrooms", tags=["Classrooms"])

# ─── Sessions ─────────────────────────────────────────────────────────────────
router.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])

# ─── Attendance & Enrollment ──────────────────────────────────────────────────
router.include_router(attendance_router, prefix="/attendance", tags=["Attendance & Enrollment"])

# ─── Analytics & Export Reports ───────────────────────────────────────────────
router.include_router(analytics_router, prefix="/analytics", tags=["Analytics & Export"])

# ─── Real-Time WebSocket Gateway ──────────────────────────────────────────────
router.include_router(ws_router, prefix="/ws", tags=["Real-Time WebSockets"])
