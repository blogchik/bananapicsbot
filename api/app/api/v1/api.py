from fastapi import APIRouter

from app.api.v1.endpoints import generations, health, info, media, models, users

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(info.router, tags=["info"])
router.include_router(users.router, tags=["users"])
router.include_router(models.router, tags=["models"])
router.include_router(generations.router, tags=["generations"])
router.include_router(media.router, tags=["media"])
