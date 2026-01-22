"""Logging middleware for request tracking."""

import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update
from core.logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware for logging all incoming updates.

    Logs:
    - Update type and ID
    - User information
    - Processing time
    - Errors
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Process update with logging."""
        start_time = time.monotonic()

        # Extract update info
        update_type = "unknown"
        user_id = None
        chat_id = None

        if isinstance(event, Update):
            if event.message:
                update_type = "message"
                user_id = event.message.from_user.id if event.message.from_user else None
                chat_id = event.message.chat.id
            elif event.callback_query:
                update_type = "callback_query"
                user_id = event.callback_query.from_user.id
                chat_id = event.callback_query.message.chat.id if event.callback_query.message else None
        elif isinstance(event, Message):
            update_type = "message"
            user_id = event.from_user.id if event.from_user else None
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery):
            update_type = "callback_query"
            user_id = event.from_user.id
            chat_id = event.message.chat.id if event.message else None

        logger.debug(
            "Incoming update",
            update_type=update_type,
            user_id=user_id,
            chat_id=chat_id,
        )

        try:
            result = await handler(event, data)

            duration_ms = (time.monotonic() - start_time) * 1000
            logger.info(
                "Update processed",
                update_type=update_type,
                user_id=user_id,
                duration_ms=round(duration_ms, 2),
            )

            return result

        except Exception as e:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.error(
                "Update processing failed",
                update_type=update_type,
                user_id=user_id,
                error=str(e),
                duration_ms=round(duration_ms, 2),
                exc_info=True,
            )
            raise
