"""Admin filter."""

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject
from core.container import get_container


class AdminFilter(BaseFilter):
    """Filter for admin users."""

    async def __call__(self, event: TelegramObject) -> bool:
        """Check if user is admin."""
        user_id = self._get_user_id(event)
        if user_id is None:
            return False

        container = get_container()
        return user_id in container.settings.admin_ids

    def _get_user_id(self, event: TelegramObject) -> int | None:
        """Extract user ID from event."""
        if isinstance(event, Message):
            return event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            return event.from_user.id
        return None


# Shorthand for AdminFilter
IsAdminFilter = AdminFilter
