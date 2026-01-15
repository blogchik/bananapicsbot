"""FSM storage factory."""

from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage

from core.logging import get_logger

logger = get_logger(__name__)


async def create_fsm_storage(settings) -> BaseStorage:
    """
    Create FSM storage.
    
    If Redis URL is provided and connection succeeds, uses Redis storage.
    Otherwise, falls back to memory storage.
    
    Args:
        settings: Application settings
    
    Returns:
        FSM storage instance
    """
    redis_url = getattr(settings, "redis_url", None)
    
    if redis_url:
        try:
            from redis.asyncio import Redis
            from aiogram.fsm.storage.redis import RedisStorage
            
            # Create Redis client
            redis_client = Redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            await redis_client.ping()
            
            # Create Redis storage
            storage = RedisStorage(redis=redis_client)
            logger.info("Using Redis FSM storage", url=redis_url)
            return storage
        
        except Exception as e:
            logger.warning(
                "Failed to connect to Redis, falling back to memory storage",
                error=str(e),
            )
    
    logger.info("Using memory FSM storage")
    return MemoryStorage()
