from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps.db import db_session_dep
from app.schemas.model_catalog import ModelCatalogOut, ModelCatalogWithPricesOut, ModelPriceOut
from app.services.models import list_active_models, list_active_prices_for_models

router = APIRouter()


@router.get("/models", response_model=list[ModelCatalogWithPricesOut])
async def list_models(db: Session = Depends(db_session_dep)) -> list[ModelCatalogWithPricesOut]:
    models = list_active_models(db)
    prices_by_model = list_active_prices_for_models(db, [model.id for model in models])
    response = []
    for model in models:
        response.append(
            ModelCatalogWithPricesOut(
                model=ModelCatalogOut.model_validate(model),
                prices=[
                    ModelPriceOut.model_validate(price)
                    for price in prices_by_model.get(model.id, [])
                ],
            )
        )
    return response
