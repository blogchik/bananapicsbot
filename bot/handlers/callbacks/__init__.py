"""Callback handlers."""

from aiogram import Router

from .navigation import router as navigation_router
from .generation import router as generation_router
from .settings import router as settings_router
from .referral import router as referral_router

# Create callbacks router
callbacks_router = Router(name="callbacks")
callbacks_router.include_router(navigation_router)
callbacks_router.include_router(generation_router)
callbacks_router.include_router(settings_router)
callbacks_router.include_router(referral_router)

__all__ = ["callbacks_router"]
