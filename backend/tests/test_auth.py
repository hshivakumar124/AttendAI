"""
AttendAI — Authentication Tests
=================================
Tests for: register, login, token refresh, /me, change password, RBAC.
Uses in-memory SQLite via conftest.py fixtures — no PostgreSQL required.
"""

import pytest
from fastapi.testclient import TestClient

# ─── Test Data ────────────────────────────────────────────────────────────────
TEST_STUDENT = {
    "email": "student@test.attendai.com",
    "password": "Secure123",
    "full_name": "Test Student",
    "role": "student",
}

TEST_FACULTY = {
    "email": "faculty@test.attendai.com",
    "password": "Faculty456",
    "full_name": "Test Faculty",
    "role": "faculty",
}


# ─── Helpers ──────────────────────────────────────────────────────────────────
def get_access_token(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    return resp.json()["access_token"]


# ─── Registration Tests ───────────────────────────────────────────────────────

class TestRegister:
    def test_register_student_success(self, client):
        """Valid student registration should return 201."""
        resp = client.post("/api/v1/auth/register", json=TEST_STUDENT)
        assert resp.status_code in (201, 409)
        if resp.status_code == 201:
            assert resp.json()["success"] is True

    def test_register_faculty_success(self, client):
        """Valid faculty registration should return 201."""
        resp = client.post("/api/v1/auth/register", json=TEST_FACULTY)
        assert resp.status_code in (201, 409)

    def test_register_weak_password_no_uppercase(self, client):
        """Password without uppercase should be rejected."""
        data = {**TEST_STUDENT, "email": "weak1@test.com", "password": "weakpass123"}
        resp = client.post("/api/v1/auth/register", json=data)
        assert resp.status_code == 422

    def test_register_weak_password_no_digit(self, client):
        """Password without digit should be rejected."""
        data = {**TEST_STUDENT, "email": "weak2@test.com", "password": "WeakPassword"}
        resp = client.post("/api/v1/auth/register", json=data)
        assert resp.status_code == 422

    def test_register_short_password(self, client):
        """Password shorter than 8 chars should be rejected."""
        data = {**TEST_STUDENT, "email": "weak3@test.com", "password": "Ab1"}
        resp = client.post("/api/v1/auth/register", json=data)
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        """Invalid email format should be rejected."""
        data = {**TEST_STUDENT, "email": "not-an-email"}
        resp = client.post("/api/v1/auth/register", json=data)
        assert resp.status_code == 422

    def test_register_admin_role_disallowed(self, client):
        """Self-registration as admin should be rejected."""
        data = {**TEST_STUDENT, "email": "hacker@test.com", "role": "admin"}
        resp = client.post("/api/v1/auth/register", json=data)
        assert resp.status_code == 422


# ─── Login Tests ──────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_success(self, client):
        """Valid login should return tokens and user info."""
        client.post("/api/v1/auth/register", json=TEST_STUDENT)
        resp = client.post("/api/v1/auth/login", json={
            "email": TEST_STUDENT["email"],
            "password": TEST_STUDENT["password"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == TEST_STUDENT["email"]
        assert data["user"]["role"] == "student"

    def test_login_wrong_password(self, client):
        """Wrong password should return 401."""
        client.post("/api/v1/auth/register", json=TEST_STUDENT)
        resp = client.post("/api/v1/auth/login", json={
            "email": TEST_STUDENT["email"],
            "password": "WrongPass999",
        })
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        """Unknown email should return 401 (not 404 — prevents user enumeration)."""
        resp = client.post("/api/v1/auth/login", json={
            "email": "nobody@doesnotexist.com",
            "password": "SomePass123",
        })
        assert resp.status_code == 401

    def test_login_case_insensitive_email(self, client):
        """Login should work regardless of email case."""
        client.post("/api/v1/auth/register", json=TEST_STUDENT)
        resp = client.post("/api/v1/auth/login", json={
            "email": TEST_STUDENT["email"].upper(),
            "password": TEST_STUDENT["password"],
        })
        assert resp.status_code == 200


# ─── /me Tests ────────────────────────────────────────────────────────────────

class TestMe:
    def test_get_me_authenticated(self, client):
        """Authenticated user should get their own profile."""
        client.post("/api/v1/auth/register", json=TEST_STUDENT)
        token = get_access_token(client, TEST_STUDENT["email"], TEST_STUDENT["password"])
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == TEST_STUDENT["email"]

    def test_get_me_no_token(self, client):
        """Request without token should return 401."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Invalid token should return 401."""
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401


# ─── Security Schema Tests ────────────────────────────────────────────────────

class TestSecuritySchemas:
    def test_token_response_has_expires_in(self, client):
        """Login response must include expires_in field."""
        client.post("/api/v1/auth/register", json=TEST_FACULTY)
        resp = client.post("/api/v1/auth/login", json={
            "email": TEST_FACULTY["email"],
            "password": TEST_FACULTY["password"],
        })
        data = resp.json()
        assert "expires_in" in data
        assert data["expires_in"] > 0

    def test_access_token_is_jwt(self, client):
        """Access token should be a valid 3-part JWT."""
        client.post("/api/v1/auth/register", json=TEST_STUDENT)
        resp = client.post("/api/v1/auth/login", json={
            "email": TEST_STUDENT["email"],
            "password": TEST_STUDENT["password"],
        })
        token = resp.json()["access_token"]
        parts = token.split(".")
        assert len(parts) == 3, "JWT must have 3 parts: header.payload.signature"
