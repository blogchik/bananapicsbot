from functools import lru_cache

from app.core.config import Settings, get_settings


@lru_cache
def settings_dep() -> Settings:
    return get_settings()
