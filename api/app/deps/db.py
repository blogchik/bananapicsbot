"""Database dependencies."""
from collections.abc import Generator, AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.infrastructure.database.session import Database
from app.core.config import get_settings


# Sync session dependency (for Alembic compatibility)
def db_session_dep() -> Generator[Session, None, None]:
    """Sync database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Async database session dependency."""
    async with Database.session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# Type alias for dependency injection
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
SyncSessionDep = Annotated[Session, Depends(db_session_dep)]


async def init_database() -> None:
    """Initialize database connection (no-op, engine created lazily)."""
    # Force engine creation
    Database.get_engine()


async def shutdown_database() -> None:
    """Shutdown database connection."""
    await Database.close()

