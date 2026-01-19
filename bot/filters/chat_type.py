"""Chat type filters."""

from aiogram.enums import ChatType
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject


class PrivateChatFilter(BaseFilter):
    """Filter for private chats only."""

    async def __call__(self, event: TelegramObject) -> bool:
        """Check if message is from private chat."""
        chat = self._get_chat(event)
        if chat is None:
            return False
        return chat.type == ChatType.PRIVATE

    def _get_chat(self, event: TelegramObject):
        """Extract chat from event."""
        if isinstance(event, Message):
            return event.chat
        elif isinstance(event, CallbackQuery):
            return event.message.chat if event.message else None
        return None
