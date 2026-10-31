"""
AttendAI — Face Enrollment & Attendance API Tests
"""

import io
import cv2
import numpy as np
import pytest

STUDENT_ENROLL = {
    "email": "enroll_student@attendai.com",
    "password": "EnrollStudent123",
    "full_name": "Enrollment Student",
    "role": "student",
}

FACULTY_ENROLL = {
    "email": "enroll_faculty@attendai.com",
    "password": "EnrollFaculty456",
    "full_name": "Enrollment Faculty",
    "role": "faculty",
}


def register_and_login(client, user_data: dict) -> tuple[str, str]:
    client.post("/api/v1/auth/register", json=user_data)
    resp = client.post("/api/v1/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"],
    })
    token = resp.json()["access_token"]
    user_id = resp.json()["user"]["id"]
    return token, user_id


def create_dummy_face_image_bytes() -> bytes:
    """Create a dummy BGR face image as JPEG bytes."""
    img = np.full((300, 300, 3), (200, 200, 200), dtype=np.uint8)
    # Draw simple face features
    cv2.circle(img, (150, 150), 70, (150, 180, 220), -1)
    cv2.circle(img, (125, 130), 10, (40, 40, 40), -1)
    cv2.circle(img, (175, 130), 10, (40, 40, 40), -1)
    cv2.line(img, (130, 180), (170, 180), (40, 40, 150), 3)

    _, encoded = cv2.imencode(".jpg", img)
    return encoded.tobytes()


class TestFaceEnrollment:
    def test_enrollment_requires_biometric_consent(self, client):
        """Enrollment should fail if consent_biometric is False."""
        token, _ = register_and_login(client, STUDENT_ENROLL)
        img_bytes = create_dummy_face_image_bytes()

        resp = client.post(
            "/api/v1/attendance/enroll-face",
            files={"file": ("face.jpg", io.BytesIO(img_bytes), "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert "consent required" in resp.json()["detail"].lower()

    def test_enrollment_success_after_granting_consent(self, client):
        """Enrollment succeeds after granting biometric consent."""
        token, user_id = register_and_login(client, STUDENT_ENROLL)

        # 1. Grant consent
        consent_resp = client.post(
            f"/api/v1/users/{user_id}/grant-biometric-consent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert consent_resp.status_code == 200

        # 2. Enroll face
        img_bytes = create_dummy_face_image_bytes()
        resp = client.post(
            "/api/v1/attendance/enroll-face",
            files={"file": ("face.jpg", io.BytesIO(img_bytes), "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "embedding_id" in data
        assert data["user_id"] == user_id
        assert data["is_active"] is True


class TestManualAttendance:
    def test_faculty_manual_override(self, client):
        f_token, _ = register_and_login(client, FACULTY_ENROLL)
        _, s_id = register_and_login(client, STUDENT_ENROLL)

        import uuid
        session_id = str(uuid.uuid4())

        resp = client.post(
            "/api/v1/attendance/mark",
            json={
                "session_id": session_id,
                "student_id": s_id,
                "status": "present",
                "confidence": 1.0,
                "remarks": "Manual check-in by faculty",
            },
            headers={"Authorization": f"Bearer {f_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "present"
        assert resp.json()["verification_type"] == "manual_override"
