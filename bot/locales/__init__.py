"""Localization module - multi-language support."""

from .base import TranslationKey, get_text, get_translator, set_user_language
from .manager import LocaleManager

__all__ = [
    "TranslationKey",
    "get_text",
    "get_translator",
    "set_user_language",
    "LocaleManager",
]
