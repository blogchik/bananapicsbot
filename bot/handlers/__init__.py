"""Handlers module - all bot event handlers."""

from aiogram import Router

from .admin import admin_router
from .callbacks import callbacks_router
from .commands import commands_router
from .messages import messages_router
from .payments import payments_router


def setup_handlers() -> Router:
    """Setup all handlers and return main router."""
    router = Router(name="main")

    # Include routers in priority order
    router.include_router(admin_router)  # Admin handlers first
    router.include_router(commands_router)
    router.include_router(callbacks_router)
    router.include_router(payments_router)
    router.include_router(messages_router)  # Messages last (catch-all)

    return router


__all__ = ["setup_handlers"]
