"""Bot constants and configuration values."""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class BotConstants:
    """Immutable bot constants."""

    # Telegram limits
    MAX_MESSAGE_LENGTH: Final[int] = 4096
    MAX_CAPTION_LENGTH: Final[int] = 1024
    MAX_CALLBACK_DATA_LENGTH: Final[int] = 64
    MAX_INLINE_BUTTONS_PER_ROW: Final[int] = 8

    # Generation limits
    MAX_REFERENCE_IMAGES: Final[int] = 10
    MAX_PROMPT_LENGTH: Final[int] = 2000

    # Polling settings
    POLL_INTERVAL_SECONDS: Final[float] = 2.0
    GENERATION_TIMEOUT_SECONDS: Final[int] = 600

    # Retry settings
    SEND_RETRY_ATTEMPTS: Final[int] = 3
    SEND_RETRY_DELAY_SECONDS: Final[float] = 1.5

    # Media group settings
    MEDIA_GROUP_DELAY_SECONDS: Final[float] = 1.0

    # Cache TTL
    MODELS_CACHE_TTL_SECONDS: Final[int] = 300
    USER_CACHE_TTL_SECONDS: Final[int] = 60

    # Allowed image extensions
    ALLOWED_IMAGE_EXTENSIONS: Final[tuple[str, ...]] = (
        ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"
    )

    # Queue statuses
    QUEUE_STATUSES: Final[frozenset[str]] = frozenset({
        "pending", "configuring", "queued", "created"
    })

    # Tools pricing
    WATERMARK_REMOVE_COST: Final[int] = 12
    UPSCALE_COST: Final[int] = 60
    DENOISE_COST: Final[int] = 20
    RESTORE_COST: Final[int] = 20
    ENHANCE_COST: Final[int] = 30


# Callback data prefixes
class CallbackPrefix:
    """Callback data prefixes for routing."""

    MENU: Final[str] = "menu"
    GENERATION: Final[str] = "gen"
    TOPUP: Final[str] = "topup"
    ADMIN: Final[str] = "admin"
    SETTINGS: Final[str] = "settings"
    LANGUAGE: Final[str] = "lang"
    REFERRAL: Final[str] = "ref"


# Bot commands
class BotCommands:
    """Bot command names."""

    START: Final[str] = "start"
    HELP: Final[str] = "help"
    PROFILE: Final[str] = "profile"
    SETTINGS: Final[str] = "settings"
    REFERRAL: Final[str] = "referral"
    ADMIN: Final[str] = "admin"
    CANCEL: Final[str] = "cancel"
