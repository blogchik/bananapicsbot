"""Tests for admin login response field alignment between backend and frontend."""

from datetime import datetime, timezone

import pytest
from app.schemas.admin import AdminInfo, AdminLoginResponse


class TestAdminLoginResponseFields:
    """Verify AdminLoginResponse fields match what the frontend LoginResponse interface expects."""

    def _make_response(self, **kwargs) -> AdminLoginResponse:
        defaults = {
            "access_token": "test.jwt.token",
            "token_type": "bearer",
            "admin": AdminInfo(telegram_id=123, username="admin", first_name="Admin"),
            "expires_at": datetime.now(timezone.utc),
        }
        defaults.update(kwargs)
        return AdminLoginResponse(**defaults)

    def test_response_has_access_token_field(self):
        """Backend must return 'access_token', not 'token'."""
        response = self._make_response(access_token="my.jwt.token")
        assert response.access_token == "my.jwt.token"

    def test_response_serializes_access_token_key(self):
        """Serialized JSON must use key 'access_token' — frontend LoginResponse reads this field."""
        response = self._make_response(access_token="my.jwt.token")
        data = response.model_dump()
        assert "access_token" in data, "JSON must contain 'access_token'"
        assert "token" not in data or data.get("token") is None, (
            "JSON must NOT contain a bare 'token' key that would shadow 'access_token'"
        )
        assert data["access_token"] == "my.jwt.token"

    def test_response_has_token_type_field(self):
        """Backend must include 'token_type' so the frontend can verify bearer scheme."""
        response = self._make_response()
        assert response.token_type == "bearer"
        data = response.model_dump()
        assert data["token_type"] == "bearer"

    def test_response_has_admin_field(self):
        """Backend must return 'admin' object matching AdminInfo schema."""
        admin = AdminInfo(telegram_id=42, username="testuser", first_name="Test")
        response = self._make_response(admin=admin)
        assert response.admin.telegram_id == 42
        assert response.admin.username == "testuser"
        assert response.admin.first_name == "Test"

    def test_response_has_expires_at_field(self):
        """Backend must return 'expires_at' so the frontend can track token expiry."""
        now = datetime.now(timezone.utc)
        response = self._make_response(expires_at=now)
        assert response.expires_at == now
        data = response.model_dump()
        assert "expires_at" in data

    def test_required_fields_all_present(self):
        """All four fields expected by the frontend LoginResponse interface must be present."""
        response = self._make_response()
        data = response.model_dump()
        required_fields = {"access_token", "token_type", "admin", "expires_at"}
        missing = required_fields - data.keys()
        assert not missing, f"AdminLoginResponse is missing fields: {missing}"

    def test_no_token_field_without_prefix(self):
        """Schema must not expose a bare 'token' field — that would cause a frontend mismatch."""
        response = self._make_response()
        data = response.model_dump()
        assert "token" not in data, "Found bare 'token' key in response; frontend expects 'access_token'"
