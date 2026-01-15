"""User service."""

from dataclasses import dataclass

from core.container import get_container
from core.logging import get_logger
from infrastructure.api_client import TrialStatus

logger = get_logger(__name__)


@dataclass
class UserProfile:
    """User profile data."""
    telegram_id: int
    balance: int
    trial_available: bool
    trial_used_count: int


class UserService:
    """User-related business logic."""
    
    @staticmethod
    async def sync_user(
        telegram_id: int,
        referral_code: str | None = None,
    ) -> dict:
        """Sync user with API."""
        container = get_container()
        return await container.api_client.sync_user(telegram_id, referral_code)
    
    @staticmethod
    async def get_balance(telegram_id: int) -> int:
        """Get user balance."""
        container = get_container()
        return await container.api_client.get_balance(telegram_id)
    
    @staticmethod
    async def get_trial(telegram_id: int) -> TrialStatus:
        """Get user trial status."""
        container = get_container()
        return await container.api_client.get_trial(telegram_id)
    
    @staticmethod
    async def get_profile(telegram_id: int) -> UserProfile:
        """Get user profile with balance and trial info."""
        container = get_container()
        
        # Sync user first
        await container.api_client.sync_user(telegram_id)
        
        # Get balance and trial
        balance = await container.api_client.get_balance(telegram_id)
        trial = await container.api_client.get_trial(telegram_id)
        
        return UserProfile(
            telegram_id=telegram_id,
            balance=balance,
            trial_available=trial.trial_available,
            trial_used_count=trial.used_count,
        )
    
    @staticmethod
    async def get_referral_info(telegram_id: int) -> dict:
        """Get referral info."""
        container = get_container()
        return await container.api_client.get_referral_info(telegram_id)
    
    @staticmethod
    def format_user_name(first_name: str, last_name: str | None, username: str | None, user_id: int) -> str:
        """Format user display name."""
        parts = [first_name or "", last_name or ""]
        name = " ".join(part for part in parts if part).strip()
        return name or (username or str(user_id))
