"""Admin authentication dependency for FastAPI."""

from fastapi import Header, HTTPException, status

from app.services.admin_auth import verify_admin_token


async def require_admin(
    authorization: str = Header(None, alias="Authorization"),
) -> dict:
    """FastAPI dependency: verify admin JWT and return admin info.

    Raises 401 if token is missing/invalid/expired.
    Raises 403 if user is not an admin.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    token = authorization.split(" ", 1)[1]
    admin_info = verify_admin_token(token)

    if admin_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return admin_info
