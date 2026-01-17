from functools import lru_cache

from app.core.config import get_settings
from app.services.wavespeed import WavespeedClient


@lru_cache
def wavespeed_client() -> WavespeedClient:
    settings = get_settings()
    if not settings.wavespeed_api_key:
        raise RuntimeError("WAVESPEED_API_KEY is not set")
    return WavespeedClient(
        api_key=settings.wavespeed_api_key,
        api_base_url=settings.wavespeed_api_base_url,
        timeout_seconds=settings.wavespeed_timeout_seconds,
    )
