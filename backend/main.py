"""
AttendAI — FastAPI Application Entry Point
==========================================
Production-grade FastAPI app with:
- Async lifespan (startup/shutdown)
- CORS middleware
- Rate limiting
- Structured logging
- Health check endpoint
- API versioning (v1)
- OpenAPI documentation
"""

import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import engine, create_all_tables
from app.core.exceptions import AttendAIException
from app.core.middleware import RequestLoggingMiddleware
from app.utils.redis_client import get_redis_client

# ─── Logging Setup ────────────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer() if settings.is_development else structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger(__name__)

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    """
    # ── Startup ──
    logger.info("🚀 AttendAI starting up", version=settings.app_version, env=settings.app_env)

    # Verify DB connection (non-fatal in development — allows running without Docker)
    try:
        import sqlalchemy
        async with engine.connect() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        logger.info("✅ Database connection established")
        # In development, auto-create tables (use Alembic in production)
        if settings.is_development:
            await create_all_tables()
            logger.info("✅ Database tables verified (dev mode)")
    except Exception as e:
        if settings.is_development:
            logger.warning(
                "⚠️  Database not available — start PostgreSQL or use Docker Compose",
                error=str(e),
            )
        else:
            logger.error("❌ Database connection failed", error=str(e))
            raise

    # Verify Redis connection (non-fatal)
    try:
        redis = await get_redis_client()
        await redis.ping()
        logger.info("✅ Redis connection established")
    except Exception as e:
        logger.warning("⚠️  Redis not available — real-time WebSocket features disabled", error=str(e))

    logger.info("✅ AttendAI is ready to serve requests")
    yield

    # ── Shutdown ──
    logger.info("🔴 AttendAI shutting down gracefully")
    await engine.dispose()
    logger.info("✅ Database connections closed")


# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="AttendAI",
    description=(
        "AI-Powered Smart Classroom Attendance & Visual Engagement Intelligence Platform. "
        "Provides real-time face recognition, multi-object tracking, visual engagement estimation, "
        "drowsiness detection, and device activity monitoring for classrooms."
    ),
    version=settings.app_version,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# ─── Custom Middleware ────────────────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)


# ─── Global Exception Handlers ───────────────────────────────────────────────
@app.exception_handler(AttendAIException)
async def attendai_exception_handler(request: Request, exc: AttendAIException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred.", "code": "INTERNAL_ERROR"},
    )


# ─── Health Check ────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"], summary="System health check")
async def health_check():
    """
    Returns system health status.
    Useful for Docker healthchecks and uptime monitors.
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@app.get("/", tags=["Health"], summary="Root endpoint")
async def root():
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": settings.app_version,
        "docs": "/docs",
    }


# ─── API Routers ─────────────────────────────────────────────────────────────
# Imported here to allow circular import resolution
from app.api.v1 import router as api_v1_router  # noqa: E402

app.include_router(api_v1_router, prefix="/api/v1")
