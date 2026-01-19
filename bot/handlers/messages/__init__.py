"""Message handlers."""

from aiogram import Router

from .media import router as media_router
from .prompt import router as prompt_router

# Create messages router
messages_router = Router(name="messages")
messages_router.include_router(media_router)  # Media first (photos, documents)
messages_router.include_router(prompt_router)  # Text messages

__all__ = ["messages_router"]
