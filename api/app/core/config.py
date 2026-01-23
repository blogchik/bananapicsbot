import json
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    # App info
    app_name: str = "Bananapics API"
    app_version: str = "0.1.2"
    api_prefix: str = "/api/v1"
    environment: str = "local"
    debug: bool = False

    # CORS
    cors_origins: str = ""

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_rps: int = 5
    rate_limit_burst: int = 10

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_active_generation_ttl_seconds: int = 900
    redis_cache_ttl_seconds: int = 300

    # Database
    postgres_user: str = "bananapics"
    postgres_password: str = "bananapics"
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "bananapics"
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600

    # Wavespeed API
    wavespeed_api_base_url: str = "https://api.wavespeed.ai"
    wavespeed_api_key: str = ""
    wavespeed_timeout_seconds: int = 180
    wavespeed_min_balance: float = 1.0
    wavespeed_balance_cache_ttl_seconds: int = 60
    wavespeed_balance_alert_ttl_seconds: int = 600
    wavespeed_model_options_cache_ttl_seconds: int = 600
    generation_poll_interval_seconds: int = 3
    generation_poll_max_duration_seconds: int = 300  # 5 minutes max polling

    # Payments
    stars_enabled: bool = True
    stars_min_amount: int = 70
    stars_presets: str = "70,140,210,350,700,1400"
    stars_exchange_numerator: int = 1000
    stars_exchange_denominator: int = 70
    referral_bonus_percent: int = 10
    referral_join_bonus: int = 20

    # Celery
    celery_broker_url: str = ""
    celery_result_backend: str = ""

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or console
    sentry_dsn: str = ""

    # Trial
    trial_generations_limit: int = 3

    # Generations
    max_parallel_generations_per_user: int = 2
    generation_price_markup: int = 0  # Credits to add to base Wavespeed price

    # Admin
    admin_telegram_ids: str = ""

    # Bot token (for Celery broadcast tasks and WebApp auth)
    bot_token: str = ""

    # Telegram API
    telegram_api_base_url: str = "https://api.telegram.org"

    # WebApp
    webapp_url: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> List[str]:
        origins = []

        # Parse from env variable
        value = self.cors_origins.strip()
        if value:
            if value.startswith("["):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        origins.extend(str(item) for item in parsed)
                except json.JSONDecodeError:
                    pass
            else:
                origins.extend(item.strip() for item in value.split(",") if item.strip())

        # Add webapp URL if configured
        if self.webapp_url:
            origins.append(self.webapp_url)

        # Add Telegram domain for WebApp iframe
        if "https://t.me" not in origins:
            origins.append("https://t.me")

        return origins

    @property
    def database_url(self) -> str:
        """Sync database URL for Alembic."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def async_database_url(self) -> str:
        """Async database URL for SQLAlchemy async engine."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def celery_broker(self) -> str:
        """Celery broker URL, defaults to Redis."""
        return self.celery_broker_url or self.redis_url

    @property
    def celery_backend(self) -> str:
        """Celery result backend, defaults to Redis."""
        return self.celery_result_backend or self.redis_url

    @property
    def admin_ids_list(self) -> list[int]:
        """Parse admin IDs from comma-separated string."""
        if not self.admin_telegram_ids:
            return []
        return [int(x.strip()) for x in self.admin_telegram_ids.split(",") if x.strip().isdigit()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
