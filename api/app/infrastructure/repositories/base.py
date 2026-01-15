"""Base repository with common functionality."""
from typing import TypeVar, Generic, Type, Optional, Sequence, Any
from datetime import datetime

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Base repository with CRUD operations."""
    
    model: Type[ModelType]
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Get entity by ID."""
        return await self.session.get(self.model, id)
    
    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        """Get all entities with pagination."""
        query = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count(self) -> int:
        """Count all entities."""
        query = select(func.count()).select_from(self.model)
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def create(self, entity: ModelType) -> ModelType:
        """Create new entity."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, entity: ModelType) -> ModelType:
        """Update existing entity."""
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, entity: ModelType) -> None:
        """Delete entity."""
        await self.session.delete(entity)
        await self.session.flush()
    
    async def delete_by_id(self, id: Any) -> bool:
        """Delete entity by ID."""
        entity = await self.get_by_id(id)
        if entity:
            await self.delete(entity)
            return True
        return False
