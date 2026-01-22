"""Internationalization middleware."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from core.container import get_container
from core.logging import get_logger
from locales import get_translator

logger = get_logger(__name__)

# Supported languages
SUPPORTED_LANGUAGES = {"uz", "ru", "en"}


class I18nMiddleware(BaseMiddleware):
    """
    Internationalization middleware.

    Loads user's preferred language and provides translator.
    Falls back to Telegram language, then to default language.
    """

    def __init__(self, default_language: str = "uz") -> None:
        self.default_language = default_language

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Process update with language context."""
        user_id = self._get_user_id(event)
        telegram_language = self._get_telegram_language(event)
        language = await self._get_user_language(user_id, telegram_language)

        # Debug log for language detection
        from core.logging import get_logger

        logger = get_logger(__name__)
        logger.info("Language detected", user_id=user_id, telegram_lang=telegram_language, final_lang=language)

        # Add language and translator to handler data
        data["language"] = language
        data["_"] = get_translator(language)

        return await handler(event, data)

    def _get_user_id(self, event: TelegramObject) -> int | None:
        """Extract user ID from event."""
        if isinstance(event, Message):
            return event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            return event.from_user.id
        return None

    def _get_telegram_language(self, event: TelegramObject) -> str | None:
        """Extract Telegram language code from event."""
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if user and user.language_code:
            # Telegram language codes can be like "en", "ru", "uz", "en-US", etc.
            lang = user.language_code.split("-")[0].lower()
            if lang in SUPPORTED_LANGUAGES:
                return lang
        return None

    async def _get_user_language(
        self,
        user_id: int | None,
        telegram_language: str | None,
    ) -> str:
        """Get user's preferred language."""
        if user_id is None:
            return telegram_language or self.default_language

        try:
            container = get_container()
            # First check if user has explicitly set language in Redis
            language = await container.redis_client.get_user_language(user_id)
            if language and language in SUPPORTED_LANGUAGES:
                return language

            # If no explicit language set, use Telegram language and save it
            if telegram_language:
                await container.redis_client.set_user_language(user_id, telegram_language)
                return telegram_language

        except Exception as e:
            logger.warning(
                "Failed to get user language",
                user_id=user_id,
                error=str(e),
            )

        return self.default_language
