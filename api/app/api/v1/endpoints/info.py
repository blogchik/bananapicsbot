from fastapi import APIRouter, Depends

from app.core.config import Settings
from app.deps.common import settings_dep
from app.schemas.common import InfoResponse

router = APIRouter()


@router.get("/info", response_model=InfoResponse)
async def info(settings: Settings = Depends(settings_dep)) -> InfoResponse:
    return InfoResponse(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
