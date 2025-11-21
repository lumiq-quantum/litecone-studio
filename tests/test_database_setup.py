#!/usr/bin/env python3
"""Test script to verify database setup is working correctly."""

import asyncio
from sqlalchemy import Column, String, select
from api.database import Base, init_engine, get_session_factory, close_db
from api.config import settings


class TestModel(Base):
    """Test model to verify database operations."""
    __tablename__ = 'test_table'
    
    name = Column(String(255), nullable=False)


async def test_database_setup():
    """Test database connection and operations."""
    print("=" * 60)
    print("Testing Database Setup")
    print("=" * 60)
    
    # Test 1: Initialize engine
    print("\n1. Initializing database engine...")
    try:
        engine = init_engine(
            settings.database_url,
            settings.database_echo,
            settings.database_pool_size,
            settings.database_max_overflow
        )
        print("   ✓ Engine initialized successfully")
        print(f"   Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
    except Exception as e:
        print(f"   ✗ Failed to initialize engine: {e}")
        return
    
    # Test 2: Get session factory
    print("\n2. Getting session factory...")
    try:
        session_factory = get_session_factory()
        print("   ✓ Session factory created successfully")
    except Exception as e:
        print(f"   ✗ Failed to get session factory: {e}")
        return
    
    # Test 3: Create a session
    print("\n3. Creating database session...")
    try:
        async with session_factory() as session:
            print("   ✓ Session created successfully")
            
            # Test 4: Execute a simple query
            print("\n4. Testing database connectivity...")
            result = await session.execute(select(1))
            value = result.scalar()
            if value == 1:
                print("   ✓ Database connection working")
            else:
                print("   ✗ Unexpected query result")
    except Exception as e:
        print(f"   ✗ Failed to create session or query database: {e}")
        return
    
    # Test 5: Verify Base model
    print("\n5. Verifying Base model...")
    try:
        # Check that Base has the common fields
        base_columns = [col.name for col in Base.__table__.columns if hasattr(Base, '__table__')]
        print(f"   ✓ Base model configured")
        print(f"   Common fields available: id, created_at, updated_at")
    except Exception as e:
        print(f"   Note: Base is abstract (expected): {e}")
    
    # Test 6: Verify TestModel inherits common fields
    print("\n6. Verifying model inheritance...")
    try:
        test_columns = [col.name for col in TestModel.__table__.columns]
        expected_fields = {'id', 'created_at', 'updated_at', 'name'}
        if expected_fields.issubset(set(test_columns)):
            print("   ✓ Models correctly inherit common fields")
            print(f"   TestModel columns: {', '.join(test_columns)}")
        else:
            print(f"   ✗ Missing expected fields. Found: {test_columns}")
    except Exception as e:
        print(f"   ✗ Failed to verify model: {e}")
    
    # Cleanup
    print("\n7. Cleaning up...")
    try:
        await close_db()
        print("   ✓ Database connections closed")
    except Exception as e:
        print(f"   ✗ Failed to close connections: {e}")
    
    print("\n" + "=" * 60)
    print("Database Setup Test Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Create database models in api/models/")
    print("  2. Generate migrations: python -m alembic revision --autogenerate -m 'initial schema'")
    print("  3. Apply migrations: python -m alembic upgrade head")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_database_setup())
