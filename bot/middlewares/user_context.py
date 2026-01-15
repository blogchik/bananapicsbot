"""User context middleware."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, User

from core.container import get_container
from core.logging import get_logger

logger = get_logger(__name__)


class UserContextMiddleware(BaseMiddleware):
    """
    User context middleware.
    
    Syncs user with API and provides user context to handlers.
    """
    
    def __init__(self, sync_on_every_request: bool = False) -> None:
        self.sync_on_every_request = sync_on_every_request
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Process update with user context."""
        user = self._get_user(event)
        if user is None:
            return await handler(event, data)
        
        # Add user to data
        data["user"] = user
        data["user_id"] = user.id
        
        # Check if user is admin
        container = get_container()
        data["is_admin"] = user.id in container.settings.admin_ids
        
        # Optionally sync user on every request
        if self.sync_on_every_request:
            await self._sync_user(user.id)
        
        return await handler(event, data)
    
    def _get_user(self, event: TelegramObject) -> User | None:
        """Extract user from event."""
        if isinstance(event, Message):
            return event.from_user
        elif isinstance(event, CallbackQuery):
            return event.from_user
        return None
    
    async def _sync_user(self, user_id: int) -> None:
        """Sync user with API."""
        try:
            container = get_container()
            await container.api_client.sync_user(user_id)
        except Exception as e:
            logger.warning(
                "Failed to sync user",
                user_id=user_id,
                error=str(e),
            )
