"""Generation domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class GenerationStatus(str, Enum):
    """Generation status enum."""

    PENDING = "pending"
    CONFIGURING = "configuring"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass
class GenerationReference:
    """Reference image for generation."""

    id: int
    request_id: int
    telegram_file_id: Optional[str] = None
    url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GenerationResult:
    """Generation result (output image)."""

    id: int
    request_id: int
    url: str
    telegram_file_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Generation:
    """Generation domain entity."""

    id: int
    public_id: str
    user_id: int
    model_id: int
    prompt: str
    status: GenerationStatus = GenerationStatus.PENDING
    size: Optional[str] = None
    aspect_ratio: Optional[str] = None
    resolution: Optional[str] = None
    style: Optional[str] = None
    input_params: Optional[dict[str, Any]] = None
    references_count: int = 0
    cost: Optional[int] = None
    is_trial: bool = False
    error_message: Optional[str] = None
    wavespeed_request_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    references: list[GenerationReference] = field(default_factory=list)
    results: list[GenerationResult] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        """Check if generation is still in progress."""
        return self.status in (
            GenerationStatus.PENDING,
            GenerationStatus.CONFIGURING,
            GenerationStatus.QUEUED,
            GenerationStatus.RUNNING,
        )

    @property
    def is_finished(self) -> bool:
        """Check if generation is finished."""
        return self.status in (
            GenerationStatus.COMPLETED,
            GenerationStatus.FAILED,
            GenerationStatus.CANCELLED,
            GenerationStatus.REFUNDED,
        )


@dataclass
class GenerationCreate:
    """Generation creation DTO."""

    user_id: int
    model_id: int
    prompt: str
    size: Optional[str] = None
    aspect_ratio: Optional[str] = None
    resolution: Optional[str] = None
    style: Optional[str] = None
    reference_urls: list[str] = field(default_factory=list)
    reference_file_ids: list[str] = field(default_factory=list)
    is_trial: bool = False
