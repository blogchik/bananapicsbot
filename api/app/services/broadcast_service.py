"""Broadcast service for managing broadcasts."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Broadcast,
    BroadcastRecipient,
    BroadcastStatus,
    LedgerEntry,
    User,
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class BroadcastService:
    """Service for broadcast management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_broadcast(
        self,
        admin_id: int,
        content_type: str,
        text: Optional[str] = None,
        media_file_id: Optional[str] = None,
        inline_button_text: Optional[str] = None,
        inline_button_url: Optional[str] = None,
        filter_type: str = "all",
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> Broadcast:
        """Create a new broadcast in pending state."""
        public_id = str(uuid.uuid4())[:8]

        # Get user count for this filter
        total_users = await self.get_filtered_users_count(filter_type, filter_params)

        broadcast = Broadcast(
            public_id=public_id,
            admin_id=admin_id,
            content_type=content_type,
            text=text,
            media_file_id=media_file_id,
            inline_button_text=inline_button_text,
            inline_button_url=inline_button_url,
            filter_type=filter_type,
            filter_params=filter_params,
            status=BroadcastStatus.pending,
            total_users=total_users,
            sent_count=0,
            failed_count=0,
            blocked_count=0,
        )

        self.session.add(broadcast)
        await self.session.commit()
        await self.session.refresh(broadcast)

        logger.info(
            "Created broadcast",
            public_id=public_id,
            admin_id=admin_id,
            content_type=content_type,
            filter_type=filter_type,
            total_users=total_users,
        )

        return broadcast

    async def get_broadcast_by_public_id(self, public_id: str) -> Optional[Broadcast]:
        """Get broadcast by public ID."""
        result = await self.session.execute(select(Broadcast).where(Broadcast.public_id == public_id))
        return result.scalar_one_or_none()

    async def get_broadcast_by_id(self, broadcast_id: int) -> Optional[Broadcast]:
        """Get broadcast by internal ID."""
        result = await self.session.execute(select(Broadcast).where(Broadcast.id == broadcast_id))
        return result.scalar_one_or_none()

    async def list_broadcasts(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Broadcast]:
        """List broadcasts, newest first."""
        result = await self.session.execute(
            select(Broadcast).order_by(Broadcast.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def get_filtered_users_count(
        self,
        filter_type: str,
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Get count of users matching the filter."""
        query = select(func.count(User.id))

        now = datetime.utcnow()

        if filter_type == "all":
            # All users (not banned)
            query = query.where(User.is_banned == False)

        elif filter_type == "active_7d":
            # Active in last 7 days
            cutoff = now - timedelta(days=7)
            query = query.where(
                and_(
                    User.is_banned == False,
                    User.last_active_at >= cutoff,
                )
            )

        elif filter_type == "active_30d":
            # Active in last 30 days
            cutoff = now - timedelta(days=30)
            query = query.where(
                and_(
                    User.is_banned == False,
                    User.last_active_at >= cutoff,
                )
            )

        elif filter_type == "with_balance":
            # Users with positive balance
            balance_subquery = (
                select(LedgerEntry.user_id, func.sum(LedgerEntry.amount).label("balance"))
                .group_by(LedgerEntry.user_id)
                .having(func.sum(LedgerEntry.amount) > 0)
                .subquery()
            )
            query = (
                select(func.count(User.id))
                .join(balance_subquery, User.id == balance_subquery.c.user_id)
                .where(User.is_banned == False)
            )

        elif filter_type == "paid_users":
            # Users who ever made a payment
            paid_subquery = select(LedgerEntry.user_id).where(LedgerEntry.entry_type == "deposit").distinct().subquery()
            query = (
                select(func.count(User.id))
                .join(paid_subquery, User.id == paid_subquery.c.user_id)
                .where(User.is_banned == False)
            )

        elif filter_type == "new_users":
            # Users registered in last 7 days
            cutoff = now - timedelta(days=7)
            query = query.where(
                and_(
                    User.is_banned == False,
                    User.created_at >= cutoff,
                )
            )

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_filtered_user_ids(
        self,
        filter_type: str,
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> List[int]:
        """Get telegram IDs of users matching the filter."""
        query = select(User.telegram_id)

        now = datetime.utcnow()

        if filter_type == "all":
            query = query.where(User.is_banned == False)

        elif filter_type == "active_7d":
            cutoff = now - timedelta(days=7)
            query = query.where(
                and_(
                    User.is_banned == False,
                    User.last_active_at >= cutoff,
                )
            )

        elif filter_type == "active_30d":
            cutoff = now - timedelta(days=30)
            query = query.where(
                and_(
                    User.is_banned == False,
                    User.last_active_at >= cutoff,
                )
            )

        elif filter_type == "with_balance":
            balance_subquery = (
                select(LedgerEntry.user_id, func.sum(LedgerEntry.amount).label("balance"))
                .group_by(LedgerEntry.user_id)
                .having(func.sum(LedgerEntry.amount) > 0)
                .subquery()
            )
            query = (
                select(User.telegram_id)
                .join(balance_subquery, User.id == balance_subquery.c.user_id)
                .where(User.is_banned == False)
            )

        elif filter_type == "paid_users":
            paid_subquery = select(LedgerEntry.user_id).where(LedgerEntry.entry_type == "deposit").distinct().subquery()
            query = (
                select(User.telegram_id)
                .join(paid_subquery, User.id == paid_subquery.c.user_id)
                .where(User.is_banned == False)
            )

        elif filter_type == "new_users":
            cutoff = now - timedelta(days=7)
            query = query.where(
                and_(
                    User.is_banned == False,
                    User.created_at >= cutoff,
                )
            )

        result = await self.session.execute(query)
        return [row[0] for row in result.fetchall()]

    async def update_broadcast_status(
        self,
        broadcast_id: int,
        status: BroadcastStatus,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ):
        """Update broadcast status."""
        broadcast = await self.get_broadcast_by_id(broadcast_id)
        if not broadcast:
            return

        broadcast.status = status
        if started_at:
            broadcast.started_at = started_at
        if completed_at:
            broadcast.completed_at = completed_at

        await self.session.commit()

    async def increment_broadcast_counter(
        self,
        broadcast_id: int,
        counter: str,
        amount: int = 1,
    ):
        """Increment a broadcast counter (sent_count, failed_count, blocked_count)."""
        broadcast = await self.get_broadcast_by_id(broadcast_id)
        if not broadcast:
            return

        if counter == "sent":
            broadcast.sent_count = (broadcast.sent_count or 0) + amount
        elif counter == "failed":
            broadcast.failed_count = (broadcast.failed_count or 0) + amount
        elif counter == "blocked":
            broadcast.blocked_count = (broadcast.blocked_count or 0) + amount

        await self.session.commit()

    async def cancel_broadcast(self, broadcast_id: int):
        """Cancel a broadcast."""
        broadcast = await self.get_broadcast_by_id(broadcast_id)
        if not broadcast:
            return

        broadcast.status = BroadcastStatus.cancelled
        broadcast.completed_at = datetime.utcnow()

        await self.session.commit()

        logger.info("Broadcast cancelled", broadcast_id=broadcast_id)

    async def add_recipient(
        self,
        broadcast_id: int,
        telegram_id: int,
        status: str = "pending",
        error: Optional[str] = None,
    ):
        """Add or update a recipient record."""
        recipient = BroadcastRecipient(
            broadcast_id=broadcast_id,
            telegram_id=telegram_id,
            status=status,
            error=error,
            sent_at=datetime.utcnow() if status != "pending" else None,
        )
        self.session.add(recipient)
        await self.session.commit()
