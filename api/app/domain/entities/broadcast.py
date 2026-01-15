"""Broadcast domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class BroadcastStatus(str, Enum):
    """Broadcast status enum."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class BroadcastContentType(str, Enum):
    """Broadcast content type."""
    
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    ANIMATION = "animation"


@dataclass
class Broadcast:
    """Broadcast domain entity."""
    
    id: int
    created_by: int  # Admin user ID
    content_type: BroadcastContentType
    text: Optional[str] = None
    media_file_id: Optional[str] = None
    status: BroadcastStatus = BroadcastStatus.PENDING
    target_count: int = 0  # Total users to send
    sent_count: int = 0
    failed_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def progress_percent(self) -> float:
        """Get broadcast progress percentage."""
        if self.target_count == 0:
            return 0.0
        return (self.sent_count + self.failed_count) / self.target_count * 100
    
    @property
    def is_active(self) -> bool:
        """Check if broadcast is active."""
        return self.status in (BroadcastStatus.PENDING, BroadcastStatus.RUNNING)
