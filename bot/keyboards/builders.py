"""Callback data builders and parsers."""

from typing import Any
from dataclasses import dataclass


@dataclass
class CallbackDataBuilder:
    """
    Callback data builder utility.
    
    Helps create and parse callback data strings with type safety.
    """
    
    separator: str = ":"
    
    def build(self, *parts: str | int) -> str:
        """Build callback data from parts."""
        return self.separator.join(str(p) for p in parts)
    
    def parse(self, data: str) -> list[str]:
        """Parse callback data into parts."""
        return data.split(self.separator)
    
    def get_prefix(self, data: str) -> str:
        """Get first part (prefix) of callback data."""
        parts = self.parse(data)
        return parts[0] if parts else ""
    
    def get_action(self, data: str) -> str:
        """Get second part (action) of callback data."""
        parts = self.parse(data)
        return parts[1] if len(parts) > 1 else ""
    
    def get_value(self, data: str, index: int = 2) -> str | None:
        """Get value at specific index."""
        parts = self.parse(data)
        return parts[index] if len(parts) > index else None
    
    def get_int_value(self, data: str, index: int = 2) -> int | None:
        """Get integer value at specific index."""
        value = self.get_value(data, index)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None


# Menu callback patterns
class MenuCallback:
    """Menu callback data patterns."""
    
    HOME = "menu:home"
    GENERATION = "menu:generation"
    WATERMARK = "menu:watermark"
    PROFILE = "menu:profile"
    TOPUP = "menu:topup"
    REFERRAL = "menu:referral"
    SETTINGS = "menu:settings"
    HELP = "menu:help"


class GenerationCallback:
    """Generation callback data patterns."""
    
    MODEL_MENU = "gen:model:menu"
    SIZE_MENU = "gen:size:menu"
    RATIO_MENU = "gen:ratio:menu"
    RESOLUTION_MENU = "gen:resolution:menu"
    QUALITY_MENU = "gen:quality:menu"
    INPUT_FIDELITY_MENU = "gen:input_fidelity:menu"
    SUBMIT = "gen:submit"
    BACK = "gen:back"
    RETRY = "gen:retry"
    
    @staticmethod
    def model_set(model_id: int) -> str:
        return f"gen:model:set:{model_id}"
    
    @staticmethod
    def size_set(size: str) -> str:
        return f"gen:size:set:{size}"
    
    @staticmethod
    def ratio_set(ratio: str) -> str:
        return f"gen:ratio:set:{ratio}"
    
    @staticmethod
    def resolution_set(resolution: str) -> str:
        return f"gen:resolution:set:{resolution}"

    @staticmethod
    def quality_set(quality: str) -> str:
        return f"gen:quality:set:{quality}"

    @staticmethod
    def input_fidelity_set(value: str) -> str:
        return f"gen:input_fidelity:set:{value}"


class WatermarkCallback:
    """Watermark tool callback data patterns."""

    REMOVE = "wm:remove"

    @staticmethod
    def remove(message_id: int) -> str:
        return f"wm:remove:{message_id}"


class TopupCallback:
    """Top-up callback data patterns."""
    
    CUSTOM = "topup:custom"
    
    @staticmethod
    def stars(amount: int) -> str:
        return f"topup:stars:{amount}"


class SettingsCallback:
    """Settings callback data patterns."""
    
    LANGUAGE_MENU = "settings:lang"
    
    @staticmethod
    def language_set(code: str) -> str:
        return f"settings:lang:{code}"


class AdminCallback:
    """Admin callback data patterns."""
    
    # Main menu
    PANEL = "admin:panel"
    MAIN = "admin:main"
    CANCEL = "admin:cancel"
    
    # Stats
    STATS = "admin:stats"
    STATS_OVERVIEW = "admin:stats:overview"
    STATS_USERS = "admin:stats:users"
    STATS_GENERATIONS = "admin:stats:generations"
    STATS_REVENUE = "admin:stats:revenue"
    
    # Users management
    USERS = "admin:users"
    USERS_SEARCH = "admin:users:search"
    USERS_LIST = "admin:users:list"
    
    # Actions
    ADD_CREDITS = "admin:credits"
    REFUND = "admin:refund"
    
    # Refund types
    REFUND_CREDITS = "admin:refund:credits"
    REFUND_STARS = "admin:refund:stars"
    REFUND_STARS_CONFIRM = "admin:refund:stars:confirm"
    REFUND_STARS_CANCEL = "admin:refund:stars:cancel"
    REFUND_STARS_ALL = "admin:refund:stars:all"
    
    @staticmethod
    def refund_stars_tx(index: int) -> str:
        """Create callback for specific transaction refund by index."""
        return f"admin:refund:stars:tx:{index}"
    
    # Broadcast
    BROADCAST = "admin:broadcast"
    BROADCAST_NEW = "admin:broadcast:new"
    BROADCAST_CONFIRM = "admin:broadcast:confirm"
    BROADCAST_CANCEL = "admin:broadcast:cancel"
    BROADCAST_HISTORY = "admin:broadcast:history"
    
    BACK = "admin:back"
    
    @staticmethod
    def user_page(page: int) -> str:
        return f"admin:users:page:{page}"
    
    @staticmethod
    def user_detail(user_id: int) -> str:
        return f"admin:user:{user_id}"
