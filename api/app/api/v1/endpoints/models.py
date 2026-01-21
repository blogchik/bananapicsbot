import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.deps.db import db_session_dep
from app.schemas.model_catalog import (
    ModelCatalogOut,
    ModelCatalogWithPricesOut,
    ModelOptionsOut,
    ModelPriceOut,
)
from app.services.model_options import get_model_parameter_options_from_wavespeed
from app.services.models import list_active_models, list_active_prices_for_models
from app.services.pricing import apply_price_markup

router = APIRouter()


@router.get("/models", response_model=list[ModelCatalogWithPricesOut])
async def list_models(db: Session = Depends(db_session_dep)) -> list[ModelCatalogWithPricesOut]:
    """List all active models with prices (including admin markup)."""
    settings = get_settings()
    markup = settings.generation_price_markup
    
    models = list_active_models(db)
    prices_by_model = list_active_prices_for_models(db, [model.id for model in models])
    options_list = await asyncio.gather(
        *(get_model_parameter_options_from_wavespeed(model.key) for model in models)
    )
    response = []
    for model, options in zip(models, options_list):
        options_out = ModelOptionsOut(
            supports_size=options.supports_size,
            supports_aspect_ratio=options.supports_aspect_ratio,
            supports_resolution=options.supports_resolution,
            supports_quality=options.supports_quality,
            supports_input_fidelity=options.supports_input_fidelity,
            quality_stars=options.quality_stars,
            avg_duration_seconds_min=options.avg_duration_seconds_min,
            avg_duration_seconds_max=options.avg_duration_seconds_max,
            avg_duration_text=options.avg_duration_text,
            size_options=options.size_options,
            aspect_ratio_options=options.aspect_ratio_options,
            resolution_options=options.resolution_options,
            quality_options=options.quality_options,
            input_fidelity_options=options.input_fidelity_options,
        )
        model_out = ModelCatalogOut.model_validate(model).model_copy(
            update={"options": options_out}
        )
        response.append(
            ModelCatalogWithPricesOut(
                model=model_out,
                prices=[
                    ModelPriceOut.model_validate(price).model_copy(
                        update={"unit_price": apply_price_markup(int(price.unit_price), markup)}
                    )
                    for price in prices_by_model.get(model.id, [])
                ],
            )
        )
    return response
