"""Async database connection and session management for the API."""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    """Base class for all database models with common fields."""
    
    # Common fields for all models
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# Global engine and session factory (initialized lazily)
_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker] = None


def get_async_database_url(database_url: str) -> str:
    """Convert sync database URL to async URL for asyncpg."""
    return database_url.replace(
        "postgresql://", "postgresql+asyncpg://"
    ).replace(
        "postgres://", "postgresql+asyncpg://"
    )


def init_engine(
    database_url: str,
    echo: bool = False,
    pool_size: int = 10,
    max_overflow: int = 20
) -> AsyncEngine:
    """
    Initialize the async database engine.
    
    Args:
        database_url: PostgreSQL connection URL
        echo: Whether to log SQL queries
        pool_size: Number of connections to maintain in the pool
        max_overflow: Maximum number of connections beyond pool_size
    
    Returns:
        AsyncEngine instance
    """
    global _engine, _async_session_factory
    
    if _engine is None:
        async_url = get_async_database_url(database_url)
        _engine = create_async_engine(
            async_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before using
        )
        
        _async_session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    
    return _engine


def get_engine() -> AsyncEngine:
    """Get the database engine, initializing if necessary."""
    global _engine
    if _engine is None:
        from api.config import settings
        init_engine(
            settings.database_url,
            settings.database_echo,
            settings.database_pool_size,
            settings.database_max_overflow
        )
    return _engine


def get_session_factory() -> async_sessionmaker:
    """Get the async session factory, initializing if necessary."""
    global _async_session_factory
    if _async_session_factory is None:
        get_engine()  # This will initialize both engine and factory
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Usage in FastAPI:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    
    Note: In production, use Alembic migrations instead.
    This is useful for development and testing.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
