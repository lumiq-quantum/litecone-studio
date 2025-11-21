#!/usr/bin/env python3
"""
End-to-End Test Script

Tests the complete workflow execution by:
1. Starting all services via Docker Compose
2. Submitting a workflow execution request
3. Verifying workflow completes successfully
4. Checking database for execution records
"""

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

import psycopg2
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

# Configuration
KAFKA_BROKERS = os.getenv('KAFKA_BROKERS', 'localhost:9092')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://workflow_user:workflow_pass@localhost:5432/workflow_db')
WORKFLOW_FILE = os.getenv('WORKFLOW_FILE', 'examples/sample_workflow.json')
WORKFLOW_INPUT_FILE = os.getenv('WORKFLOW_INPUT_FILE', 'examples/sample_workflow_input.json')
TIMEOUT_SECONDS = int(os.getenv('TEST_TIMEOUT', '120'))

# Kafka topics
EXECUTOR_TRIGGER_TOPIC = 'workflow.execution.requests'
MONITORING_TOPIC = 'workflow.monitoring.updates'


class E2ETest:
    """End-to-end test orchestrator"""
    
    def __init__(self):
        self.run_id = f"test-run-{uuid.uuid4()}"
        self.kafka_producer: Optional[KafkaProducer] = None
        self.kafka_consumer: Optional[KafkaConsumer] = None
        self.db_conn = None
        self.workflow_plan = None
        self.workflow_input = None
        
    def load_workflow_files(self):
        """Load workflow plan and input from JSON files"""
        print(f"Loading workflow from {WORKFLOW_FILE}")
        with open(WORKFLOW_FILE, 'r') as f:
            self.workflow_plan = json.load(f)
        
        print(f"Loading workflow input from {WORKFLOW_INPUT_FILE}")
        with open(WORKFLOW_INPUT_FILE, 'r') as f:
            self.workflow_input = json.load(f)
    
    def connect_kafka(self):
        """Initialize Kafka producer and consumer"""
        print(f"Connecting to Kafka at {KAFKA_BROKERS}")
        
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKERS.split(','),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            max_block_ms=10000
        )
        
        self.kafka_consumer = KafkaConsumer(
            MONITORING_TOPIC,
            bootstrap_servers=KAFKA_BROKERS.split(','),
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id=f'e2e-test-{uuid.uuid4()}',
            consumer_timeout_ms=5000
        )
        
        print("✓ Kafka connected")
    
    def connect_database(self):
        """Connect to PostgreSQL database"""
        print(f"Connecting to database")
        
        # Parse DATABASE_URL
        # Format: postgresql://user:pass@host:port/dbname
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
        if not match:
            raise ValueError(f"Invalid DATABASE_URL format: {DATABASE_URL}")
        
        user, password, host, port, dbname = match.groups()
        
        self.db_conn = psycopg2.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            dbname=dbname
        )
        
        print("✓ Database connected")
    
    def submit_workflow(self):
        """Submit workflow execution request"""
        print(f"\nSubmitting workflow execution request (run_id: {self.run_id})")
        
        # Create execution request message
        request = {
            'run_id': self.run_id,
            'workflow_plan': self.workflow_plan,
            'workflow_input': self.workflow_input,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Note: In a real system, this would trigger the executor spawn
        # For this test, we'll manually invoke the executor with these parameters
        print(f"Workflow: {self.workflow_plan['name']} (v{self.workflow_plan['version']})")
        print(f"Input: {json.dumps(self.workflow_input, indent=2)}")
        
        return request
    
    def monitor_workflow_execution(self) -> bool:
        """Monitor workflow execution via Kafka monitoring topic"""
        print(f"\nMonitoring workflow execution (timeout: {TIMEOUT_SECONDS}s)")
        
        start_time = time.time()
        step_statuses = {}
        workflow_completed = False
        workflow_failed = False
        
        while time.time() - start_time < TIMEOUT_SECONDS:
            try:
                # Poll for messages
                messages = self.kafka_consumer.poll(timeout_ms=1000)
                
                for topic_partition, records in messages.items():
                    for record in records:
                        update = record.value
                        
                        # Filter for our run_id
                        if update.get('run_id') != self.run_id:
                            continue
                        
                        step_id = update.get('step_id', 'unknown')
                        status = update.get('status', 'unknown')
                        timestamp = update.get('timestamp', '')
                        
                        print(f"  [{timestamp}] Step {step_id}: {status}")
                        
                        step_statuses[step_id] = status
                        
                        # Check for workflow completion
                        if status == 'COMPLETED' and step_id == 'workflow':
                            workflow_completed = True
                            break
                        elif status == 'FAILED':
                            workflow_failed = True
                            error = update.get('metadata', {}).get('error_message', 'Unknown error')
                            print(f"  ERROR: {error}")
                            break
                
                if workflow_completed or workflow_failed:
                    break
                    
            except Exception as e:
                print(f"Error polling Kafka: {e}")
                time.sleep(1)
        
        if workflow_completed:
            print("\n✓ Workflow completed successfully")
            return True
        elif workflow_failed:
            print("\n✗ Workflow failed")
            return False
        else:
            print(f"\n✗ Workflow did not complete within {TIMEOUT_SECONDS}s")
            return False
    
    def verify_database_records(self) -> bool:
        """Verify workflow execution records in database"""
        print("\nVerifying database records...")
        
        cursor = self.db_conn.cursor()
        
        try:
            # Check workflow_runs table
            cursor.execute(
                "SELECT run_id, workflow_id, status, created_at, completed_at FROM workflow_runs WHERE run_id = %s",
                (self.run_id,)
            )
            run_record = cursor.fetchone()
            
            if not run_record:
                print("✗ No workflow run record found in database")
                return False
            
            run_id, workflow_id, status, created_at, completed_at = run_record
            print(f"✓ Workflow run record found:")
            print(f"  - run_id: {run_id}")
            print(f"  - workflow_id: {workflow_id}")
            print(f"  - status: {status}")
            print(f"  - created_at: {created_at}")
            print(f"  - completed_at: {completed_at}")
            
            if status != 'COMPLETED':
                print(f"✗ Expected status COMPLETED, got {status}")
                return False
            
            # Check step_executions table
            cursor.execute(
                "SELECT step_id, step_name, agent_name, status, input_data, output_data FROM step_executions WHERE run_id = %s ORDER BY started_at",
                (self.run_id,)
            )
            step_records = cursor.fetchall()
            
            if not step_records:
                print("✗ No step execution records found in database")
                return False
            
            print(f"\n✓ Found {len(step_records)} step execution records:")
            for step_id, step_name, agent_name, status, input_data, output_data in step_records:
                print(f"  - Step {step_id} ({agent_name}): {status}")
                print(f"    Input keys: {list(input_data.keys()) if input_data else 'None'}")
                print(f"    Output keys: {list(output_data.keys()) if output_data else 'None'}")
                
                if status != 'COMPLETED':
                    print(f"    ✗ Expected status COMPLETED, got {status}")
                    return False
            
            # Verify step count matches workflow plan
            expected_steps = len(self.workflow_plan['steps'])
            if len(step_records) != expected_steps:
                print(f"✗ Expected {expected_steps} steps, found {len(step_records)}")
                return False
            
            print("\n✓ All database records verified successfully")
            return True
            
        except Exception as e:
            print(f"✗ Database verification error: {e}")
            return False
        finally:
            cursor.close()
    
    def cleanup(self):
        """Clean up connections"""
        print("\nCleaning up...")
        
        if self.kafka_producer:
            self.kafka_producer.close()
        if self.kafka_consumer:
            self.kafka_consumer.close()
        if self.db_conn:
            self.db_conn.close()
        
        print("✓ Cleanup complete")
    
    def run(self) -> bool:
        """Run the complete end-to-end test"""
        print("=" * 60)
        print("End-to-End Workflow Execution Test")
        print("=" * 60)
        
        try:
            # Step 1: Load workflow files
            self.load_workflow_files()
            
            # Step 2: Connect to services
            self.connect_kafka()
            self.connect_database()
            
            # Step 3: Submit workflow
            request = self.submit_workflow()
            
            # Step 4: Start executor manually (in real system, this would be automatic)
            print("\n" + "=" * 60)
            print("MANUAL STEP REQUIRED:")
            print("=" * 60)
            print("Run the executor with the following command:")
            print(f"\n  python -m src.executor.centralized_executor \\")
            print(f"    --run-id {self.run_id} \\")
            print(f"    --workflow-plan '{json.dumps(self.workflow_plan)}' \\")
            print(f"    --workflow-input '{json.dumps(self.workflow_input)}'")
            print("\nOr use the Docker Compose profile:")
            print(f"\n  docker-compose --profile executor up")
            print("\nPress Enter when executor is running...")
            input()
            
            # Step 5: Monitor execution
            success = self.monitor_workflow_execution()
            
            if not success:
                return False
            
            # Step 6: Verify database records
            success = self.verify_database_records()
            
            return success
            
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
            return False
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


def check_services_ready():
    """Check if required services are running"""
    print("Checking if services are ready...")
    
    # Check Kafka
    try:
        from kafka.admin import KafkaAdminClient
        admin = KafkaAdminClient(bootstrap_servers=KAFKA_BROKERS.split(','))
        admin.close()
        print("✓ Kafka is ready")
    except Exception as e:
        print(f"✗ Kafka is not ready: {e}")
        print("\nStart services with: docker-compose up -d")
        return False
    
    # Check PostgreSQL
    try:
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
        if match:
            user, password, host, port, dbname = match.groups()
            conn = psycopg2.connect(host=host, port=int(port), user=user, password=password, dbname=dbname)
            conn.close()
            print("✓ PostgreSQL is ready")
        else:
            raise ValueError("Invalid DATABASE_URL")
    except Exception as e:
        print(f"✗ PostgreSQL is not ready: {e}")
        print("\nStart services with: docker-compose up -d")
        return False
    
    return True


def main():
    """Main entry point"""
    # Check if services are ready
    if not check_services_ready():
        sys.exit(1)
    
    # Run test
    test = E2ETest()
    success = test.run()
    
    # Print final result
    print("\n" + "=" * 60)
    if success:
        print("✓ END-TO-END TEST PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("✗ END-TO-END TEST FAILED")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
