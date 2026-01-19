"""Locale manager for handling translations."""

from typing import Any


class LocaleManager:
    """
    Locale manager singleton.
    
    Handles translation loading and retrieval.
    """

    _instance: "LocaleManager | None" = None

    def __init__(self) -> None:
        self._translations: dict[str, dict[str, str]] = {}
        self._default_language = "uz"
        self._load_translations()

    @classmethod
    def get_instance(cls) -> "LocaleManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset instance (for testing)."""
        cls._instance = None

    def _load_translations(self) -> None:
        """Load all translations."""
        from . import en, ru, uz

        self._translations = {
            "uz": uz.TRANSLATIONS,
            "ru": ru.TRANSLATIONS,
            "en": en.TRANSLATIONS,
        }

    @property
    def available_languages(self) -> list[str]:
        """Get available language codes."""
        return list(self._translations.keys())

    @property
    def language_names(self) -> dict[str, str]:
        """Get language names."""
        return {
            "uz": "🇺🇿 O'zbek",
            "ru": "🇷🇺 Русский",
            "en": "🇬🇧 English",
        }

    def get(
        self,
        language: str,
        key: str,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Get translated text."""
        # Get translation dict for language
        translations = self._translations.get(language)
        if translations is None:
            translations = self._translations.get(self._default_language, {})

        # Get text by key
        text = translations.get(key)
        if text is None:
            # Fallback to default language
            text = self._translations.get(self._default_language, {}).get(key)
        if text is None:
            # Return key if translation not found
            return f"[{key}]"

        # Format with params
        if params:
            try:
                text = text.format(**params)
            except (KeyError, ValueError):
                pass

        return text

    def set_default_language(self, language: str) -> None:
        """Set default language."""
        if language in self._translations:
            self._default_language = language
