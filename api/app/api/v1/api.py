from fastapi import APIRouter

from app.api.v1.endpoints import health, info

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(info.router, tags=["info"])
