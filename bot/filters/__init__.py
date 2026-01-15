"""Custom filters for the bot."""

from .admin import AdminFilter, IsAdminFilter
from .chat_type import PrivateChatFilter

__all__ = [
    "AdminFilter",
    "IsAdminFilter",
    "PrivateChatFilter",
]
