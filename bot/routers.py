from aiogram import Router

from handlers import (
    admin_router,
    generation_router,
    payments_router,
    profile_router,
    referral_router,
    start_router,
)


def setup_routers() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(admin_router)
    router.include_router(profile_router)
    router.include_router(payments_router)
    router.include_router(referral_router)
    router.include_router(generation_router)
    return router
