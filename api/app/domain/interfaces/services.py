"""Service interfaces - external service contracts."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class IWavespeedService(ABC):
    """Wavespeed AI service interface."""
    
    @abstractmethod
    async def submit_generation(
        self,
        model_key: str,
        prompt: str,
        images: Optional[list[str]] = None,
        size: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
    ) -> dict[str, Any]:
        """Submit generation to Wavespeed."""
        pass
    
    @abstractmethod
    async def get_generation_status(
        self,
        request_id: str,
    ) -> dict[str, Any]:
        """Get generation status from Wavespeed."""
        pass
    
    @abstractmethod
    async def cancel_generation(
        self,
        request_id: str,
    ) -> bool:
        """Cancel generation in Wavespeed."""
        pass


class ICacheService(ABC):
    """Cache service interface."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: int) -> None:
        """Set TTL on key."""
        pass


class IEventPublisher(ABC):
    """Event publisher interface for async communication."""
    
    @abstractmethod
    async def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Publish event."""
        pass
    
    @abstractmethod
    async def publish_delayed(
        self,
        event_type: str,
        payload: dict[str, Any],
        delay_seconds: int,
    ) -> None:
        """Publish delayed event."""
        pass
