"""Payment domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    """Payment status enum."""
    
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentProvider(str, Enum):
    """Payment provider enum."""
    
    TELEGRAM_STARS = "telegram_stars"
    CLICK = "click"
    PAYME = "payme"


@dataclass
class Payment:
    """Payment domain entity."""
    
    id: int
    user_id: int
    amount: int  # Stars or currency amount
    credits: int  # Credits to add
    provider: PaymentProvider
    status: PaymentStatus = PaymentStatus.PENDING
    telegram_charge_id: Optional[str] = None
    provider_charge_id: Optional[str] = None
    invoice_payload: Optional[str] = None
    currency: str = "XTR"  # Telegram Stars
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    
    @property
    def is_completed(self) -> bool:
        """Check if payment is completed."""
        return self.status == PaymentStatus.COMPLETED
    
    @property
    def is_refundable(self) -> bool:
        """Check if payment can be refunded."""
        return self.status == PaymentStatus.COMPLETED
