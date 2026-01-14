from fastapi import APIRouter

from app.api.v1.endpoints import health, info, models, users

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(info.router, tags=["info"])
router.include_router(users.router, tags=["users"])
router.include_router(models.router, tags=["models"])
