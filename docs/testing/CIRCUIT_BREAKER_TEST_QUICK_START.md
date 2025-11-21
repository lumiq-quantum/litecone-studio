# Circuit Breaker Test - Quick Start

## 🚀 Fastest Way to Test (2 Commands)

```bash
# 1. Make script executable (one time only)
chmod +x test_circuit_breaker_live.sh

# 2. Run the test
./test_circuit_breaker_live.sh
```

That's it! The script will:
- ✅ Check all services are running
- ✅ Start a mock failing agent
- ✅ Register agent with circuit breaker
- ✅ Create test workflow
- ✅ Execute tests and show results
- ✅ Verify circuit breaker behavior
- ✅ Clean up (optional)

## 📊 What You'll See

```
==========================================
Circuit Breaker Live Test
==========================================

Step 1: Checking Prerequisites
==================================================
✓ redis is running
✓ kafka is running
✓ postgres is running
✓ bridge is running
✓ API is accessible

Step 2: Starting Mock Failing Agent
==================================================
✓ Mock agent is responding

Step 3: Registering Agent with Circuit Breaker
==================================================
✓ Agent registered successfully

Step 4: Creating Test Workflow
==================================================
✓ Workflow created successfully

Step 5: Testing Circuit Breaker Behavior
==================================================

Phase 1: Trigger Circuit Breaker (3 failures)
----------------------------------------------
Test 1: First failure
  Run ID: run-xxx
  Status: FAILED
  Circuit State: closed
✓ Status matches expected: FAILED

Test 2: Second failure
  Run ID: run-yyy
  Status: FAILED
  Circuit State: closed
✓ Status matches expected: FAILED

Test 3: Third failure - circuit should OPEN
  Run ID: run-zzz
  Status: FAILED
  Circuit State: open
✓ Status matches expected: FAILED

Verifying Circuit State
✓ Circuit is OPEN as expected

Phase 2: Test Fast Failure (circuit OPEN)
------------------------------------------
Test 4: Fast failure test
  Run ID: run-aaa
  Status: FAILED
  Circuit State: open
  Execution time: 234ms
✓ Fast failure confirmed (<1 second)

Phase 3: Wait for Recovery (30 seconds)
----------------------------------------
  Waiting... 1 seconds remaining

Phase 4: Test Recovery (circuit HALF_OPEN)
-------------------------------------------
Test 5: First recovery test
  Run ID: run-bbb
  Status: COMPLETED
  Circuit State: half_open
✓ Status matches expected: COMPLETED

Test 6: Second recovery test - circuit should CLOSE
  Run ID: run-ccc
  Status: COMPLETED
  Circuit State: closed
✓ Status matches expected: COMPLETED

Verifying Final Circuit State
✓ Circuit is CLOSED - recovery successful!

✓ Circuit breaker test completed!

Circuit breaker is working correctly! 🎉
```

## 🔍 Manual Testing (Step by Step)

If you prefer manual testing:

### 1. Start Services
```bash
docker-compose up -d redis kafka postgres bridge
```

### 2. Create Mock Failing Agent
```bash
# Install Flask
pip install flask

# Create mock agent
cat > mock_failing_agent.py << 'EOF'
from flask import Flask, request, jsonify
import os

app = Flask(__name__)
call_count = 0
fail_count = int(os.getenv('FAIL_COUNT', '5'))

@app.route('/', methods=['POST'])
def process():
    global call_count
    call_count += 1
    
    if call_count <= fail_count:
        return jsonify({
            "jsonrpc": "2.0",
            "id": request.json.get('id'),
            "error": {"code": -32000, "message": "Simulated failure"}
        }), 500
    else:
        return jsonify({
            "jsonrpc": "2.0",
            "id": request.json.get('id'),
            "result": {
                "status": {"state": "completed"},
                "artifacts": [{"parts": [{"kind": "text", "text": "Success!"}]}]
            }
        }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090)
EOF

# Run it
FAIL_COUNT=5 python mock_failing_agent.py
```

### 3. Register Agent (in another terminal)
```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TestAgent",
    "url": "http://host.docker.internal:8090",
    "circuit_breaker_config": {
      "enabled": true,
      "failure_threshold": 3,
      "timeout_seconds": 30
    }
  }'
```

### 4. Create Workflow
```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "test",
    "start_step": "step-1",
    "steps": {
      "step-1": {
        "id": "step-1",
        "agent_name": "TestAgent",
        "input_mapping": {}
      }
    }
  }'
```

### 5. Execute 3 Times (Circuit Opens)
```bash
# Execution 1
curl -X POST http://localhost:8000/api/v1/workflows/test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'

# Execution 2
curl -X POST http://localhost:8000/api/v1/workflows/test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'

# Execution 3 (circuit opens!)
curl -X POST http://localhost:8000/api/v1/workflows/test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'
```

### 6. Check Circuit State
```bash
docker exec redis redis-cli GET "circuit_breaker:TestAgent:state"
# Should return: "open"
```

### 7. Test Fast Failure
```bash
# This should fail immediately
time curl -X POST http://localhost:8000/api/v1/workflows/test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'
# Should take <1 second
```

### 8. Wait and Test Recovery
```bash
# Wait 30 seconds
sleep 30

# Execute again (circuit half-open)
curl -X POST http://localhost:8000/api/v1/workflows/test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'

# Execute again (circuit closes)
curl -X POST http://localhost:8000/api/v1/workflows/test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'

# Check state
docker exec redis redis-cli GET "circuit_breaker:TestAgent:state"
# Should return: "closed"
```

## 📝 Verification Checklist

- [ ] Services are running (redis, kafka, postgres, bridge)
- [ ] Mock agent responds on port 8090
- [ ] Agent registered with circuit breaker config
- [ ] Workflow created successfully
- [ ] First 3 executions fail (circuit opens)
- [ ] Circuit state is "open" in Redis
- [ ] 4th execution fails immediately (<1s)
- [ ] After 30s, circuit transitions to "half_open"
- [ ] Test calls succeed
- [ ] Circuit state is "closed" in Redis
- [ ] Logs show circuit breaker events

## 🔧 Troubleshooting

### Services Not Running
```bash
docker-compose up -d redis kafka postgres bridge
docker-compose ps
```

### Mock Agent Not Responding
```bash
# Check if port is in use
lsof -i :8090

# Check mock agent logs
tail -f mock_agent.log
```

### Circuit Not Opening
```bash
# Check bridge logs
docker-compose logs bridge | grep -i circuit

# Verify Redis connection
docker exec redis redis-cli PING

# Check agent configuration
curl http://localhost:8000/api/v1/agents/TestAgent | jq .circuit_breaker_config
```

### Circuit Not Closing
```bash
# Check if agent is now succeeding
curl -X POST http://localhost:8090 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": "test", "method": "message/send", "params": {}}'

# Manually reset if needed
docker exec redis redis-cli DEL "circuit_breaker:TestAgent:state"
```

## 📚 More Information

- **Full Testing Guide**: [CIRCUIT_BREAKER_TESTING_GUIDE.md](CIRCUIT_BREAKER_TESTING_GUIDE.md)
- **Usage Guide**: [examples/CIRCUIT_BREAKER_USAGE_GUIDE.md](examples/CIRCUIT_BREAKER_USAGE_GUIDE.md)
- **Documentation**: [docs/circuit_breaker.md](docs/circuit_breaker.md)
- **Quick Reference**: [examples/CIRCUIT_BREAKER_QUICK_REFERENCE.md](examples/CIRCUIT_BREAKER_QUICK_REFERENCE.md)

## 🎉 Success!

If you see:
- ✅ Circuit opens after 3 failures
- ✅ Fast failure when circuit is open
- ✅ Circuit closes after successful recovery
- ✅ Logs show state transitions

**Your circuit breaker is working perfectly!** 🎊
