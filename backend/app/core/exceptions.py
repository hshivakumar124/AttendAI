"""
AttendAI — Custom Exceptions
==============================
Centralized exception hierarchy for consistent API error responses.
"""

from fastapi import status


class AttendAIException(Exception):
    """Base exception for all AttendAI custom errors."""

    def __init__(self, detail: str, code: str = "ERROR", status_code: int = status.HTTP_400_BAD_REQUEST):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        super().__init__(detail)


class NotFoundException(AttendAIException):
    def __init__(self, resource: str, resource_id: str = ""):
        msg = f"{resource} not found" + (f": {resource_id}" if resource_id else "")
        super().__init__(detail=msg, code="NOT_FOUND", status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedException(AttendAIException):
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(detail=detail, code="UNAUTHORIZED", status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AttendAIException):
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(detail=detail, code="FORBIDDEN", status_code=status.HTTP_403_FORBIDDEN)


class ConflictException(AttendAIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, code="CONFLICT", status_code=status.HTTP_409_CONFLICT)


class ValidationException(AttendAIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, code="VALIDATION_ERROR", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class BiometricConsentException(AttendAIException):
    def __init__(self, detail: str = "Biometric consent has not been provided"):
        super().__init__(detail=detail, code="CONSENT_REQUIRED", status_code=status.HTTP_400_BAD_REQUEST)


BiometricConsentRequiredException = BiometricConsentException


class SessionNotActiveException(AttendAIException):
    def __init__(self):
        super().__init__(
            detail="No active classroom session found",
            code="SESSION_NOT_ACTIVE",
            status_code=status.HTTP_409_CONFLICT,
        )


class AIServiceException(AttendAIException):
    def __init__(self, detail: str = "AI inference service is unavailable"):
        super().__init__(detail=detail, code="AI_SERVICE_ERROR", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
