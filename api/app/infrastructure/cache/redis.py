"""Redis cache implementation."""
from typing import Optional, Any, Dict
import json
from datetime import timedelta

from redis.asyncio import Redis

from app.core.config import get_settings


class RedisCache:
    """Redis cache implementation."""
    
    def __init__(
        self,
        redis: Redis,
        prefix: str = "cache",
        default_ttl: int = 300,  # 5 minutes
    ):
        self._redis = redis
        self._prefix = prefix
        self.default_ttl = default_ttl
    
    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self._prefix}:{key}"
    
    def _serialize(self, value: Any) -> str:
        """Serialize value to JSON."""
        return json.dumps(value, default=str)
    
    def _deserialize(self, value: Optional[bytes]) -> Optional[Any]:
        """Deserialize value from JSON."""
        if value is None:
            return None
        return json.loads(value.decode("utf-8"))
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = await self._redis.get(self._make_key(key))
        return self._deserialize(value)
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in cache."""
        await self._redis.set(
            self._make_key(key),
            self._serialize(value),
            ex=ttl if ttl is not None else self.default_ttl,
        )
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        result = await self._redis.delete(self._make_key(key))
        return result > 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self._redis.exists(self._make_key(key)) > 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on key."""
        return await self._redis.expire(self._make_key(key), ttl)
    
    async def ttl(self, key: str) -> int:
        """Get TTL of key."""
        return await self._redis.ttl(self._make_key(key))
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment value."""
        return await self._redis.incrby(self._make_key(key), amount)
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement value."""
        return await self._redis.decrby(self._make_key(key), amount)
    
    async def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple values."""
        if not keys:
            return {}
        
        prefixed_keys = [self._make_key(k) for k in keys]
        values = await self._redis.mget(prefixed_keys)
        
        return {
            key: self._deserialize(value)
            for key, value in zip(keys, values)
            if value is not None
        }
    
    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """Set multiple values."""
        if not items:
            return
        
        pipe = self._redis.pipeline()
        for key, value in items.items():
            pipe.set(
                self._make_key(key),
                self._serialize(value),
                ex=ttl if ttl is not None else self.default_ttl,
            )
        await pipe.execute()
    
    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple keys."""
        if not keys:
            return 0
        
        prefixed_keys = [self._make_key(k) for k in keys]
        return await self._redis.delete(*prefixed_keys)
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        prefixed_pattern = self._make_key(pattern)
        keys = []
        async for key in self._redis.scan_iter(prefixed_pattern):
            keys.append(key)
        
        if keys:
            return await self._redis.delete(*keys)
        return 0
    
    async def clear(self) -> None:
        """Clear all cache (with prefix)."""
        await self.delete_pattern("*")
    
    async def ping(self) -> bool:
        """Check connection."""
        try:
            await self._redis.ping()
            return True
        except Exception:
            return False
    
    # Hash operations
    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field."""
        value = await self._redis.hget(self._make_key(key), field)
        return self._deserialize(value)
    
    async def hset(
        self,
        key: str,
        field: str,
        value: Any,
    ) -> None:
        """Set hash field."""
        await self._redis.hset(
            self._make_key(key),
            field,
            self._serialize(value),
        )
    
    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields."""
        data = await self._redis.hgetall(self._make_key(key))
        return {
            k.decode("utf-8"): self._deserialize(v)
            for k, v in data.items()
        }
    
    async def hdel(self, key: str, *fields: str) -> int:
        """Delete hash fields."""
        return await self._redis.hdel(self._make_key(key), *fields)
    
    # List operations
    async def lpush(self, key: str, *values: Any) -> int:
        """Push to list (left)."""
        serialized = [self._serialize(v) for v in values]
        return await self._redis.lpush(self._make_key(key), *serialized)
    
    async def rpush(self, key: str, *values: Any) -> int:
        """Push to list (right)."""
        serialized = [self._serialize(v) for v in values]
        return await self._redis.rpush(self._make_key(key), *serialized)
    
    async def lrange(
        self,
        key: str,
        start: int = 0,
        end: int = -1,
    ) -> list[Any]:
        """Get list range."""
        values = await self._redis.lrange(self._make_key(key), start, end)
        return [self._deserialize(v) for v in values]
    
    async def llen(self, key: str) -> int:
        """Get list length."""
        return await self._redis.llen(self._make_key(key))
