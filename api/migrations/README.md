# Database Migrations

This directory contains Alembic database migrations for the Workflow Management API.

## Overview

Alembic is used to manage database schema changes in a version-controlled manner. Each migration represents a specific change to the database schema.

## Configuration

- **alembic.ini**: Main configuration file (located in project root)
- **env.py**: Migration environment configuration with async support
- **versions/**: Directory containing migration scripts

## Common Commands

### Create a new migration

```bash
# Auto-generate migration from model changes
python -m alembic revision --autogenerate -m "description of changes"

# Create empty migration
python -m alembic revision -m "description of changes"
```

### Apply migrations

```bash
# Upgrade to latest version
python -m alembic upgrade head

# Upgrade to specific version
python -m alembic upgrade <revision>

# Upgrade by one version
python -m alembic upgrade +1
```

### Rollback migrations

```bash
# Downgrade by one version
python -m alembic downgrade -1

# Downgrade to specific version
python -m alembic downgrade <revision>

# Downgrade all
python -m alembic downgrade base
```

### View migration history

```bash
# Show current version
python -m alembic current

# Show migration history
python -m alembic history

# Show pending migrations
python -m alembic history --verbose
```

## Migration Best Practices

1. **Always review auto-generated migrations** - Alembic's autogenerate is helpful but not perfect
2. **Test migrations both up and down** - Ensure both upgrade and downgrade work correctly
3. **Use descriptive names** - Make migration names clear and specific
4. **One logical change per migration** - Keep migrations focused and atomic
5. **Add data migrations when needed** - Use `op.execute()` for data changes
6. **Never edit applied migrations** - Create a new migration to fix issues

## Async Support

This project uses async SQLAlchemy with asyncpg. The `env.py` file is configured to support async migrations:

- Database URL is automatically converted to use `postgresql+asyncpg://`
- Migrations run in an async context
- All database operations use async/await

## Environment Variables

The migration system reads the database URL from environment variables:

- `DATABASE_URL`: PostgreSQL connection string (loaded from `.env.api`)

## Example Migration

```python
"""add user table

Revision ID: abc123
Revises: def456
Create Date: 2024-01-01 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)

def downgrade() -> None:
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
```

## Troubleshooting

### Migration fails with "Target database is not up to date"

```bash
# Check current version
python -m alembic current

# Stamp database with current version
python -m alembic stamp head
```

### Need to reset migrations

```bash
# Downgrade all migrations
python -m alembic downgrade base

# Re-apply all migrations
python -m alembic upgrade head
```

### Autogenerate doesn't detect changes

- Ensure models are imported in `env.py`
- Check that `target_metadata` is set correctly
- Verify database connection is working
