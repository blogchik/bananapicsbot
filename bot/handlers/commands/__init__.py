"""Command handlers."""

from aiogram import Router

from .start import router as start_router
from .profile import router as profile_router
from .settings import router as settings_router
from .help import router as help_router

# Create commands router
commands_router = Router(name="commands")
commands_router.include_router(start_router)
commands_router.include_router(profile_router)
commands_router.include_router(settings_router)
commands_router.include_router(help_router)

__all__ = ["commands_router"]
