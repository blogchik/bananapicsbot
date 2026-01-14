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


@lru_cache
def get_settings() -> Settings:
    return Settings()
