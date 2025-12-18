#!/usr/bin/env python3
"""
Debug script to inspect step outputs and available fields.
This helps identify what fields are actually available for input mapping.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.database import get_db, init_engine
from api.config import settings
from sqlalchemy import text


async def debug_step_outputs(run_id: str = None):
    """Debug step outputs for a specific run or the latest run."""
    
    # Initialize database
    init_engine(
        settings.database_url,
        settings.database_echo,
        settings.database_pool_size,
        settings.database_max_overflow
    )
    
    async for db in get_db():
        try:
            if run_id:
                # Get specific run
                query = """
                SELECT run_id, step_id, agent_name, status, input_data, output_data, started_at
                FROM step_executions 
                WHERE run_id = :run_id
                ORDER BY started_at ASC
                """
                result = await db.execute(text(query), {"run_id": run_id})
            else:
                # Get latest run
                query = """
                SELECT run_id, step_id, agent_name, status, input_data, output_data, started_at
                FROM step_executions 
                WHERE run_id = (
                    SELECT run_id FROM step_executions 
                    ORDER BY started_at DESC 
                    LIMIT 1
                )
                ORDER BY started_at ASC
                """
                result = await db.execute(text(query))
            
            rows = result.fetchall()
            
            if not rows:
                print("❌ No step executions found")
                if run_id:
                    print(f"   Run ID: {run_id}")
                return
            
            current_run_id = rows[0].run_id
            print(f"🔍 Debugging Step Outputs for Run: {current_run_id}")
            print("=" * 80)
            
            for row in rows:
                print(f"\n📋 Step: {row.step_id}")
                print(f"   Agent: {row.agent_name}")
                print(f"   Status: {row.status}")
                print(f"   Created: {row.created_at}")
                
                print(f"\n📥 Input Data:")
                if row.input_data:
                    print(json.dumps(row.input_data, indent=2))
                else:
                    print("   (No input data)")
                
                print(f"\n📤 Output Data:")
                if row.output_data:
                    output = row.output_data
                    print(json.dumps(output, indent=2))
                    
                    # Show available fields for input mapping
                    print(f"\n🔑 Available Fields for Input Mapping:")
                    if isinstance(output, dict):
                        for key in output.keys():
                            print(f"   ${{{row.step_id}.output.{key}}}")
                    else:
                        print(f"   Output is not a dictionary: {type(output)}")
                else:
                    print("   (No output data)")
                
                print("-" * 60)
            
            # Show example input mapping
            print(f"\n💡 Example Input Mapping for Next Step:")
            if rows:
                last_step = rows[-1]
                if last_step.output_data and isinstance(last_step.output_data, dict):
                    print("   {")
                    for key in last_step.output_data.keys():
                        print(f'     "{key}": "${{{last_step.step_id}.output.{key}}}",')
                    print("   }")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            break


async def list_recent_runs():
    """List recent workflow runs."""
    
    # Initialize database
    init_engine(
        settings.database_url,
        settings.database_echo,
        settings.database_pool_size,
        settings.database_max_overflow
    )
    
    async for db in get_db():
        try:
            query = """
            SELECT DISTINCT run_id, workflow_name, status, created_at
            FROM workflow_runs 
            ORDER BY created_at DESC 
            LIMIT 10
            """
            result = await db.execute(text(query))
            rows = result.fetchall()
            
            if not rows:
                print("❌ No workflow runs found")
                return
            
            print("📋 Recent Workflow Runs:")
            print("=" * 80)
            for row in rows:
                print(f"🔄 {row.run_id}")
                print(f"   Workflow: {row.workflow_name}")
                print(f"   Status: {row.status}")
                print(f"   Created: {row.created_at}")
                print()
                
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            asyncio.run(list_recent_runs())
        else:
            run_id = sys.argv[1]
            asyncio.run(debug_step_outputs(run_id))
    else:
        print("🔍 Debugging latest workflow run...")
        asyncio.run(debug_step_outputs())