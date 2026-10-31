"""
AttendAI — Request Logging Middleware
=======================================
Logs every request with timing, status code, and request ID.
Adds X-Request-ID and X-Process-Time response headers.
"""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Generates a unique X-Request-ID for each request
    2. Measures total request processing time
    3. Logs method, path, status, duration for every request
    4. Adds timing headers to all responses
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Add request ID to request state for use in route handlers
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration_ms}ms"

        # Skip logging for health checks to reduce noise
        if request.url.path not in ("/health", "/"):
            logger.info(
                "Request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=request_id,
            )

        return response
