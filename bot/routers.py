from aiogram import Router

from handlers import profile_router, start_router


def setup_routers() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(profile_router)
    return router
