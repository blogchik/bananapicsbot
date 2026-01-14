from functools import lru_cache
import json
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bananapics API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    environment: str = "local"

    cors_origins: str = ""

    rate_limit_enabled: bool = True
    rate_limit_rps: int = 5
    rate_limit_burst: int = 10

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_active_generation_ttl_seconds: int = 900

    wavespeed_api_base_url: str = "https://api.wavespeed.ai/api/v3"
    wavespeed_api_key: str = ""
    wavespeed_seedream_v4_t2i_url: str = (
        "https://api.wavespeed.ai/api/v3/bytedance/seedream-v4"
    )
    wavespeed_seedream_v4_i2i_url: str = (
        "https://api.wavespeed.ai/api/v3/bytedance/seedream-v4/edit"
    )
    wavespeed_nano_banana_t2i_url: str = (
        "https://api.wavespeed.ai/api/v3/google/nano-banana/text-to-image"
    )
    wavespeed_nano_banana_i2i_url: str = (
        "https://api.wavespeed.ai/api/v3/google/nano-banana/edit"
    )
    wavespeed_nano_banana_pro_t2i_url: str = (
        "https://api.wavespeed.ai/api/v3/google/nano-banana-pro/text-to-image"
    )
    wavespeed_nano_banana_pro_i2i_url: str = (
        "https://api.wavespeed.ai/api/v3/google/nano-banana-pro/edit"
    )
    wavespeed_timeout_seconds: int = 180

    postgres_user: str = "bananapics"
    postgres_password: str = "bananapics"
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "bananapics"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> List[str]:
        value = self.cors_origins.strip()
        if not value:
            return []
        if value.startswith("["):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
