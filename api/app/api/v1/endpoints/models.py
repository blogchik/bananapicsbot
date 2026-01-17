from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services.model_options import get_model_parameter_options_from_wavespeed
from app.deps.db import db_session_dep
from app.schemas.model_catalog import (
    ModelCatalogOut,
    ModelCatalogWithPricesOut,
    ModelOptionsOut,
    ModelPriceOut,
)
from app.services.models import list_active_models, list_active_prices_for_models

router = APIRouter()


@router.get("/models", response_model=list[ModelCatalogWithPricesOut])
async def list_models(db: Session = Depends(db_session_dep)) -> list[ModelCatalogWithPricesOut]:
    models = list_active_models(db)
    prices_by_model = list_active_prices_for_models(db, [model.id for model in models])
    response = []
    for model in models:
        options = await get_model_parameter_options_from_wavespeed(model.key)
        options_out = ModelOptionsOut(
            supports_size=options.supports_size,
            supports_aspect_ratio=options.supports_aspect_ratio,
            supports_resolution=options.supports_resolution,
            quality_stars=options.quality_stars,
            avg_duration_seconds_min=options.avg_duration_seconds_min,
            avg_duration_seconds_max=options.avg_duration_seconds_max,
            avg_duration_text=options.avg_duration_text,
            size_options=options.size_options,
            aspect_ratio_options=options.aspect_ratio_options,
            resolution_options=options.resolution_options,
        )
        model_out = ModelCatalogOut.model_validate(model).model_copy(
            update={"options": options_out}
        )
        response.append(
            ModelCatalogWithPricesOut(
                model=model_out,
                prices=[
                    ModelPriceOut.model_validate(price)
                    for price in prices_by_model.get(model.id, [])
                ],
            )
        )
    return response
