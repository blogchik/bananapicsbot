from datetime import datetime

from pydantic import BaseModel


class ModelCatalogOut(BaseModel):
    id: int
    key: str
    name: str
    provider: str
    supports_reference: bool
    supports_aspect_ratio: bool
    supports_style: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ModelPriceOut(BaseModel):
    id: int
    model_id: int
    currency: str
    unit_price: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ModelCatalogWithPricesOut(BaseModel):
    model: ModelCatalogOut
    prices: list[ModelPriceOut]
