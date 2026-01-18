from datetime import datetime

from pydantic import BaseModel, Field


class ModelOptionsOut(BaseModel):
    supports_size: bool = False
    supports_aspect_ratio: bool = False
    supports_resolution: bool = False
    supports_quality: bool = False
    supports_input_fidelity: bool = False
    quality_stars: int | None = None
    avg_duration_seconds_min: int | None = None
    avg_duration_seconds_max: int | None = None
    avg_duration_text: str | None = None
    size_options: list[str] = Field(default_factory=list)
    aspect_ratio_options: list[str] = Field(default_factory=list)
    resolution_options: list[str] = Field(default_factory=list)
    quality_options: list[str] = Field(default_factory=list)
    input_fidelity_options: list[str] = Field(default_factory=list)


class ModelCatalogOut(BaseModel):
    id: int
    key: str
    name: str
    provider: str
    supports_text_to_image: bool
    supports_image_to_image: bool
    supports_reference: bool
    supports_aspect_ratio: bool
    supports_style: bool
    is_active: bool
    created_at: datetime
    options: ModelOptionsOut | None = None

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
