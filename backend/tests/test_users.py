"""
AttendAI — User & Institution Management Tests
"""
import pytest


# ─── Fixtures ──────────────────────────────────────────────────────────────────
ADMIN_USER = {
    "email": "admin@attendai.com",
    "password": "Admin1234",
    "full_name": "System Admin",
    "role": "admin",
}

FACULTY_USER = {
    "email": "faculty2@attendai.com",
    "password": "Faculty789",
    "full_name": "Prof Smith",
    "role": "faculty",
}

STUDENT_USER = {
    "email": "student2@attendai.com",
    "password": "Student456",
    "full_name": "Jane Doe",
    "role": "student",
}


def register_and_login(client, user_data: dict) -> str:
    client.post("/api/v1/auth/register", json=user_data)
    resp = client.post("/api/v1/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"],
    })
    return resp.json()["access_token"]


# ─── User Tests ───────────────────────────────────────────────────────────────

class TestUserProfile:
    def test_get_my_profile(self, client):
        token = register_and_login(client, FACULTY_USER)
        resp = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == FACULTY_USER["email"]
        assert data["full_name"] == FACULTY_USER["full_name"]
        assert data["role"] == "faculty"

    def test_update_my_profile(self, client):
        token = register_and_login(client, FACULTY_USER)
        resp = client.put(
            "/api/v1/users/me",
            json={"full_name": "Prof Smith Updated"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Prof Smith Updated"

    def test_cannot_deactivate_self(self, client):
        """Users cannot change their own is_active status."""
        token = register_and_login(client, STUDENT_USER)
        resp = client.put(
            "/api/v1/users/me",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        # is_active is stripped, profile returned unchanged
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True


class TestBiometricConsent:
    def test_student_grants_own_consent(self, client):
        token = register_and_login(client, STUDENT_USER)
        # Get own user ID
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        user_id = me.json()["id"]

        resp = client.post(
            f"/api/v1/users/{user_id}/grant-biometric-consent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Verify consent recorded
        profile = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert profile.json()["consent_biometric"] is True

    def test_cannot_grant_consent_for_other_user(self, client):
        """Faculty cannot grant consent on behalf of a student."""
        student_token = register_and_login(client, STUDENT_USER)
        student_id = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {student_token}"}
        ).json()["id"]

        faculty_token = register_and_login(client, FACULTY_USER)
        resp = client.post(
            f"/api/v1/users/{student_id}/grant-biometric-consent",
            headers={"Authorization": f"Bearer {faculty_token}"},
        )
        assert resp.status_code == 403


# ─── Institution Tests ────────────────────────────────────────────────────────

class TestInstitutions:
    def test_faculty_can_list_institutions(self, client):
        token = register_and_login(client, FACULTY_USER)
        resp = client.get(
            "/api/v1/institutions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_student_cannot_list_institutions(self, client):
        token = register_and_login(client, STUDENT_USER)
        resp = client.get(
            "/api/v1/institutions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_unauthenticated_cannot_access(self, client):
        resp = client.get("/api/v1/institutions")
        assert resp.status_code == 401


# ─── Session Tests ────────────────────────────────────────────────────────────

class TestSessions:
    def test_student_cannot_create_session(self, client):
        token = register_and_login(client, STUDENT_USER)
        import uuid
        resp = client.post(
            "/api/v1/sessions",
            json={
                "course_id": str(uuid.uuid4()),
                "classroom_id": str(uuid.uuid4()),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_get_nonexistent_session(self, client):
        token = register_and_login(client, FACULTY_USER)
        import uuid
        resp = client.get(
            f"/api/v1/sessions/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
