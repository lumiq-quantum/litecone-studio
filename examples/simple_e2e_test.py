#!/usr/bin/env python3
"""
Simplified End-to-End Test

A simpler version that tests the workflow execution without requiring
the full Docker Compose setup. This can be run with just Kafka and PostgreSQL.
"""

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.executor.centralized_executor import CentralizedExecutor
from src.models.workflow import WorkflowPlan
from src.database.connection import init_database


async def run_simple_test():
    """Run a simplified end-to-end test"""
    print("=" * 60)
    print("Simplified End-to-End Test")
    print("=" * 60)
    
    # Load workflow plan
    print("\nLoading workflow plan...")
    with open('examples/sample_workflow.json', 'r') as f:
        workflow_data = json.load(f)
    
    # Load workflow input
    print("Loading workflow input...")
    with open('examples/sample_workflow_input.json', 'r') as f:
        workflow_input = json.load(f)
    
    # Generate run ID
    run_id = f"test-{uuid.uuid4()}"
    print(f"\nRun ID: {run_id}")
    
    # Initialize database
    print("\nInitializing database...")
    await init_database()
    
    # Create workflow plan object
    workflow_plan = WorkflowPlan(**workflow_data)
    
    # Create executor
    print("\nCreating executor...")
    executor = CentralizedExecutor(run_id, workflow_plan)
    
    try:
        # Initialize executor
        print("Initializing executor...")
        await executor.initialize()
        
        # Execute workflow
        print("\nExecuting workflow...")
        print(f"Workflow: {workflow_plan.name} (v{workflow_plan.version})")
        print(f"Input: {json.dumps(workflow_input, indent=2)}")
        
        await executor.execute_workflow(workflow_input)
        
        print("\n" + "=" * 60)
        print("✓ WORKFLOW EXECUTION COMPLETED")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        print("\nCleaning up...")
        await executor.shutdown()


def main():
    """Main entry point"""
    try:
        success = asyncio.run(run_simple_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)


if __name__ == '__main__':
    main()
