"""Telegram API service for fetching user profiles."""

import asyncio
from typing import Any

import httpx

from app.core.config import get_settings
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Cache for user profiles (telegram_id -> profile data)
_user_cache: dict[int, dict[str, Any]] = {}
_cache_ttl: dict[int, float] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


async def get_telegram_user_profile(telegram_id: int) -> dict[str, Any]:
    """
    Fetch user profile from Telegram API.
    Returns cached data if available and not expired.
    """
    import time

    now = time.time()

    # Check cache
    if telegram_id in _user_cache and telegram_id in _cache_ttl:
        if now - _cache_ttl[telegram_id] < CACHE_TTL_SECONDS:
            return _user_cache[telegram_id]

    # Fetch from Telegram API
    settings = get_settings()
    if not settings.bot_token:
        return _empty_profile(telegram_id)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{settings.telegram_api_base_url}/bot{settings.bot_token}/getChat"
            response = await client.post(url, json={"chat_id": telegram_id})

            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and data.get("result"):
                    result = data["result"]
                    profile = {
                        "telegram_id": telegram_id,
                        "username": result.get("username"),
                        "first_name": result.get("first_name"),
                        "last_name": result.get("last_name"),
                        "photo_url": None,  # Will be fetched separately if needed
                    }

                    # Try to get profile photo
                    photo_url = await _get_profile_photo(client, settings, telegram_id)
                    if photo_url:
                        profile["photo_url"] = photo_url

                    # Cache the result
                    _user_cache[telegram_id] = profile
                    _cache_ttl[telegram_id] = now
                    return profile

    except Exception as e:
        logger.warning("Failed to fetch Telegram profile", telegram_id=telegram_id, error=str(e))

    return _empty_profile(telegram_id)


async def _get_profile_photo(client: httpx.AsyncClient, settings: Any, telegram_id: int) -> str | None:
    """Get user profile photo URL."""
    try:
        url = f"{settings.telegram_api_base_url}/bot{settings.bot_token}/getUserProfilePhotos"
        response = await client.post(url, json={"user_id": telegram_id, "limit": 1})

        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("result", {}).get("photos"):
                photos = data["result"]["photos"]
                if photos and photos[0]:
                    # Get the largest photo
                    photo = photos[0][-1] if photos[0] else None
                    if photo:
                        file_id = photo.get("file_id")
                        if file_id:
                            # Get file path
                            file_url = f"{settings.telegram_api_base_url}/bot{settings.bot_token}/getFile"
                            file_response = await client.post(file_url, json={"file_id": file_id})
                            if file_response.status_code == 200:
                                file_data = file_response.json()
                                if file_data.get("ok") and file_data.get("result", {}).get("file_path"):
                                    file_path = file_data["result"]["file_path"]
                                    return f"https://api.telegram.org/file/bot{settings.bot_token}/{file_path}"
    except Exception as e:
        logger.debug("Failed to get profile photo", telegram_id=telegram_id, error=str(e))

    return None


def _empty_profile(telegram_id: int) -> dict[str, Any]:
    """Return empty profile for a user."""
    return {
        "telegram_id": telegram_id,
        "username": None,
        "first_name": None,
        "last_name": None,
        "photo_url": None,
    }


async def get_telegram_user_profiles_batch(
    telegram_ids: list[int],
) -> dict[int, dict[str, Any]]:
    """Fetch multiple user profiles in parallel."""
    tasks = [get_telegram_user_profile(tid) for tid in telegram_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    profiles = {}
    for tid, result in zip(telegram_ids, results):
        if isinstance(result, Exception):
            profiles[tid] = _empty_profile(tid)
        else:
            profiles[tid] = result

    return profiles


def clear_user_cache(telegram_id: int | None = None) -> None:
    """Clear user profile cache."""
    if telegram_id:
        _user_cache.pop(telegram_id, None)
        _cache_ttl.pop(telegram_id, None)
    else:
        _user_cache.clear()
        _cache_ttl.clear()
