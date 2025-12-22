#!/usr/bin/env python3
"""
Test script to see what your agent is actually returning.
"""

import asyncio
import httpx
import json

async def test_agent():
    """Test what your agent returns."""
    
    # Your agent URL (from the logs)
    agent_url = "https://agent007.codeshare.co.in/"
    
    # Build JSON-RPC request (same format the bridge uses)
    request = {
        "jsonrpc": "2.0",
        "id": "test-task-123",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": "msg-test-123",
                "parts": [
                    {
                        "kind": "text",
                        "text": "Hello, please return some test data"
                    }
                ]
            }
        }
    }
    
    print("🔄 Testing your agent...")
    print(f"📡 URL: {agent_url}")
    print(f"📤 Request:")
    print(json.dumps(request, indent=2))
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                agent_url,
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            print(f"\n📥 Response Status: {response.status_code}")
            print(f"📥 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"📥 Response Body:")
                print(json.dumps(response_data, indent=2))
                
                # Analyze the response structure
                print(f"\n🔍 Analysis:")
                if isinstance(response_data, dict):
                    print(f"✓ Response is a dictionary")
                    print(f"✓ Available fields: {list(response_data.keys())}")
                    
                    # Check if it's proper JSON-RPC
                    if "jsonrpc" in response_data and "result" in response_data:
                        print(f"✓ Proper JSON-RPC 2.0 response")
                        result = response_data["result"]
                        if isinstance(result, dict):
                            print(f"✓ Result fields: {list(result.keys())}")
                        else:
                            print(f"❌ Result is not a dictionary: {type(result)}")
                    else:
                        print(f"❌ Not a proper JSON-RPC 2.0 response")
                        print(f"   Missing 'jsonrpc' and/or 'result' fields")
                else:
                    print(f"❌ Response is not a dictionary: {type(response_data)}")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())