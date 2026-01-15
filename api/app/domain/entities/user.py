"""User domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User domain entity."""
    
    id: int
    telegram_id: int
    referral_code: str
    referred_by_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: str = "uz"
    is_banned: bool = False
    is_admin: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else f"User {self.telegram_id}"


@dataclass
class UserCreate:
    """User creation DTO."""
    
    telegram_id: int
    referral_code: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: str = "uz"


@dataclass
class UserUpdate:
    """User update DTO."""
    
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    is_banned: Optional[bool] = None
    is_admin: Optional[bool] = None
