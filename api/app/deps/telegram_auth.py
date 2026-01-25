"""
Telegram Mini App authentication dependency.
Validates initData signature and extracts user information.
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


async def get_telegram_user(
    x_telegram_init_data: Annotated[str | None, Header(alias="X-Telegram-Init-Data")] = None,
) -> TelegramUser:
    """
    FastAPI dependency for Telegram authentication.
    Extracts and validates initData from request header.

    Usage:
        @router.get("/protected")
        async def protected_endpoint(user: TelegramUser = Depends(get_telegram_user)):
            return {"user_id": user.id}
    """
    settings = get_settings()

    if not x_telegram_init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Telegram-Init-Data header",
        )

    if not settings.bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bot token not configured",
        )

    try:
        init_data = validate_init_data(
            init_data=x_telegram_init_data,
            bot_token=settings.bot_token,
            max_age_seconds=86400,  # 24 hours
        )
        return init_data.user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
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
