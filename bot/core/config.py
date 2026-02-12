"""Application configuration using Pydantic settings."""

from functools import lru_cache
from typing import Literal, Union

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Bot settings
    bot_token: SecretStr = Field(..., description="Telegram bot token")
    bot_mode: Literal["polling", "webhook"] = Field(
        default="polling",
        description="Bot running mode",
    )

    # Webhook settings (optional, for webhook mode)
    webhook_url: str = Field(default="", description="Webhook URL")
    webhook_base_url: str = Field(default="", description="Webhook base URL")
    webhook_path: str = Field(default="/webhook", description="Webhook path")
    webhook_secret: str = Field(default="", description="Webhook secret token")
    webhook_host: str = Field(default="0.0.0.0", description="Webhook server host")
    webhook_port: int = Field(default=8443, description="Webhook server port")

    @property
    def use_webhook(self) -> bool:
        """Check if webhook mode is enabled."""
        return self.bot_mode == "webhook"

    # API settings
    api_base_url: str = Field(default="http://api:8000", description="API base URL")
    api_timeout_seconds: int = Field(default=180, description="API request timeout")

    # Redis settings
    redis_url: str = Field(default="redis://redis:6379/0", description="Redis URL")
    redis_prefix: str = Field(default="bot", description="Redis key prefix")

    # Payment settings
    payment_provider_token: str = Field(default="", description="Payment provider token")

    # Admin settings - use str to avoid JSON parsing, then convert via validator
    admin_ids: Union[str, list[int]] = Field(default="", description="Admin user IDs (comma-separated)")

    # Rate limiting
    rate_limit_messages: int = Field(default=30, description="Messages per minute")
    rate_limit_callbacks: int = Field(default=60, description="Callbacks per minute")
    rate_limit_period: int = Field(default=60, description="Rate limit period in seconds")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    sentry_dsn: str = Field(default="", description="Sentry DSN for error tracking")

    # Localization
    default_language: str = Field(default="uz", description="Default language code")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        if isinstance(v, int):
            return [v]
        if isinstance(v, list):
            return [int(x) for x in v]
        return []

    @property
    def admin_ids_list(self) -> list[int]:
        """Get admin IDs as a list."""
        if isinstance(self.admin_ids, list):
            return self.admin_ids
        return []

    @field_validator("bot_token", mode="before")
    @classmethod
    def validate_bot_token(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("BOT_TOKEN is required")
            if ":" not in v:
                raise ValueError("Invalid bot token format")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
