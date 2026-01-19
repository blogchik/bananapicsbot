"""Ledger domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class LedgerEntryType(str, Enum):
    """Ledger entry types."""

    # Credits
    ADMIN_CREDIT = "admin_credit"
    REFERRAL_BONUS = "referral_bonus"
    STARS_PURCHASE = "stars_purchase"
    PROMO_CREDIT = "promo_credit"
    REFUND = "refund"

    # Debits
    GENERATION_COST = "generation_cost"

    # Adjustments
    ADMIN_ADJUSTMENT = "admin_adjustment"


@dataclass
class LedgerEntry:
    """Ledger entry domain entity."""

    id: int
    user_id: int
    amount: int
    entry_type: LedgerEntryType
    reference_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[int] = None  # Admin user ID

    @property
    def is_credit(self) -> bool:
        """Check if this is a credit entry."""
        return self.amount > 0

    @property
    def is_debit(self) -> bool:
        """Check if this is a debit entry."""
        return self.amount < 0
