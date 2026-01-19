"""User repository implementation."""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional, Sequence

from sqlalchemy import String, and_, cast, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User, UserCreate, UserUpdate
from app.domain.interfaces.repositories import IUserRepository
from app.infrastructure.database.models import LedgerEntryModel, UserModel
from app.infrastructure.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserModel], IUserRepository):
    """User repository implementation."""

    model = UserModel

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _to_entity(self, model: UserModel) -> User:
        """Convert ORM model to domain entity."""
        return User(
            telegram_id=model.telegram_id,
            username=model.username,
            first_name=model.first_name,
            last_name=model.last_name,
            language_code=model.language_code,
            is_active=model.is_active,
            is_banned=model.is_banned,
            ban_reason=model.ban_reason,
            trial_remaining=model.trial_remaining,
            referrer_id=model.referrer_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_active_at=model.last_active_at,
        )

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        query = select(UserModel).where(UserModel.telegram_id == telegram_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = select(UserModel).where(UserModel.username == username)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, user_data: UserCreate) -> User:
        """Create new user."""
        model = UserModel(
            telegram_id=user_data.telegram_id,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            language_code=user_data.language_code,
            referrer_id=user_data.referrer_id,
            trial_remaining=user_data.trial_remaining,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def update(self, telegram_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user data."""
        query = select(UserModel).where(UserModel.telegram_id == telegram_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            return None

        update_data = user_data.to_dict()
        for key, value in update_data.items():
            setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def update_last_active(self, telegram_id: int) -> None:
        """Update last active timestamp."""
        query = (
            update(UserModel)
            .where(UserModel.telegram_id == telegram_id)
            .values(last_active_at=datetime.utcnow())
        )
        await self.session.execute(query)

    async def get_balance(self, telegram_id: int) -> Decimal:
        """Get user's current balance."""
        query = select(func.coalesce(func.sum(LedgerEntryModel.amount), Decimal("0"))).where(
            LedgerEntryModel.telegram_id == telegram_id
        )
        result = await self.session.execute(query)
        return result.scalar() or Decimal("0")

    async def ban_user(self, telegram_id: int, reason: Optional[str] = None) -> bool:
        """Ban user."""
        query = (
            update(UserModel)
            .where(UserModel.telegram_id == telegram_id)
            .values(is_banned=True, ban_reason=reason, updated_at=datetime.utcnow())
        )
        result = await self.session.execute(query)
        return result.rowcount > 0

    async def unban_user(self, telegram_id: int) -> bool:
        """Unban user."""
        query = (
            update(UserModel)
            .where(UserModel.telegram_id == telegram_id)
            .values(is_banned=False, ban_reason=None, updated_at=datetime.utcnow())
        )
        result = await self.session.execute(query)
        return result.rowcount > 0

    async def search(
        self,
        query_str: Optional[str] = None,
        is_banned: Optional[bool] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[User]:
        """Search users with filters."""
        query = select(UserModel)

        conditions = []
        if query_str:
            search_pattern = f"%{query_str}%"
            conditions.append(
                or_(
                    UserModel.username.ilike(search_pattern),
                    UserModel.first_name.ilike(search_pattern),
                    UserModel.last_name.ilike(search_pattern),
                    cast(UserModel.telegram_id, String).like(search_pattern),
                )
            )

        if is_banned is not None:
            conditions.append(UserModel.is_banned == is_banned)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(UserModel.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_total(self) -> int:
        """Count total users."""
        query = select(func.count()).select_from(UserModel)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_active(self, days: int = 7) -> int:
        """Count active users in last N days."""
        since = datetime.utcnow() - timedelta(days=days)
        query = select(func.count()).select_from(UserModel).where(
            UserModel.last_active_at >= since
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_new_today(self) -> int:
        """Count new users today."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        query = select(func.count()).select_from(UserModel).where(
            UserModel.created_at >= today
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_referrals(
        self,
        telegram_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[User]:
        """Get user's referrals."""
        query = (
            select(UserModel)
            .where(UserModel.referrer_id == telegram_id)
            .order_by(UserModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_referrals(self, telegram_id: int) -> int:
        """Count user's referrals."""
        query = select(func.count()).select_from(UserModel).where(
            UserModel.referrer_id == telegram_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get user statistics."""
        total = await self.count_total()
        active_7d = await self.count_active(7)
        active_30d = await self.count_active(30)
        new_today = await self.count_new_today()

        banned_query = select(func.count()).select_from(UserModel).where(
            UserModel.is_banned == True
        )
        banned_result = await self.session.execute(banned_query)
        banned = banned_result.scalar() or 0

        return {
            "total_users": total,
            "active_7d": active_7d,
            "active_30d": active_30d,
            "new_today": new_today,
            "banned_users": banned,
        }

    # Interface required methods
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID (alias for telegram_id)."""
        return await self.get_by_telegram_id(user_id)

    async def get_by_referral_code(self, referral_code: str) -> Optional[User]:
        """Get user by referral code."""
        # Referral code is telegram_id based
        try:
            telegram_id = int(referral_code)
            return await self.get_by_telegram_id(telegram_id)
        except ValueError:
            return None

    async def get_list(
        self,
        offset: int = 0,
        limit: int = 50,
        is_banned: Optional[bool] = None,
    ) -> tuple[Sequence[User], int]:
        """Get paginated users list with total count."""
        users = await self.search(
            query_str=None,
            is_banned=is_banned,
            offset=offset,
            limit=limit,
        )
        total = await self.count_total()
        return users, total

    async def get_total_count(self) -> int:
        """Get total users count."""
        return await self.count_total()

    async def get_all_telegram_ids(self) -> Sequence[int]:
        """Get all active user telegram IDs (for broadcast)."""
        query = select(UserModel.telegram_id).where(
            and_(
                UserModel.is_active == True,
                UserModel.is_banned == False,
            )
        )
        result = await self.session.execute(query)
        return [r for r in result.scalars().all()]
