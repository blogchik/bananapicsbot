"""Ban check middleware."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User
from core.container import get_container
from core.logging import get_logger

logger = get_logger(__name__)

# Ban messages in different languages
BAN_MESSAGES = {
    "uz": "⛔️ Siz ushbu botdan foydalanishdan bloklangansiz.",
    "ru": "⛔️ Вы заблокированы в этом боте.",
    "en": "⛔️ You have been banned from using this bot.",
}

BAN_REASON_PREFIX = {
    "uz": "Sabab",
    "ru": "Причина",
    "en": "Reason",
}


class BanCheckMiddleware(BaseMiddleware):
    """
    Middleware to check if user is banned.

    If user is banned, sends a message and stops processing.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Check if user is banned before processing."""
        user = self._get_user(event)
        if user is None:
            return await handler(event, data)

        # Check ban status via API
        try:
            container = get_container()
            ban_info = await container.api_client.check_user_ban(user.id)

            if ban_info and ban_info.get("is_banned"):
                # User is banned, send message and stop
                await self._send_ban_message(event, user, ban_info.get("ban_reason"))
                return None
        except Exception as e:
            # If API call fails, allow user to continue (fail open)
            logger.warning(
                "Failed to check ban status",
                user_id=user.id,
                error=str(e),
            )

        return await handler(event, data)

    def _get_user(self, event: TelegramObject) -> User | None:
        """Extract user from event."""
        if isinstance(event, Message):
            return event.from_user
        elif isinstance(event, CallbackQuery):
            return event.from_user
        return None

    async def _send_ban_message(
        self,
        event: TelegramObject,
        user: User,
        reason: str | None,
    ) -> None:
        """Send ban message to user."""
        # Detect user language
        lang = user.language_code or "en"
        if lang not in BAN_MESSAGES:
            lang = "en"

        message = BAN_MESSAGES[lang]
        if reason:
            reason_prefix = BAN_REASON_PREFIX.get(lang, "Reason")
            message += f"\n\n{reason_prefix}: {reason}"

        try:
            if isinstance(event, Message):
                await event.answer(message)
            elif isinstance(event, CallbackQuery):
                await event.answer(message, show_alert=True)
        except Exception as e:
            logger.warning(
                "Failed to send ban message",
                user_id=user.id,
                error=str(e),
            )
