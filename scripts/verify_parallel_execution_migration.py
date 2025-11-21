#!/usr/bin/env python3
"""
Verify that the parallel execution migration was applied successfully.
"""

import os
import sys
from sqlalchemy import create_engine, inspect

def verify_migration():
    """Verify the parallel execution columns exist."""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL', 'postgresql://workflow_user:workflow_pass@localhost:5432/workflow_db')
    
    print(f"Connecting to database: {database_url.split('@')[1]}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        # Check if step_executions table exists
        if 'step_executions' not in inspector.get_table_names():
            print("❌ ERROR: step_executions table not found")
            return False
        
        print("✅ step_executions table exists")
        
        # Get columns
        columns = {col['name']: col for col in inspector.get_columns('step_executions')}
        
        # Check for new columns
        required_columns = ['parent_step_id', 'branch_name', 'join_policy']
        
        for col_name in required_columns:
            if col_name in columns:
                col = columns[col_name]
                print(f"✅ Column '{col_name}' exists (type: {col['type']}, nullable: {col['nullable']})")
            else:
                print(f"❌ ERROR: Column '{col_name}' not found")
                return False
        
        # Check for index
        indexes = inspector.get_indexes('step_executions')
        index_names = [idx['name'] for idx in indexes]
        
        if 'idx_step_branch' in index_names:
            print("✅ Index 'idx_step_branch' exists")
        else:
            print("❌ WARNING: Index 'idx_step_branch' not found")
        
        print("\n✅ Migration verification successful!")
        print("\nParallel execution columns:")
        print("  - parent_step_id: For tracking parallel/fork-join parent steps")
        print("  - branch_name: For fork-join branch identification")
        print("  - join_policy: For fork-join policy (ALL, ANY, MAJORITY, N_OF_M)")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == '__main__':
    success = verify_migration()
    sys.exit(0 if success else 1)
