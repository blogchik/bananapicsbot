"""In-memory cache implementation using TTL cache."""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    value: Any
    expires_at: datetime

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class MemoryCache:
    """Thread-safe in-memory cache with TTL."""

    def __init__(
        self,
        default_ttl: int = 300,  # 5 minutes
        max_size: int = 10000,
        cleanup_interval: int = 60,
    ):
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start cleanup background task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop cleanup background task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self) -> None:
        """Periodically clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception:
                pass  # Continue on errors

    async def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        async with self._lock:
            now = datetime.utcnow()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]

    async def _ensure_capacity(self) -> None:
        """Ensure cache doesn't exceed max size."""
        if len(self._cache) >= self.max_size:
            # Remove oldest entries (simple LRU approximation)
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].expires_at,
            )
            remove_count = len(self._cache) - self.max_size + 100
            for key, _ in sorted_entries[:remove_count]:
                del self._cache[key]

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.is_expired():
                del self._cache[key]
                return None
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in cache."""
        async with self._lock:
            await self._ensure_capacity()
            expires_at = datetime.utcnow() + timedelta(
                seconds=ttl if ttl is not None else self.default_ttl
            )
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired():
                del self._cache[key]
                return False
            return True

    async def clear(self) -> None:
        """Clear all cache."""
        async with self._lock:
            self._cache.clear()

    async def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple values."""
        result = {}
        async with self._lock:
            for key in keys:
                entry = self._cache.get(key)
                if entry and not entry.is_expired():
                    result[key] = entry.value
        return result

    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """Set multiple values."""
        async with self._lock:
            await self._ensure_capacity()
            expires_at = datetime.utcnow() + timedelta(
                seconds=ttl if ttl is not None else self.default_ttl
            )
            for key, value in items.items():
                self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern (simple glob)."""
        import fnmatch
        async with self._lock:
            matching_keys = [
                key for key in self._cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            for key in matching_keys:
                del self._cache[key]
            return len(matching_keys)

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "default_ttl": self.default_ttl,
        }
