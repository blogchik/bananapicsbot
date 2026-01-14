from redis.asyncio import Redis

from app.services.redis_client import get_redis


async def redis_dep() -> Redis:
    return get_redis()
