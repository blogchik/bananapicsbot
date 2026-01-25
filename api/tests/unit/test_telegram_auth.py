"""Tests for Telegram Mini App authentication."""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from app.deps.telegram_auth import (
    TelegramInitData,
    TelegramUser,
    validate_init_data,
)


def create_init_data(
    user_id: int = 123456789,
    first_name: str = "Test",
    last_name: str = "User",
    username: str = "testuser",
    bot_token: str = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
    auth_date: int | None = None,
) -> str:
    """Create valid initData string for testing."""
    if auth_date is None:
        auth_date = int(time.time())

    user_data = {
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "language_code": "en",
    }

    params = {
        "user": json.dumps(user_data, separators=(",", ":")),
        "auth_date": str(auth_date),
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
    }

    # Sort parameters alphabetically
    data_check_parts = [f"{k}={v}" for k, v in sorted(params.items())]
    data_check_string = "\n".join(data_check_parts)

    # Create secret key
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

    # Calculate hash
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    params["hash"] = hash_value
    return urlencode(params)


class TestValidateInitData:
    """Test cases for validate_init_data function."""

    BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

    def test_valid_init_data(self):
        """Test validation with valid initData."""
        init_data = create_init_data(bot_token=self.BOT_TOKEN)

        result = validate_init_data(init_data, self.BOT_TOKEN)

        assert isinstance(result, TelegramInitData)
        assert result.user.id == 123456789
        assert result.user.first_name == "Test"
        assert result.user.last_name == "User"
        assert result.user.username == "testuser"
        assert result.query_id == "AAHdF6IQAAAAAN0XohDhrOrc"

    def test_empty_init_data(self):
        """Test validation with empty initData."""
        with pytest.raises(ValueError, match="No initData provided"):
            validate_init_data("", self.BOT_TOKEN)

    def test_missing_hash(self):
        """Test validation with missing hash."""
        init_data = "user=%7B%22id%22%3A123%7D&auth_date=1234567890"

        with pytest.raises(ValueError, match="Missing hash"):
            validate_init_data(init_data, self.BOT_TOKEN)

    def test_invalid_signature(self):
        """Test validation with invalid signature."""
        init_data = create_init_data(bot_token=self.BOT_TOKEN)
        # Tamper with the data
        init_data = init_data.replace("Test", "Hacker")

        with pytest.raises(ValueError, match="Invalid initData signature"):
            validate_init_data(init_data, self.BOT_TOKEN)

    def test_wrong_bot_token(self):
        """Test validation with wrong bot token."""
        init_data = create_init_data(bot_token=self.BOT_TOKEN)

        with pytest.raises(ValueError, match="Invalid initData signature"):
            validate_init_data(init_data, "wrong:token")

    def test_expired_init_data(self):
        """Test validation with expired initData."""
        # Create initData from 25 hours ago
        old_auth_date = int(time.time()) - (25 * 60 * 60)
        init_data = create_init_data(bot_token=self.BOT_TOKEN, auth_date=old_auth_date)

        with pytest.raises(ValueError, match="initData expired"):
            validate_init_data(init_data, self.BOT_TOKEN, max_age_seconds=86400)

    def test_custom_max_age(self):
        """Test validation with custom max age."""
        # Create initData from 2 hours ago
        old_auth_date = int(time.time()) - (2 * 60 * 60)
        init_data = create_init_data(bot_token=self.BOT_TOKEN, auth_date=old_auth_date)

        # Should fail with 1 hour max age
        with pytest.raises(ValueError, match="initData expired"):
            validate_init_data(init_data, self.BOT_TOKEN, max_age_seconds=3600)

        # Should pass with 3 hour max age
        result = validate_init_data(init_data, self.BOT_TOKEN, max_age_seconds=10800)
        assert result.user.id == 123456789

    def test_missing_user_data(self):
        """Test validation with missing user data."""
        auth_date = int(time.time())
        params = {
            "auth_date": str(auth_date),
            "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        }

        # Create hash
        data_check_parts = [f"{k}={v}" for k, v in sorted(params.items())]
        data_check_string = "\n".join(data_check_parts)
        secret_key = hmac.new(b"WebAppData", self.BOT_TOKEN.encode(), hashlib.sha256).digest()
        hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        params["hash"] = hash_value

        init_data = urlencode(params)

        with pytest.raises(ValueError, match="Missing user data"):
            validate_init_data(init_data, self.BOT_TOKEN)


class TestTelegramUser:
    """Test cases for TelegramUser dataclass."""

    def test_user_creation(self):
        """Test TelegramUser creation with all fields."""
        user = TelegramUser(
            id=123456789,
            first_name="Test",
            last_name="User",
            username="testuser",
            language_code="en",
            is_premium=True,
        )

        assert user.id == 123456789
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.username == "testuser"
        assert user.language_code == "en"
        assert user.is_premium is True

    def test_user_creation_minimal(self):
        """Test TelegramUser creation with minimal fields."""
        user = TelegramUser(id=123456789, first_name="Test")

        assert user.id == 123456789
        assert user.first_name == "Test"
        assert user.last_name is None
        assert user.username is None
        assert user.language_code is None
        assert user.is_premium is False
