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
        seedream_v4_t2i_url=settings.wavespeed_seedream_v4_t2i_url,
        seedream_v4_i2i_url=settings.wavespeed_seedream_v4_i2i_url,
        nano_banana_t2i_url=settings.wavespeed_nano_banana_t2i_url,
        nano_banana_i2i_url=settings.wavespeed_nano_banana_i2i_url,
        nano_banana_pro_t2i_url=settings.wavespeed_nano_banana_pro_t2i_url,
        nano_banana_pro_i2i_url=settings.wavespeed_nano_banana_pro_i2i_url,
        timeout_seconds=settings.wavespeed_timeout_seconds,
    )
