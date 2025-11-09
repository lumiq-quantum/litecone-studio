#!/usr/bin/env python3
"""Test workflow execution with JSON-RPC 2.0"""

import json
import time
import uuid
from kafka import KafkaProducer, KafkaConsumer


def test_workflow():
    """Test a simple workflow through Kafka"""
    print("=" * 60)
    print("Testing Workflow with JSON-RPC 2.0")
    print("=" * 60)
    
    # Create producer
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    # Create consumer
    consumer = KafkaConsumer(
        'results.topic',
        bootstrap_servers=['localhost:9092'],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        consumer_timeout_ms=30000,
        group_id=f'test-{uuid.uuid4()}'
    )
    
    # Generate task
    task_id = str(uuid.uuid4())
    run_id = f"test-{int(time.time())}"
    correlation_id = str(uuid.uuid4())
    
    task = {
        "run_id": run_id,
        "task_id": task_id,
        "agent_name": "ResearchAgent",
        "input_data": {
            "topic": "Artificial Intelligence",
            "depth": "comprehensive"
        },
        "correlation_id": correlation_id
    }
    
    print(f"\nTask Details:")
    print(f"  Task ID: {task_id}")
    print(f"  Run ID: {run_id}")
    print(f"  Agent: ResearchAgent")
    print(f"  Input: {task['input_data']}")
    
    # Send task
    print(f"\nSending task to Kafka topic 'orchestrator.tasks.http'...")
    producer.send('orchestrator.tasks.http', value=task)
    producer.flush()
    print("✓ Task sent")
    
    # Wait for result
    print("\nWaiting for result (timeout: 30s)...")
    
    for message in consumer:
        result = message.value
        
        if result.get('task_id') == task_id:
            print(f"\n✓ Received result for task {task_id}")
            print(f"\nResult:")
            print(json.dumps(result, indent=2))
            
            if result.get('status') == 'SUCCESS':
                print("\n" + "=" * 60)
                print("✓ TEST PASSED - Task completed successfully")
                print("=" * 60)
                
                # Verify output structure
                output = result.get('output_data', {})
                if 'text' in output or 'response' in output:
                    print("✓ Output contains expected fields")
                
                return True
            else:
                print("\n" + "=" * 60)
                print(f"✗ TEST FAILED - Task failed: {result.get('error_message')}")
                print("=" * 60)
                return False
    
    print("\n" + "=" * 60)
    print("✗ TEST FAILED - Timeout waiting for result")
    print("=" * 60)
    return False


if __name__ == '__main__':
    try:
        success = test_workflow()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
