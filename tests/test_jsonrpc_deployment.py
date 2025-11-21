#!/usr/bin/env python3
"""
Test JSON-RPC 2.0 Deployment

Tests the deployed bridge and mock agents with JSON-RPC 2.0 protocol.
"""

import json
import requests
import sys
import time
import uuid


def test_mock_agent_jsonrpc():
    """Test mock agent with JSON-RPC 2.0 request"""
    print("=" * 60)
    print("Test 1: Mock Agent JSON-RPC 2.0 Request")
    print("=" * 60)
    
    # Build JSON-RPC 2.0 request
    request_id = str(uuid.uuid4())
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": f"msg-{request_id}",
                "parts": [
                    {
                        "kind": "text",
                        "text": json.dumps({
                            "topic": "Climate Change",
                            "depth": "comprehensive"
                        })
                    }
                ]
            }
        }
    }
    
    print(f"\nSending JSON-RPC request to ResearchAgent...")
    print(f"Request ID: {request_id}")
    
    try:
        response = requests.post(
            "http://localhost:8081",
            json=request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"\nResponse:")
            print(json.dumps(response_data, indent=2))
            
            # Validate JSON-RPC response
            if "jsonrpc" in response_data and response_data["jsonrpc"] == "2.0":
                print("\n✓ Valid JSON-RPC 2.0 response")
                
                if "result" in response_data:
                    result = response_data["result"]
                    if "status" in result and result["status"]["state"] == "completed":
                        print("✓ Task completed successfully")
                    if "artifacts" in result:
                        print(f"✓ Response contains {len(result['artifacts'])} artifact(s)")
                    if "history" in result:
                        print(f"✓ Response contains {len(result['history'])} history item(s)")
                    return True
                else:
                    print("✗ Response missing 'result' field")
                    return False
            else:
                print("✗ Invalid JSON-RPC response")
                return False
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_kafka_workflow():
    """Test workflow execution through Kafka"""
    print("\n" + "=" * 60)
    print("Test 2: Workflow Execution via Kafka")
    print("=" * 60)
    
    try:
        from kafka import KafkaProducer, KafkaConsumer
        import time
        
        # Create Kafka producer
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Create Kafka consumer for results
        consumer = KafkaConsumer(
            'results.topic',
            bootstrap_servers=['localhost:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            consumer_timeout_ms=30000,
            group_id=f'test-consumer-{uuid.uuid4()}'
        )
        
        # Generate task
        task_id = str(uuid.uuid4())
        run_id = f"test-run-{int(time.time())}"
        correlation_id = str(uuid.uuid4())
        
        task = {
            "run_id": run_id,
            "task_id": task_id,
            "agent_name": "ResearchAgent",
            "input_data": {
                "topic": "Artificial Intelligence",
                "depth": "basic"
            },
            "correlation_id": correlation_id
        }
        
        print(f"\nSending task to Kafka...")
        print(f"Task ID: {task_id}")
        print(f"Run ID: {run_id}")
        print(f"Agent: ResearchAgent")
        
        # Send task
        producer.send('orchestrator.tasks.http', value=task)
        producer.flush()
        
        print("✓ Task sent to Kafka")
        print("\nWaiting for result...")
        
        # Wait for result
        for message in consumer:
            result = message.value
            print(f"\nReceived result:")
            print(json.dumps(result, indent=2))
            
            if result.get('task_id') == task_id:
                if result.get('status') == 'SUCCESS':
                    print("\n✓ Task completed successfully")
                    print(f"✓ Output received: {result.get('output_data')}")
                    return True
                else:
                    print(f"\n✗ Task failed: {result.get('error_message')}")
                    return False
        
        print("\n✗ Timeout waiting for result")
        return False
        
    except ImportError:
        print("\n⚠ kafka-python not installed, skipping Kafka test")
        print("  Install with: pip install kafka-python")
        return None
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("JSON-RPC 2.0 Deployment Tests")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Direct mock agent test
    result1 = test_mock_agent_jsonrpc()
    results.append(("Mock Agent JSON-RPC", result1))
    
    # Test 2: Kafka workflow test
    result2 = test_kafka_workflow()
    if result2 is not None:
        results.append(("Kafka Workflow", result2))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(r for r in results if r[1] is not None)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
