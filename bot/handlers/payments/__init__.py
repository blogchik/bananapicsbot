"""Payment handlers."""

from aiogram import Router

from .stars import router as stars_router

# Create payments router
payments_router = Router(name="payments")
payments_router.include_router(stars_router)

__all__ = ["payments_router"]
