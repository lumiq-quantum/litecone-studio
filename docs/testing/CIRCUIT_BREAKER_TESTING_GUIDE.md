# Circuit Breaker Testing Guide

## Overview

This guide shows you how to test the circuit breaker functionality step-by-step.

## Prerequisites

1. Docker and Docker Compose installed
2. Services running (Redis, Kafka, PostgreSQL, Bridge)
3. At least one agent registered

## Quick Test (5 Minutes)

### Step 1: Start Services

```bash
# Start all required services
docker-compose up -d redis kafka postgres bridge

# Verify services are running
docker-compose ps
```

### Step 2: Create a Mock Failing Agent

We'll create a simple mock agent that fails on purpose:

```bash
# Create a simple failing agent script
cat > mock_failing_agent.py << 'EOF'
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Counter to track calls
call_count = 0
fail_count = int(os.getenv('FAIL_COUNT', '5'))  # Fail first N calls

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/', methods=['POST'])
def process():
    global call_count
    call_count += 1
    
    print(f"Call #{call_count}")
    
    # Fail first N calls, then succeed
    if call_count <= fail_count:
        print(f"  → Failing (call {call_count}/{fail_count})")
        return jsonify({
            "jsonrpc": "2.0",
            "id": request.json.get('id'),
            "error": {
                "code": -32000,
                "message": f"Simulated failure {call_count}/{fail_count}"
            }
        }), 500
    else:
        print(f"  → Success (call {call_count})")
        return jsonify({
            "jsonrpc": "2.0",
            "id": request.json.get('id'),
            "result": {
                "status": {"state": "completed"},
                "artifacts": [{
                    "parts": [{
                        "kind": "text",
                        "text": f"Success after {fail_count} failures!"
                    }]
                }]
            }
        }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090)
EOF

# Install Flask if needed
pip install flask

# Run the mock agent (in a separate terminal)
FAIL_COUNT=5 python mock_failing_agent.py
```

### Step 3: Register the Agent with Circuit Breaker

```bash
# Register the failing agent with circuit breaker configuration
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FailingTestAgent",
    "url": "http://host.docker.internal:8090",
    "description": "Test agent that fails initially",
    "timeout_ms": 5000,
    "retry_config": {
      "max_retries": 0,
      "initial_delay_ms": 100,
      "max_delay_ms": 1000,
      "backoff_multiplier": 1.0
    },
    "circuit_breaker_config": {
      "enabled": true,
      "failure_threshold": 3,
      "failure_rate_threshold": 0.5,
      "timeout_seconds": 30,
      "half_open_max_calls": 2,
      "window_size_seconds": 60
    }
  }'
```

### Step 4: Create Test Workflow

```bash
# Create a simple test workflow
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "circuit-breaker-test",
    "name": "Circuit Breaker Test",
    "start_step": "test-step",
    "steps": {
      "test-step": {
        "id": "test-step",
        "agent_name": "FailingTestAgent",
        "input_mapping": {
          "test": "data"
        }
      }
    }
  }'
```

### Step 5: Execute and Watch Circuit Breaker in Action

```bash
# Execute the workflow multiple times
echo "=== Execution 1 (should fail) ==="
curl -X POST http://localhost:8000/api/v1/workflows/circuit-breaker-test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {"test": "1"}}'
sleep 2

echo -e "\n=== Execution 2 (should fail) ==="
curl -X POST http://localhost:8000/api/v1/workflows/circuit-breaker-test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {"test": "2"}}'
sleep 2

echo -e "\n=== Execution 3 (should fail, circuit opens!) ==="
curl -X POST http://localhost:8000/api/v1/workflows/circuit-breaker-test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {"test": "3"}}'
sleep 2

echo -e "\n=== Execution 4 (should fail IMMEDIATELY - circuit is OPEN) ==="
curl -X POST http://localhost:8000/api/v1/workflows/circuit-breaker-test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {"test": "4"}}'
```

### Step 6: Check Circuit Breaker State

```bash
# Check circuit breaker state in Redis
docker exec redis redis-cli GET "circuit_breaker:FailingTestAgent:state"
# Should return: "open"

# Check when circuit was opened
docker exec redis redis-cli GET "circuit_breaker:FailingTestAgent:open_timestamp"

# View all circuit breaker keys
docker exec redis redis-cli KEYS "circuit_breaker:*"
```

### Step 7: Watch Logs

```bash
# Watch bridge logs for circuit breaker events
docker-compose logs -f bridge | grep -i circuit

# You should see:
# "Circuit breaker OPENED for agent 'FailingTestAgent' due to failures"
```

### Step 8: Wait for Recovery

```bash
# Wait 30 seconds (timeout_seconds)
echo "Waiting 30 seconds for circuit to attempt recovery..."
sleep 30

# Execute again - circuit should be HALF_OPEN
echo -e "\n=== Execution 5 (circuit HALF_OPEN, testing recovery) ==="
curl -X POST http://localhost:8000/api/v1/workflows/circuit-breaker-test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {"test": "5"}}'
sleep 2

# Execute again - should succeed and close circuit
echo -e "\n=== Execution 6 (circuit should CLOSE) ==="
curl -X POST http://localhost:8000/api/v1/workflows/circuit-breaker-test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {"test": "6"}}'

# Check circuit state
docker exec redis redis-cli GET "circuit_breaker:FailingTestAgent:state"
# Should return: "closed"
```

## Automated Test Script

Save this as `test_circuit_breaker.sh`:

```bash
#!/bin/bash

echo "=========================================="
echo "Circuit Breaker Test Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check circuit state
check_circuit_state() {
    state=$(docker exec redis redis-cli GET "circuit_breaker:FailingTestAgent:state" 2>/dev/null | tr -d '\r')
    echo "$state"
}

# Function to execute workflow
execute_workflow() {
    local num=$1
    echo -e "${YELLOW}Execution #$num${NC}"
    
    response=$(curl -s -X POST http://localhost:8000/api/v1/workflows/circuit-breaker-test/execute \
      -H "Content-Type: application/json" \
      -d '{"input": {"test": "'$num'"}}')
    
    run_id=$(echo $response | jq -r '.run_id // empty')
    
    if [ -n "$run_id" ]; then
        echo "  Run ID: $run_id"
        
        # Wait a bit for execution
        sleep 3
        
        # Check run status
        status=$(curl -s http://localhost:8000/api/v1/runs/$run_id | jq -r '.status')
        echo "  Status: $status"
        
        if [ "$status" = "FAILED" ]; then
            error=$(curl -s http://localhost:8000/api/v1/runs/$run_id | jq -r '.error_message // empty')
            if [[ "$error" == *"Circuit breaker is OPEN"* ]]; then
                echo -e "  ${RED}Failed: Circuit breaker is OPEN${NC}"
            else
                echo -e "  ${RED}Failed: $error${NC}"
            fi
        else
            echo -e "  ${GREEN}Success!${NC}"
        fi
    else
        echo -e "  ${RED}Failed to start workflow${NC}"
    fi
    
    # Check circuit state
    state=$(check_circuit_state)
    echo "  Circuit State: $state"
    echo ""
}

# Test sequence
echo "Starting test sequence..."
echo ""

echo "Phase 1: Trigger circuit breaker (3 failures)"
echo "----------------------------------------------"
execute_workflow 1
execute_workflow 2
execute_workflow 3

echo "Phase 2: Verify circuit is OPEN"
echo "--------------------------------"
state=$(check_circuit_state)
if [ "$state" = "open" ]; then
    echo -e "${GREEN}✓ Circuit is OPEN as expected${NC}"
else
    echo -e "${RED}✗ Circuit state is '$state', expected 'open'${NC}"
fi
echo ""

echo "Phase 3: Test fast failure (circuit OPEN)"
echo "------------------------------------------"
execute_workflow 4

echo "Phase 4: Wait for timeout (30 seconds)"
echo "---------------------------------------"
for i in {30..1}; do
    echo -ne "  Waiting... $i seconds remaining\r"
    sleep 1
done
echo ""
echo ""

echo "Phase 5: Test recovery (circuit HALF_OPEN)"
echo "-------------------------------------------"
execute_workflow 5
execute_workflow 6

echo "Phase 6: Verify circuit is CLOSED"
echo "----------------------------------"
state=$(check_circuit_state)
if [ "$state" = "closed" ]; then
    echo -e "${GREEN}✓ Circuit is CLOSED - recovery successful!${NC}"
else
    echo -e "${YELLOW}⚠ Circuit state is '$state'${NC}"
fi
echo ""

echo "=========================================="
echo "Test Complete!"
echo "=========================================="
```

Make it executable and run:

```bash
chmod +x test_circuit_breaker.sh
./test_circuit_breaker.sh
```

## Manual Testing via UI

### Step 1: Create Agent via UI

1. Go to **Agents** page
2. Click **Create Agent**
3. Fill in:
   - Name: `TestFailingAgent`
   - URL: `http://host.docker.internal:8090`
4. Scroll to **Circuit Breaker** section
5. Configure:
   - Enabled: ✓
   - Failure Threshold: 3
   - Failure Rate: 0.5
   - Timeout: 30s
6. Click **Create**

### Step 2: Create Workflow via UI

1. Go to **Workflows** page
2. Click **Create Workflow**
3. Paste this JSON:
```json
{
  "workflow_id": "ui-circuit-test",
  "name": "UI Circuit Breaker Test",
  "start_step": "test",
  "steps": {
    "test": {
      "id": "test",
      "agent_name": "TestFailingAgent",
      "input_mapping": {
        "data": "${workflow.input.data}"
      }
    }
  }
}
```
4. Click **Create**

### Step 3: Execute Multiple Times

1. Click **Execute** on the workflow
2. Enter input: `{"data": "test1"}`
3. Click **Execute** - Should fail
4. Repeat 2 more times - Circuit should open
5. Execute again - Should fail immediately with "Circuit breaker is OPEN"

### Step 4: Monitor in UI

1. Go to **Runs** page
2. See the failed runs
3. Click on a run to see error details
4. Look for "Circuit breaker is OPEN" message

## Verification Checklist

Use this checklist to verify circuit breaker is working:

- [ ] **Phase 1: Normal Failures**
  - [ ] First 3 executions fail normally (take ~5 seconds each)
  - [ ] Error messages show agent failures

- [ ] **Phase 2: Circuit Opens**
  - [ ] After 3 failures, circuit state is "open"
  - [ ] Logs show "Circuit breaker OPENED"

- [ ] **Phase 3: Fast Failure**
  - [ ] Next execution fails immediately (<1 second)
  - [ ] Error message: "Circuit breaker is OPEN for agent 'FailingTestAgent'"
  - [ ] No HTTP call made to agent

- [ ] **Phase 4: Recovery Testing**
  - [ ] After 30 seconds, circuit state is "half_open"
  - [ ] Test calls are allowed through
  - [ ] Logs show "Circuit breaker transitioned to HALF_OPEN"

- [ ] **Phase 5: Circuit Closes**
  - [ ] After 2 successful test calls, circuit state is "closed"
  - [ ] Logs show "Circuit breaker transitioned to CLOSED"
  - [ ] Normal operation resumes

## Troubleshooting

### Circuit Doesn't Open

**Check:**
```bash
# Verify Redis is running
docker exec redis redis-cli PING

# Check if circuit breaker is enabled
docker-compose logs bridge | grep "Circuit Breaker"

# Verify agent configuration
curl http://localhost:8000/api/v1/agents/FailingTestAgent
```

### Circuit Opens Too Quickly

**Solution:** Increase thresholds
```bash
# Update agent with higher thresholds
curl -X PUT http://localhost:8000/api/v1/agents/FailingTestAgent \
  -H "Content-Type: application/json" \
  -d '{
    "circuit_breaker_config": {
      "enabled": true,
      "failure_threshold": 10,
      "failure_rate_threshold": 0.3,
      "timeout_seconds": 60
    }
  }'
```

### Circuit Doesn't Close

**Check:**
```bash
# Verify agent is now succeeding
curl -X POST http://host.docker.internal:8090 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": "test", "method": "message/send", "params": {}}'

# Manually reset circuit
docker exec redis redis-cli DEL "circuit_breaker:FailingTestAgent:state"
```

## Expected Log Output

When circuit breaker is working correctly, you should see:

```
INFO: Circuit breaker state changed to open for agent 'FailingTestAgent'
INFO: Circuit breaker threshold reached: 3 consecutive failures
WARNING: Circuit breaker OPENED for agent 'FailingTestAgent' due to failures

... 30 seconds later ...

INFO: Circuit breaker timeout elapsed (30.1s), attempting reset
INFO: Circuit breaker state changed to half_open for agent 'FailingTestAgent'

... after successful test calls ...

INFO: Circuit breaker transitioned to CLOSED for agent 'FailingTestAgent' after 2 successful test calls
```

## Performance Verification

Verify fast failure when circuit is open:

```bash
# Time a call when circuit is CLOSED (should take ~5 seconds)
time curl -X POST http://localhost:8000/api/v1/workflows/circuit-breaker-test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'

# Time a call when circuit is OPEN (should take <1 second)
time curl -X POST http://localhost:8000/api/v1/workflows/circuit-breaker-test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'
```

## Clean Up

After testing:

```bash
# Stop mock agent (Ctrl+C in its terminal)

# Delete test workflow
curl -X DELETE http://localhost:8000/api/v1/workflows/circuit-breaker-test

# Delete test agent
curl -X DELETE http://localhost:8000/api/v1/agents/FailingTestAgent

# Clear Redis data
docker exec redis redis-cli FLUSHDB
```

## Next Steps

Once you've verified circuit breaker works:

1. Configure circuit breaker for your production agents
2. Adjust thresholds based on your requirements
3. Set up monitoring and alerts
4. Test with real failing scenarios

## Summary

The circuit breaker is working correctly if:

✅ Circuit opens after configured number of failures  
✅ Subsequent calls fail immediately when circuit is open  
✅ Circuit transitions to half-open after timeout  
✅ Circuit closes after successful test calls  
✅ Fast failure (<1ms) when circuit is open  
✅ Logs show state transitions  

You've successfully tested the circuit breaker! 🎉
