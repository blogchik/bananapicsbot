"""Admin authentication service using Telegram Login Widget + JWT."""

import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from app.core.config import get_settings
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24


def verify_telegram_login(data: dict, bot_token: str) -> bool:
    """Verify Telegram Login Widget data using HMAC-SHA256.

    See: https://core.telegram.org/widgets/login#checking-authorization
    """
    check_hash = data.get("hash")
    if not check_hash:
        return False

    # Build data-check-string: sort fields alphabetically, join with newline
    filtered = {k: v for k, v in data.items() if k != "hash" and v is not None}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(filtered.items()))

    # Secret key = SHA256(bot_token)
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    # HMAC-SHA256 of the data-check-string
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, check_hash):
        logger.warning("Telegram login hash mismatch")
        return False

    # Check auth_date is not too old (1 hour)
    auth_date = int(data.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        logger.warning("Telegram login auth_date too old", auth_date=auth_date)
        return False

    return True


def create_admin_token(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
) -> tuple[str, datetime]:
    """Create JWT token for admin session."""
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)

    payload = {
        "sub": str(telegram_id),
        "username": username,
        "first_name": first_name,
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
        "type": "admin",
    }

    token = jwt.encode(payload, settings.admin_jwt_secret, algorithm=ALGORITHM)
    return token, expires_at


def verify_admin_token(token: str) -> Optional[dict]:
    """Verify and decode admin JWT token. Returns payload or None."""
    settings = get_settings()

    try:
        payload = jwt.decode(token, settings.admin_jwt_secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.debug("Admin token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid admin token", error=str(e))
        return None

    if payload.get("type") != "admin":
        logger.warning("Token type is not admin")
        return None

    telegram_id = int(payload["sub"])
    if telegram_id not in settings.admin_ids_list:
        logger.warning("Token holder is not an admin", telegram_id=telegram_id)
        return None

    return {
        "telegram_id": telegram_id,
        "username": payload.get("username"),
        "first_name": payload.get("first_name"),
    }
