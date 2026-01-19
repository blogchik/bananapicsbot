"""Model domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ModelPrice:
    """Model pricing entity."""

    id: int
    model_id: int
    currency: str = "credit"
    unit_price: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Model:
    """AI Model domain entity."""

    id: int
    key: str
    name: str
    provider: str
    description: Optional[str] = None
    supports_text_to_image: bool = False
    supports_image_to_image: bool = False
    supports_reference: bool = False
    supports_aspect_ratio: bool = False
    supports_size: bool = False
    supports_resolution: bool = False
    supports_style: bool = False
    is_active: bool = True
    sort_order: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    prices: list[ModelPrice] = field(default_factory=list)

    @property
    def current_price(self) -> int:
        """Get current active price."""
        for price in self.prices:
            if price.is_active and price.currency == "credit":
                return price.unit_price
        return 0
