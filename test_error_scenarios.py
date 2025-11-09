#!/usr/bin/env python3
"""Test JSON-RPC error scenarios"""

import json
import time
import uuid
from kafka import KafkaProducer, KafkaConsumer


def test_jsonrpc_error():
    """Test JSON-RPC error response handling"""
    print("=" * 60)
    print("Test: JSON-RPC Error Response")
    print("=" * 60)
    
    print("\nNote: Testing with existing agents")
    print("Test 1: Invalid agent name (should fail at registry)")
    print("Test 2: Valid agent (should succeed)")
    
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
        consumer_timeout_ms=15000,
        group_id=f'test-error-{uuid.uuid4()}'
    )
    
    # Test 1: Invalid agent (should fail at registry lookup)
    print("\n--- Test 1: Invalid Agent Name ---")
    task_id = str(uuid.uuid4())
    task = {
        "run_id": f"test-error-{int(time.time())}",
        "task_id": task_id,
        "agent_name": "NonExistentAgent",
        "input_data": {"test": "data"},
        "correlation_id": str(uuid.uuid4())
    }
    
    print(f"Sending task with invalid agent name...")
    producer.send('orchestrator.tasks.http', value=task)
    producer.flush()
    
    # Wait for result
    for message in consumer:
        result = message.value
        if result.get('task_id') == task_id:
            print(f"\nResult: {json.dumps(result, indent=2)}")
            if result.get('status') == 'FAILURE':
                print("✓ Correctly handled invalid agent")
            break
    
    # Test 2: Malformed JSON-RPC request (missing required fields)
    print("\n--- Test 2: Test with valid agent ---")
    task_id = str(uuid.uuid4())
    task = {
        "run_id": f"test-success-{int(time.time())}",
        "task_id": task_id,
        "agent_name": "ResearchAgent",
        "input_data": {"topic": "Test Topic"},
        "correlation_id": str(uuid.uuid4())
    }
    
    print(f"Sending task to ResearchAgent...")
    producer.send('orchestrator.tasks.http', value=task)
    producer.flush()
    
    # Wait for result
    for message in consumer:
        result = message.value
        if result.get('task_id') == task_id:
            print(f"\nResult status: {result.get('status')}")
            if result.get('status') == 'SUCCESS':
                print("✓ Successfully processed valid request")
            break
    
    print("\n" + "=" * 60)
    print("Error Scenario Tests Complete")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_jsonrpc_error()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
