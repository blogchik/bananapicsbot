"""Internationalization middleware."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from core.container import get_container
from core.logging import get_logger
from locales import get_translator

logger = get_logger(__name__)


class I18nMiddleware(BaseMiddleware):
    """
    Internationalization middleware.
    
    Loads user's preferred language and provides translator.
    Falls back to default language if not set.
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
        language = await self._get_user_language(user_id)
        
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
    
    async def _get_user_language(self, user_id: int | None) -> str:
        """Get user's preferred language."""
        if user_id is None:
            return self.default_language
        
        try:
            container = get_container()
            language = await container.redis_client.get_user_language(user_id)
            if language and language in ("uz", "ru", "en"):
                return language
        except Exception as e:
            logger.warning(
                "Failed to get user language",
                user_id=user_id,
                error=str(e),
            )
        
        return self.default_language
