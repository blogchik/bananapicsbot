"""Global error handler middleware."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from core.exceptions import (
    ActiveGenerationError,
    APIConnectionError,
    BotException,
    InsufficientBalanceError,
    RateLimitExceededError,
)
from core.logging import get_logger
from locales import TranslationKey, get_text

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    """
    Global error handler middleware.

    Catches exceptions and sends user-friendly messages.
    Logs errors for debugging.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Process update with error handling."""
        try:
            return await handler(event, data)

        except BotException as e:
            await self._handle_bot_exception(event, data, e)

        except Exception as e:
            await self._handle_unexpected_exception(event, data, e)

    async def _handle_bot_exception(
        self,
        event: TelegramObject,
        data: Dict[str, Any],
        error: BotException,
    ) -> None:
        """Handle known bot exceptions."""
        language = data.get("language", "uz")

        # Map exception to translation key
        if isinstance(error, InsufficientBalanceError):
            message = get_text(TranslationKey.INSUFFICIENT_BALANCE, language)
        elif isinstance(error, ActiveGenerationError):
            message = get_text(TranslationKey.GEN_ACTIVE_EXISTS, language)
        elif isinstance(error, RateLimitExceededError):
            message = get_text(
                TranslationKey.RATE_LIMIT_EXCEEDED,
                language,
                {"seconds": error.retry_after},
            )
        elif isinstance(error, APIConnectionError):
            message = get_text(TranslationKey.ERROR_CONNECTION, language)
        else:
            message = get_text(TranslationKey.ERROR_GENERIC, language)

        await self._send_error_message(event, message)

    async def _handle_unexpected_exception(
        self,
        event: TelegramObject,
        data: Dict[str, Any],
        error: Exception,
    ) -> None:
        """Handle unexpected exceptions."""
        language = data.get("language", "uz")

        logger.error(
            "Unexpected error in handler",
            error=str(error),
            error_type=type(error).__name__,
            exc_info=True,
        )

        message = get_text(TranslationKey.ERROR_GENERIC, language)
        await self._send_error_message(event, message)

    async def _send_error_message(
        self,
        event: TelegramObject,
        message: str,
    ) -> None:
        """Send error message to user."""
        try:
            if isinstance(event, Message):
                await event.answer(message)
            elif isinstance(event, CallbackQuery):
                await event.answer(message, show_alert=True)
        except Exception as e:
            logger.error(
                "Failed to send error message",
                error=str(e),
            )
