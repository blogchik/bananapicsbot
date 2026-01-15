"""Multi-layer cache implementation."""
from typing import Optional, Any, Dict

from app.domain.interfaces.services import ICacheService
from app.infrastructure.cache.memory import MemoryCache
from app.infrastructure.cache.redis import RedisCache


class MultiLayerCache(ICacheService):
    """Multi-layer cache: L1 (Memory) + L2 (Redis).
    
    Read path: L1 -> L2 -> DB (if miss, populate both)
    Write path: Invalidate L1 -> Write L2
    """
    
    def __init__(
        self,
        redis_cache: RedisCache,
        memory_cache: Optional[MemoryCache] = None,
        l1_ttl: int = 60,  # 1 minute for memory
        l2_ttl: int = 300,  # 5 minutes for Redis
    ):
        self._l1 = memory_cache or MemoryCache(default_ttl=l1_ttl)
        self._l2 = redis_cache
        self._l1_ttl = l1_ttl
        self._l2_ttl = l2_ttl
    
    @property
    def l1(self) -> MemoryCache:
        """L1 (memory) cache."""
        return self._l1
    
    @property
    def l2(self) -> RedisCache:
        """L2 (Redis) cache."""
        return self._l2
    
    async def start(self) -> None:
        """Start cache layers."""
        await self._l1.start()
    
    async def stop(self) -> None:
        """Stop cache layers."""
        await self._l1.stop()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache (L1 first, then L2)."""
        # Try L1
        value = await self._l1.get(key)
        if value is not None:
            return value
        
        # Try L2
        value = await self._l2.get(key)
        if value is not None:
            # Populate L1
            await self._l1.set(key, value, self._l1_ttl)
            return value
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set in both cache layers."""
        l2_ttl = ttl if ttl is not None else self._l2_ttl
        l1_ttl = min(self._l1_ttl, l2_ttl)
        
        # Write to both
        await self._l1.set(key, value, l1_ttl)
        await self._l2.set(key, value, l2_ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete from both layers."""
        l1_deleted = await self._l1.delete(key)
        l2_deleted = await self._l2.delete(key)
        return l1_deleted or l2_deleted
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in any layer."""
        if await self._l1.exists(key):
            return True
        return await self._l2.exists(key)
    
    async def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple values."""
        result = {}
        missing_keys = []
        
        # Try L1 first
        for key in keys:
            value = await self._l1.get(key)
            if value is not None:
                result[key] = value
            else:
                missing_keys.append(key)
        
        # Try L2 for missing
        if missing_keys:
            l2_results = await self._l2.get_many(missing_keys)
            for key, value in l2_results.items():
                result[key] = value
                # Populate L1
                await self._l1.set(key, value, self._l1_ttl)
        
        return result
    
    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """Set multiple values in both layers."""
        l2_ttl = ttl if ttl is not None else self._l2_ttl
        l1_ttl = min(self._l1_ttl, l2_ttl)
        
        await self._l1.set_many(items, l1_ttl)
        await self._l2.set_many(items, l2_ttl)
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        l1_count = await self._l1.delete_pattern(pattern)
        l2_count = await self._l2.delete_pattern(pattern)
        return max(l1_count, l2_count)
    
    async def clear(self) -> None:
        """Clear both layers."""
        await self._l1.clear()
        await self._l2.clear()
    
    async def invalidate(self, key: str) -> None:
        """Invalidate key (delete from L1 only for read-through)."""
        await self._l1.delete(key)
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate pattern (delete from L1 only)."""
        return await self._l1.delete_pattern(pattern)
    
    # Cache-aside pattern helpers
    async def get_or_set(
        self,
        key: str,
        factory,  # async callable
        ttl: Optional[int] = None,
    ) -> Any:
        """Get from cache or compute and cache."""
        value = await self.get(key)
        if value is not None:
            return value
        
        # Compute value
        value = await factory()
        
        # Cache it
        await self.set(key, value, ttl)
        
        return value
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "l1": self._l1.stats(),
            "l1_ttl": self._l1_ttl,
            "l2_ttl": self._l2_ttl,
        }
