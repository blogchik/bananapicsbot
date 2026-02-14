"""Admin authentication dependency for FastAPI.

Supports dual authentication:
1. JWT Bearer token (web admin panel)
2. Internal API key (bot-to-API calls)
"""

from typing import Annotated

from fastapi import Header, HTTPException, status

from app.core.config import get_settings
from app.deps.telegram_auth import validate_internal_api_key
from app.services.admin_auth import verify_admin_token


async def require_admin(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_internal_api_key: Annotated[str | None, Header(alias="X-Internal-Api-Key")] = None,
) -> dict:
    """FastAPI dependency: verify admin access via JWT or internal API key.

    Method 1: Authorization: Bearer <JWT> (web admin panel)
    Method 2: X-Internal-Api-Key (bot-to-API, bot already validates admin access)

    Raises 401 if no valid auth provided.
    """
    # Method 1: JWT Bearer token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        admin_info = verify_admin_token(token)

        if admin_info is not None:
            return admin_info

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Method 2: Internal API key (bot-to-API calls)
    if x_internal_api_key:
        settings = get_settings()
        if settings.bot_token and validate_internal_api_key(x_internal_api_key, settings.bot_token):
            return {
                "telegram_id": 0,
                "username": "bot",
                "first_name": "Bot Internal",
            }

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication",
    )
