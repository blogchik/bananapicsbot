"""Dependency injection container."""

from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import BaseStorage

from .config import Settings, get_settings

if TYPE_CHECKING:
    from infrastructure.api_client import ApiClient
    from infrastructure.redis_client import RedisClient


class Container:
    """
    Dependency injection container.
    
    Holds all shared instances and provides access to them.
    Implements lazy initialization for better startup performance.
    """

    _instance: "Container | None" = None

    def __init__(self) -> None:
        self._settings: Settings | None = None
        self._bot: Bot | None = None
        self._dispatcher: Dispatcher | None = None
        self._storage: BaseStorage | None = None
        self._api_client: "ApiClient | None" = None
        self._redis_client: "RedisClient | None" = None

    @classmethod
    def get_instance(cls) -> "Container":
        """Get singleton container instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset container instance (for testing)."""
        cls._instance = None

    @property
    def settings(self) -> Settings:
        """Get settings instance."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    @property
    def bot(self) -> Bot:
        """Get bot instance."""
        if self._bot is None:
            raise RuntimeError("Bot not initialized. Call set_bot() first.")
        return self._bot

    def set_bot(self, bot: Bot) -> None:
        """Set bot instance."""
        self._bot = bot

    @property
    def dispatcher(self) -> Dispatcher:
        """Get dispatcher instance."""
        if self._dispatcher is None:
            raise RuntimeError("Dispatcher not initialized. Call set_dispatcher() first.")
        return self._dispatcher

    def set_dispatcher(self, dispatcher: Dispatcher) -> None:
        """Set dispatcher instance."""
        self._dispatcher = dispatcher

    @property
    def storage(self) -> BaseStorage:
        """Get FSM storage instance."""
        if self._storage is None:
            raise RuntimeError("Storage not initialized. Call set_storage() first.")
        return self._storage

    def set_storage(self, storage: BaseStorage) -> None:
        """Set FSM storage instance."""
        self._storage = storage

    @property
    def api_client(self) -> "ApiClient":
        """Get API client instance."""
        if self._api_client is None:
            from infrastructure.api_client import ApiClient
            self._api_client = ApiClient(
                base_url=self.settings.api_base_url,
                timeout_seconds=self.settings.api_timeout_seconds,
            )
        return self._api_client

    @property
    def redis_client(self) -> "RedisClient":
        """Get Redis client instance."""
        if self._redis_client is None:
            from infrastructure.redis_client import RedisClient
            self._redis_client = RedisClient(
                url=self.settings.redis_url,
                prefix=self.settings.redis_prefix,
            )
        return self._redis_client

    async def close(self) -> None:
        """Close all connections."""
        if self._api_client is not None:
            await self._api_client.close()
            self._api_client = None

        if self._redis_client is not None:
            await self._redis_client.close()
            self._redis_client = None

        if self._bot is not None:
            await self._bot.session.close()
            self._bot = None


def get_container() -> Container:
    """Get container instance shortcut."""
    return Container.get_instance()
