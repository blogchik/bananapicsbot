"""
Telegram Mini App authentication dependency.
Validates initData signature and extracts user information.
Supports dual authentication: WebApp initData OR internal bot API key.
"""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Annotated, Optional
from urllib.parse import parse_qs

from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TelegramUser:
    """Validated Telegram user data."""

    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: bool = False


@dataclass
class TelegramInitData:
    """Parsed and validated Telegram initData."""

    user: TelegramUser
    auth_date: int
    query_id: Optional[str] = None
    hash: str = ""


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> TelegramInitData:
    """
    Validate Telegram Mini App initData signature.

    Args:
        init_data: Raw initData query string from Telegram WebApp
        bot_token: Telegram bot token for HMAC validation
        max_age_seconds: Maximum age of initData in seconds (default: 24 hours)

    Returns:
        TelegramInitData with validated user information

    Raises:
        ValueError: If validation fails
    """
    if not init_data:
        raise ValueError("No initData provided")

    # Parse query string
    params = parse_qs(init_data, keep_blank_values=True)

    # Extract hash
    hash_value = params.get("hash", [""])[0]
    if not hash_value:
        raise ValueError("Missing hash in initData")

    # Build data check string (sorted alphabetically, excluding hash)
    data_check_parts = []
    for key in sorted(params.keys()):
        if key != "hash":
            # parse_qs returns lists, get first value
            value = params[key][0] if params[key] else ""
            data_check_parts.append(f"{key}={value}")

    data_check_string = "\n".join(data_check_parts)

    # Create secret key: HMAC-SHA256(bot_token, "WebAppData")
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

    # Calculate signature: HMAC-SHA256(data_check_string, secret_key)
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    # Compare hashes (constant time comparison)
    if not hmac.compare_digest(calculated_hash, hash_value):
        raise ValueError("Invalid initData signature")

    # Check auth_date freshness
    auth_date_str = params.get("auth_date", [""])[0]
    if not auth_date_str:
        raise ValueError("Missing auth_date in initData")

    try:
        auth_date = int(auth_date_str)
    except ValueError:
        raise ValueError("Invalid auth_date format")

    current_time = int(time.time())
    if current_time - auth_date > max_age_seconds:
        raise ValueError(f"initData expired (age: {current_time - auth_date}s, max: {max_age_seconds}s)")

    # Parse user data
    user_json = params.get("user", [""])[0]
    if not user_json:
        raise ValueError("Missing user data in initData")

    try:
        user_data = json.loads(user_json)
    except json.JSONDecodeError:
        raise ValueError("Invalid user data format")

    # Build TelegramUser
    user = TelegramUser(
        id=user_data.get("id"),
        first_name=user_data.get("first_name", ""),
        last_name=user_data.get("last_name"),
        username=user_data.get("username"),
        language_code=user_data.get("language_code"),
        is_premium=user_data.get("is_premium", False),
    )

    if not user.id:
        raise ValueError("Missing user ID in initData")

    # Build and return validated initData
    return TelegramInitData(
        user=user,
        auth_date=auth_date,
        query_id=params.get("query_id", [""])[0] or None,
        hash=hash_value,
    )


def generate_internal_api_key(bot_token: str) -> str:
    """
    Generate internal API key from bot token.
    This key is used for bot-to-API authentication.
    """
    secret = hmac.new(b"InternalApiKey", bot_token.encode(), hashlib.sha256).hexdigest()
    return secret


def validate_internal_api_key(api_key: str, bot_token: str) -> bool:
    """
    Validate internal API key.
    Returns True if the key matches the expected key derived from bot token.
    """
    expected_key = generate_internal_api_key(bot_token)
    return hmac.compare_digest(api_key, expected_key)


async def get_telegram_user(
    x_telegram_init_data: Annotated[str | None, Header(alias="X-Telegram-Init-Data")] = None,
    x_internal_api_key: Annotated[str | None, Header(alias="X-Internal-Api-Key")] = None,
    x_telegram_user_id: Annotated[str | None, Header(alias="X-Telegram-User-Id")] = None,
) -> TelegramUser:
    """
    FastAPI dependency for Telegram authentication.
    Supports two authentication methods:
    1. WebApp: X-Telegram-Init-Data header with Telegram initData
    2. Internal Bot: X-Internal-Api-Key + X-Telegram-User-Id headers

    Usage:
        @router.get("/protected")
        async def protected_endpoint(user: TelegramUser = Depends(get_telegram_user)):
            return {"user_id": user.id}
    """
    settings = get_settings()

    if not settings.bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bot token not configured",
        )

    # Method 1: WebApp authentication via initData
    if x_telegram_init_data:
        try:
            init_data = validate_init_data(
                init_data=x_telegram_init_data,
                bot_token=settings.bot_token,
                max_age_seconds=86400,  # 24 hours
            )
            logger.debug("WebApp auth successful", user_id=init_data.user.id)
            return init_data.user
        except ValueError as e:
            logger.warning("WebApp auth failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
            )

    # Method 2: Internal bot authentication via API key
    if x_internal_api_key and x_telegram_user_id:
        if not validate_internal_api_key(x_internal_api_key, settings.bot_token):
            logger.warning("Internal API key validation failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid internal API key",
            )

        try:
            user_id = int(x_telegram_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid telegram user ID format",
            )

        logger.debug("Internal bot auth successful", user_id=user_id)
        # Return a minimal TelegramUser for internal bot requests
        return TelegramUser(
            id=user_id,
            first_name="Bot User",  # Placeholder, not used for authorization
        )

    # No valid authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication: provide X-Telegram-Init-Data or X-Internal-Api-Key with X-Telegram-User-Id",
    )


async def get_optional_telegram_user(
    x_telegram_init_data: Annotated[str | None, Header(alias="X-Telegram-Init-Data")] = None,
) -> Optional[TelegramUser]:
    """
    FastAPI dependency for optional Telegram authentication.
    Returns None if no initData provided, otherwise validates and returns user.

    Usage:
        @router.get("/public")
        async def public_endpoint(user: Optional[TelegramUser] = Depends(get_optional_telegram_user)):
            if user:
                return {"user_id": user.id}
            return {"message": "Anonymous access"}
    """
    if not x_telegram_init_data:
        return None

    try:
        return await get_telegram_user(x_telegram_init_data)
    except HTTPException:
        return None


# Type aliases for cleaner dependency injection
TelegramUserDep = Annotated[TelegramUser, Depends(get_telegram_user)]
OptionalTelegramUserDep = Annotated[Optional[TelegramUser], Depends(get_optional_telegram_user)]
