"""Database connection factory and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from src.database.models import Base


class DatabaseConnection:
    """Database connection factory with connection pooling."""
    
    def __init__(self, database_url: str, pool_size: int = 10, max_overflow: int = 20):
        """
        Initialize database connection factory.
        
        Args:
            database_url: PostgreSQL connection URL
            pool_size: Number of connections to maintain in the pool
            max_overflow: Maximum number of connections to create beyond pool_size
        """
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL query logging
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self) -> None:
        """Create all database tables if they don't exist."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self) -> None:
        """Drop all database tables. Use with caution!"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy Session instance
        """
        return self.SessionLocal()
    
    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[Session, None]:
        """
        Provide a transactional scope for database operations.
        
        Usage:
            async with db.session_scope() as session:
                # perform database operations
                session.add(obj)
        
        Yields:
            SQLAlchemy Session instance
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self) -> None:
        """Close the database engine and all connections."""
        self.engine.dispose()


def init_database(database_url: str) -> DatabaseConnection:
    """
    Initialize database connection and create tables.
    
    Args:
        database_url: PostgreSQL connection URL
    
    Returns:
        DatabaseConnection instance
    """
    db = DatabaseConnection(database_url)
    db.create_tables()
    return db
