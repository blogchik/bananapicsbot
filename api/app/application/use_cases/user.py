"""User use cases."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Sequence

from app.domain.entities.user import User, UserCreate, UserUpdate
from app.domain.interfaces.repositories import ILedgerRepository, IUserRepository
from app.domain.interfaces.services import ICacheService
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class UserProfileDTO:
    """User profile with balance."""
    user: User
    balance: Decimal
    referral_count: int
    generation_count: int


class GetOrCreateUserUseCase:
    """Get existing user or create new one."""

    def __init__(
        self,
        user_repo: IUserRepository,
        ledger_repo: ILedgerRepository,
        cache: ICacheService,
        trial_generations: int = 3,
    ):
        self._user_repo = user_repo
        self._ledger_repo = ledger_repo
        self._cache = cache
        self._trial_generations = trial_generations

    async def execute(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
        referrer_id: Optional[int] = None,
    ) -> tuple[User, bool]:
        """
        Execute use case.
        
        Returns:
            Tuple of (user, is_new)
        """
        # Check cache first
        cache_key = f"user:{telegram_id}"
        cached = await self._cache.get(cache_key)
        if cached:
            return User(**cached), False

        # Try to get existing user
        user = await self._user_repo.get_by_telegram_id(telegram_id)

        if user:
            # Update last active
            await self._user_repo.update_last_active(telegram_id)

            # Update user info if changed
            if username != user.username or first_name != user.first_name:
                await self._user_repo.update(
                    telegram_id,
                    UserUpdate(
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                    ),
                )

            # Cache user
            await self._cache.set(cache_key, user.__dict__, ttl=300)

            return user, False

        # Validate referrer
        valid_referrer_id = None
        if referrer_id and referrer_id != telegram_id:
            referrer = await self._user_repo.get_by_telegram_id(referrer_id)
            if referrer and not referrer.is_banned:
                valid_referrer_id = referrer_id

        # Create new user
        user_data = UserCreate(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            referrer_id=valid_referrer_id,
            trial_remaining=self._trial_generations,
        )

        user = await self._user_repo.create(user_data)

        logger.info(
            "New user created",
            telegram_id=telegram_id,
            referrer_id=valid_referrer_id,
        )

        return user, True


class GetUserProfileUseCase:
    """Get user profile with balance and stats."""

    def __init__(
        self,
        user_repo: IUserRepository,
        ledger_repo: ILedgerRepository,
        cache: ICacheService,
    ):
        self._user_repo = user_repo
        self._ledger_repo = ledger_repo
        self._cache = cache

    async def execute(self, telegram_id: int) -> Optional[UserProfileDTO]:
        """Execute use case."""
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return None

        # Get balance
        balance = await self._ledger_repo.get_balance(telegram_id)

        # Get referral count
        referral_count = await self._user_repo.count_referrals(telegram_id)

        # Get generation count (from cache or compute)
        gen_cache_key = f"user_gen_count:{telegram_id}"
        generation_count = await self._cache.get(gen_cache_key)
        if generation_count is None:
            # This would require generation repository
            generation_count = 0
            await self._cache.set(gen_cache_key, generation_count, ttl=60)

        return UserProfileDTO(
            user=user,
            balance=balance,
            referral_count=referral_count,
            generation_count=generation_count,
        )


class UpdateUserUseCase:
    """Update user information."""

    def __init__(
        self,
        user_repo: IUserRepository,
        cache: ICacheService,
    ):
        self._user_repo = user_repo
        self._cache = cache

    async def execute(
        self,
        telegram_id: int,
        update_data: UserUpdate,
    ) -> Optional[User]:
        """Execute use case."""
        user = await self._user_repo.update(telegram_id, update_data)

        if user:
            # Invalidate cache
            await self._cache.delete(f"user:{telegram_id}")

            logger.info("User updated", telegram_id=telegram_id)

        return user


class BanUserUseCase:
    """Ban or unban user."""

    def __init__(
        self,
        user_repo: IUserRepository,
        cache: ICacheService,
    ):
        self._user_repo = user_repo
        self._cache = cache

    async def execute(
        self,
        telegram_id: int,
        ban: bool,
        reason: Optional[str] = None,
    ) -> bool:
        """Execute use case."""
        if ban:
            success = await self._user_repo.ban_user(telegram_id, reason)
            action = "banned"
        else:
            success = await self._user_repo.unban_user(telegram_id)
            action = "unbanned"

        if success:
            # Invalidate cache
            await self._cache.delete(f"user:{telegram_id}")

            logger.info(
                f"User {action}",
                telegram_id=telegram_id,
                reason=reason,
            )

        return success


class SearchUsersUseCase:
    """Search users with filters."""

    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    async def execute(
        self,
        query: Optional[str] = None,
        is_banned: Optional[bool] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[User]:
        """Execute use case."""
        return await self._user_repo.search(
            query_str=query,
            is_banned=is_banned,
            offset=offset,
            limit=limit,
        )
