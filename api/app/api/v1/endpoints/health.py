from fastapi import APIRouter, Depends

from app.core.config import Settings
from app.deps.common import settings_dep

router = APIRouter()


@router.get("/health")
async def healthcheck(settings: Settings = Depends(settings_dep)) -> dict:
    return {"status": "ok", "version": settings.app_version}
