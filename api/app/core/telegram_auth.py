"""Telegram WebApp initData validation.

See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qs, unquote

from app.core.config import get_settings
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


def validate_init_data(
    init_data: str,
    bot_token: str | None = None,
    max_age_hours: int = 24,
) -> dict[str, Any] | None:
    """
    Validate Telegram WebApp initData.

    Args:
        init_data: Raw initData string from Telegram WebApp
        bot_token: Bot token for HMAC validation (uses settings if not provided)
        max_age_hours: Maximum age of auth_date in hours (default 24)

    Returns:
        Parsed user data dict if valid, None if invalid
    """
    if not init_data:
        logger.warning("Empty initData provided")
        return None

    # Use settings if bot_token not provided
    if bot_token is None:
        settings = get_settings()
        bot_token = settings.bot_token

    if not bot_token:
        logger.error("No bot token available for initData validation")
        return None

    try:
        # Parse query string
        parsed = parse_qs(init_data)

        # Extract hash
        hash_list = parsed.pop("hash", None)
        if not hash_list:
            logger.warning("No hash in initData")
            return None
        received_hash = hash_list[0]

        # Check auth_date is not too old
        auth_date_list = parsed.get("auth_date")
        if auth_date_list:
            try:
                auth_timestamp = int(auth_date_list[0])
                auth_time = datetime.fromtimestamp(auth_timestamp, tz=timezone.utc)
                now = datetime.now(tz=timezone.utc)

                if now - auth_time > timedelta(hours=max_age_hours):
                    logger.warning(
                        "initData too old",
                        extra={
                            "auth_time": auth_time.isoformat(),
                            "max_age_hours": max_age_hours,
                        },
                    )
                    return None
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid auth_date: {e}")
                return None

        # Create data-check-string
        # Sort by key and format as "key=value" with newlines
        data_check_items = []
        for key in sorted(parsed.keys()):
            value = parsed[key][0]
            data_check_items.append(f"{key}={value}")
        data_check_string = "\n".join(data_check_items)

        # Create secret key: HMAC-SHA256(bot_token, "WebAppData")
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        # Calculate hash: HMAC-SHA256(data_check_string, secret_key)
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        # Compare hashes
        if not hmac.compare_digest(calculated_hash, received_hash):
            logger.warning("initData hash mismatch")
            return None

        # Parse user data
        user_str = parsed.get("user", [None])[0]
        user_data = None
        if user_str:
            try:
                user_data = json.loads(unquote(user_str))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse user data: {e}")

        return {
            "user": user_data,
            "auth_date": auth_date_list[0] if auth_date_list else None,
            "query_id": parsed.get("query_id", [None])[0],
            "chat_type": parsed.get("chat_type", [None])[0],
            "chat_instance": parsed.get("chat_instance", [None])[0],
            "start_param": parsed.get("start_param", [None])[0],
        }

    except Exception as e:
        logger.exception(f"Error validating initData: {e}")
        return None


def get_telegram_user_from_init_data(init_data: str) -> dict[str, Any] | None:
    """
    Extract and validate Telegram user from initData.

    Args:
        init_data: Raw initData string from Telegram WebApp

    Returns:
        User dict with id, first_name, etc. if valid, None if invalid
    """
    result = validate_init_data(init_data)
    if result is None:
        return None

    user = result.get("user")
    if not user or not isinstance(user, dict) or "id" not in user:
        logger.warning("No valid user in initData")
        return None

    return user
