"""Dependency Injection Container using dependency-injector."""

from typing import Optional

from dependency_injector import containers, providers
from redis.asyncio import Redis

from app.core.config import get_settings
from app.infrastructure.cache.memory import MemoryCache
from app.infrastructure.cache.multi_layer import MultiLayerCache
from app.infrastructure.cache.redis import RedisCache
from app.infrastructure.database.session import Database


class Container(containers.DeclarativeContainer):
    """Dependency Injection Container."""

    wiring_config = containers.WiringConfiguration(
        packages=[
            "app.api",
            "app.services",
        ]
    )

    # Configuration
    config = providers.Singleton(get_settings)

    # Database
    database = providers.Singleton(
        Database,
        settings=config,
    )

    # Redis
    redis = providers.Singleton(
        Redis.from_url,
        url=config.provided.redis_url,
        decode_responses=False,
    )

    # Cache layers
    redis_cache = providers.Singleton(
        RedisCache,
        redis=redis,
        prefix="bananapics",
        default_ttl=config.provided.redis_cache_ttl_seconds,
    )

    memory_cache = providers.Singleton(
        MemoryCache,
        default_ttl=60,  # 1 minute for L1
        max_size=10000,
    )

    cache = providers.Singleton(
        MultiLayerCache,
        redis_cache=redis_cache,
        memory_cache=memory_cache,
        l1_ttl=60,
        l2_ttl=config.provided.redis_cache_ttl_seconds,
    )

    # Repositories - Factory (new instance per request)
    user_repository = providers.Factory(
        "app.infrastructure.repositories.user.UserRepository",
    )

    generation_repository = providers.Factory(
        "app.infrastructure.repositories.generation.GenerationRepository",
    )

    model_repository = providers.Factory(
        "app.infrastructure.repositories.model.ModelRepository",
    )

    ledger_repository = providers.Factory(
        "app.infrastructure.repositories.ledger.LedgerRepository",
    )

    payment_repository = providers.Factory(
        "app.infrastructure.repositories.payment.PaymentRepository",
    )

    broadcast_repository = providers.Factory(
        "app.infrastructure.repositories.broadcast.BroadcastRepository",
    )


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get or create container instance."""
    global _container
    if _container is None:
        _container = Container()
    return _container


async def init_container() -> Container:
    """Initialize container and resources."""
    container = get_container()

    # Initialize database
    await container.database().connect()

    # Start cache
    await container.cache().start()

    return container


async def shutdown_container() -> None:
    """Shutdown container resources."""
    global _container
    if _container is not None:
        # Stop cache
        await _container.cache().stop()

        # Disconnect database
        await _container.database().disconnect()

        # Close Redis
        redis = _container.redis()
        await redis.close()

        _container = None
