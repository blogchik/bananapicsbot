"""Rate limiting middleware."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from core.container import get_container
from core.exceptions import RateLimitExceededError
from core.logging import get_logger

logger = get_logger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """
    Rate limiting middleware using Redis.
    
    Features:
    - Separate limits for messages and callbacks
    - Per-user rate limiting
    - Sliding window algorithm
    """
    
    def __init__(
        self,
        message_limit: int = 30,
        callback_limit: int = 60,
        window_seconds: int = 60,
    ) -> None:
        self.message_limit = message_limit
        self.callback_limit = callback_limit
        self.window_seconds = window_seconds
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Process update with rate limiting."""
        user_id = self._get_user_id(event)
        if user_id is None:
            return await handler(event, data)
        
        # Determine rate limit based on event type
        if isinstance(event, Message):
            limit = self.message_limit
            key_prefix = "msg"
        elif isinstance(event, CallbackQuery):
            limit = self.callback_limit
            key_prefix = "cb"
        else:
            return await handler(event, data)
        
        # Check rate limit
        is_allowed, remaining = await self._check_rate_limit(
            user_id,
            key_prefix,
            limit,
        )
        
        if not is_allowed:
            ttl = await self._get_retry_after(user_id, key_prefix)
            logger.warning(
                "Rate limit exceeded",
                user_id=user_id,
                event_type=key_prefix,
                retry_after=ttl,
            )
            raise RateLimitExceededError(retry_after=ttl)
        
        return await handler(event, data)
    
    def _get_user_id(self, event: TelegramObject) -> int | None:
        """Extract user ID from event."""
        if isinstance(event, Message):
            return event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            return event.from_user.id
        return None
    
    async def _check_rate_limit(
        self,
        user_id: int,
        key_prefix: str,
        limit: int,
    ) -> tuple[bool, int]:
        """Check if user is within rate limit."""
        try:
            container = get_container()
            key = f"throttle:{key_prefix}:{user_id}"
            return await container.redis_client.check_rate_limit(
                key,
                limit,
                self.window_seconds,
            )
        except Exception as e:
            logger.error(
                "Rate limit check failed",
                error=str(e),
            )
            # Allow request if rate limiting fails
            return True, limit
    
    async def _get_retry_after(
        self,
        user_id: int,
        key_prefix: str,
    ) -> int:
        """Get seconds until rate limit resets."""
        try:
            container = get_container()
            key = f"throttle:{key_prefix}:{user_id}"
            return await container.redis_client.get_rate_limit_ttl(key)
        except Exception:
            return self.window_seconds
