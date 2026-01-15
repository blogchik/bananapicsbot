"""Redis client for caching and rate limiting."""

import asyncio
from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis

from core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """
    Redis client wrapper with connection pooling.
    
    Features:
    - Connection pooling
    - Automatic reconnection
    - Key prefixing
    - Rate limiting support
    - Caching support
    """
    
    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        prefix: str = "bot",
        max_connections: int = 50,
    ) -> None:
        self.url = url
        self.prefix = prefix
        self.max_connections = max_connections
        self._pool: redis.ConnectionPool | None = None
        self._client: Redis | None = None
    
    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self.prefix}:{key}"
    
    async def _get_client(self) -> Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._pool = redis.ConnectionPool.from_url(
                self.url,
                max_connections=self.max_connections,
                decode_responses=True,
            )
            self._client = Redis(connection_pool=self._pool)
        return self._client
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None
        if self._pool is not None:
            await self._pool.disconnect()
            self._pool = None
    
    async def ping(self) -> bool:
        """Check Redis connection."""
        try:
            client = await self._get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error("Redis ping failed", error=str(e))
            return False
    
    # Basic operations
    async def get(self, key: str) -> str | None:
        """Get value by key."""
        client = await self._get_client()
        return await client.get(self._make_key(key))
    
    async def set(
        self,
        key: str,
        value: str,
        expire_seconds: int | None = None,
    ) -> bool:
        """Set value with optional expiration."""
        client = await self._get_client()
        return await client.set(
            self._make_key(key),
            value,
            ex=expire_seconds,
        )
    
    async def delete(self, key: str) -> int:
        """Delete key."""
        client = await self._get_client()
        return await client.delete(self._make_key(key))
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        client = await self._get_client()
        return await client.exists(self._make_key(key)) > 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration."""
        client = await self._get_client()
        return await client.expire(self._make_key(key), seconds)
    
    async def ttl(self, key: str) -> int:
        """Get key TTL."""
        client = await self._get_client()
        return await client.ttl(self._make_key(key))
    
    # Hash operations
    async def hget(self, name: str, key: str) -> str | None:
        """Get hash field."""
        client = await self._get_client()
        return await client.hget(self._make_key(name), key)
    
    async def hset(self, name: str, key: str, value: str) -> int:
        """Set hash field."""
        client = await self._get_client()
        return await client.hset(self._make_key(name), key, value)
    
    async def hgetall(self, name: str) -> dict[str, str]:
        """Get all hash fields."""
        client = await self._get_client()
        return await client.hgetall(self._make_key(name))
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        client = await self._get_client()
        return await client.hdel(self._make_key(name), *keys)
    
    # Rate limiting
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """
        Check rate limit using sliding window.
        
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        client = await self._get_client()
        full_key = self._make_key(f"ratelimit:{key}")
        
        current = await client.incr(full_key)
        if current == 1:
            await client.expire(full_key, window_seconds)
        
        remaining = max(0, limit - current)
        is_allowed = current <= limit
        
        return is_allowed, remaining
    
    async def get_rate_limit_ttl(self, key: str) -> int:
        """Get rate limit TTL."""
        client = await self._get_client()
        full_key = self._make_key(f"ratelimit:{key}")
        ttl = await client.ttl(full_key)
        return max(0, ttl)
    
    # Cache operations
    async def cache_get(self, key: str) -> str | None:
        """Get cached value."""
        return await self.get(f"cache:{key}")
    
    async def cache_set(
        self,
        key: str,
        value: str,
        ttl_seconds: int = 300,
    ) -> bool:
        """Set cached value with TTL."""
        return await self.set(f"cache:{key}", value, expire_seconds=ttl_seconds)
    
    async def cache_delete(self, key: str) -> int:
        """Delete cached value."""
        return await self.delete(f"cache:{key}")
    
    # User language
    async def get_user_language(self, user_id: int) -> str | None:
        """Get user's preferred language."""
        return await self.hget("user_languages", str(user_id))
    
    async def set_user_language(self, user_id: int, language: str) -> int:
        """Set user's preferred language."""
        return await self.hset("user_languages", str(user_id), language)
    
    # Locks
    async def acquire_lock(
        self,
        key: str,
        ttl_seconds: int = 30,
    ) -> bool:
        """Acquire distributed lock."""
        client = await self._get_client()
        full_key = self._make_key(f"lock:{key}")
        return await client.set(full_key, "1", nx=True, ex=ttl_seconds)
    
    async def release_lock(self, key: str) -> int:
        """Release distributed lock."""
        return await self.delete(f"lock:{key}")
