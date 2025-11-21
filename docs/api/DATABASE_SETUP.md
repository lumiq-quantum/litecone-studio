# Database Setup Documentation

This document describes the database configuration and migration setup for the Workflow Management API.

## Overview

The API uses:
- **SQLAlchemy 2.0+** with async support
- **Alembic** for database migrations
- **asyncpg** as the PostgreSQL driver
- **PostgreSQL 15+** as the database

## Files Created

### 1. `api/database.py`

Main database module providing:

- **Base**: Declarative base class with common fields (id, created_at, updated_at)
- **init_engine()**: Initialize async database engine
- **get_db()**: FastAPI dependency for database sessions
- **init_db()**: Initialize database tables (for development/testing)
- **close_db()**: Close database connections

Key features:
- Lazy initialization to avoid import-time side effects
- Async/await support throughout
- Connection pooling with configurable pool size
- Automatic session management with commit/rollback

### 2. `alembic.ini`

Alembic configuration file with:
- Script location pointing to `api/migrations`
- Database URL loaded from environment variables
- Logging configuration

### 3. `api/migrations/env.py`

Alembic environment configuration with:
- Async migration support using asyncpg
- Automatic database URL conversion (postgresql:// → postgresql+asyncpg://)
- Integration with Base metadata for autogenerate
- Both online and offline migration modes

### 4. `api/migrations/README.md`

Comprehensive documentation covering:
- Common Alembic commands
- Migration best practices
- Troubleshooting guide
- Example migrations

## Base Model

All database models should inherit from `Base` to get common fields:

```python
from api.database import Base
from sqlalchemy import Column, String

class MyModel(Base):
    __tablename__ = 'my_table'
    
    name = Column(String(255), nullable=False)
    # id, created_at, updated_at are inherited from Base
```

## Usage in FastAPI

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.database import get_db

@app.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

## Creating Migrations

```bash
# Auto-generate migration from model changes
python -m alembic revision --autogenerate -m "add agents table"

# Apply migrations
python -m alembic upgrade head

# Rollback one migration
python -m alembic downgrade -1
```

## Configuration

Database settings are loaded from `.env.api`:

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/workflow_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_ECHO=false
```

## Dependencies Installed

The following packages are required (already in `api/requirements.txt`):

- sqlalchemy==2.0.23
- alembic==1.12.1
- asyncpg==0.29.0
- psycopg2-binary==2.9.9
- greenlet (for async support)

## Next Steps

1. Create database models in `api/models/` (agents, workflows, runs, audit logs)
2. Generate initial migration with all tables
3. Apply migrations to development database
4. Implement repositories using the async session
