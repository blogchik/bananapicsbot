import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    api_base_url: str
    api_timeout_seconds: int


def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    api_base_url = os.getenv("API_BASE_URL", "").strip()
    api_timeout_seconds = int(os.getenv("API_TIMEOUT_SECONDS", "180"))
    if not token:
        raise RuntimeError("BOT_TOKEN is not set in environment")
    if not api_base_url:
        api_base_url = "http://api:8000"
    return Settings(
        bot_token=token,
        api_base_url=api_base_url,
        api_timeout_seconds=api_timeout_seconds,
    )
