"""Broadcast repository implementation."""
from typing import Optional, Sequence, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.broadcast import Broadcast, BroadcastStatus, BroadcastContentType
from app.domain.interfaces.repositories import IBroadcastRepository
from app.infrastructure.database.models import BroadcastModel
from app.infrastructure.repositories.base import BaseRepository


class BroadcastRepository(BaseRepository[BroadcastModel], IBroadcastRepository):
    """Broadcast repository implementation."""
    
    model = BroadcastModel
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    def _to_entity(self, model: BroadcastModel) -> Broadcast:
        """Convert ORM model to domain entity."""
        return Broadcast(
            id=model.id,
            admin_id=model.admin_id,
            content_type=BroadcastContentType(model.content_type),
            content=model.content,
            media_file_id=model.media_file_id,
            status=BroadcastStatus(model.status),
            total_recipients=model.total_recipients,
            sent_count=model.sent_count,
            failed_count=model.failed_count,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
        )
    
    async def create(
        self,
        admin_id: int,
        content_type: BroadcastContentType,
        content: str,
        media_file_id: Optional[str] = None,
        total_recipients: int = 0,
    ) -> Broadcast:
        """Create broadcast record."""
        model = BroadcastModel(
            admin_id=admin_id,
            content_type=content_type.value,
            content=content,
            media_file_id=media_file_id,
            status=BroadcastStatus.PENDING.value,
            total_recipients=total_recipients,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)
    
    async def get_by_id(self, broadcast_id: UUID) -> Optional[Broadcast]:
        """Get broadcast by ID."""
        query = select(BroadcastModel).where(BroadcastModel.id == broadcast_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def update_status(
        self,
        broadcast_id: UUID,
        status: BroadcastStatus,
    ) -> bool:
        """Update broadcast status."""
        values: Dict[str, Any] = {"status": status.value}
        
        if status == BroadcastStatus.SENDING:
            values["started_at"] = datetime.utcnow()
        elif status in (BroadcastStatus.COMPLETED, BroadcastStatus.FAILED, BroadcastStatus.CANCELLED):
            values["completed_at"] = datetime.utcnow()
        
        query = (
            update(BroadcastModel)
            .where(BroadcastModel.id == broadcast_id)
            .values(**values)
        )
        result = await self.session.execute(query)
        return result.rowcount > 0
    
    async def update_progress(
        self,
        broadcast_id: UUID,
        sent_count: int,
        failed_count: int,
    ) -> bool:
        """Update broadcast progress."""
        query = (
            update(BroadcastModel)
            .where(BroadcastModel.id == broadcast_id)
            .values(sent_count=sent_count, failed_count=failed_count)
        )
        result = await self.session.execute(query)
        return result.rowcount > 0
    
    async def increment_sent(self, broadcast_id: UUID) -> bool:
        """Increment sent count."""
        query = (
            update(BroadcastModel)
            .where(BroadcastModel.id == broadcast_id)
            .values(sent_count=BroadcastModel.sent_count + 1)
        )
        result = await self.session.execute(query)
        return result.rowcount > 0
    
    async def increment_failed(self, broadcast_id: UUID) -> bool:
        """Increment failed count."""
        query = (
            update(BroadcastModel)
            .where(BroadcastModel.id == broadcast_id)
            .values(failed_count=BroadcastModel.failed_count + 1)
        )
        result = await self.session.execute(query)
        return result.rowcount > 0
    
    async def get_all(
        self,
        status: Optional[BroadcastStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Broadcast]:
        """Get all broadcasts."""
        query = select(BroadcastModel)
        
        if status:
            query = query.where(BroadcastModel.status == status.value)
        
        query = (
            query.order_by(BroadcastModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]
    
    async def get_pending_broadcasts(self) -> Sequence[Broadcast]:
        """Get pending broadcasts for processing."""
        query = (
            select(BroadcastModel)
            .where(BroadcastModel.status == BroadcastStatus.PENDING.value)
            .order_by(BroadcastModel.created_at.asc())
        )
        result = await self.session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]
    
    async def cancel(self, broadcast_id: UUID) -> bool:
        """Cancel broadcast."""
        return await self.update_status(broadcast_id, BroadcastStatus.CANCELLED)
