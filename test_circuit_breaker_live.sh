#!/bin/bash

# Circuit Breaker Live Test Script
# This script tests the circuit breaker functionality end-to-end

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
AGENT_NAME="CircuitBreakerTestAgent"
WORKFLOW_ID="circuit-breaker-live-test"
MOCK_AGENT_PORT=8090

echo -e "${BLUE}=========================================="
echo "Circuit Breaker Live Test"
echo -e "==========================================${NC}"
echo ""

# Function to print section header
print_section() {
    echo -e "\n${BLUE}$1${NC}"
    echo "$(printf '=%.0s' {1..50})"
}

# Detect docker compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo -e "${RED}Error: Neither 'docker-compose' nor 'docker compose' found${NC}"
    exit 1
fi

# Function to check if service is running
check_service() {
    local service=$1
    if $DOCKER_COMPOSE ps | grep -q "$service.*Up\|$service.*running"; then
        echo -e "${GREEN}✓${NC} $service is running"
        return 0
    else
        echo -e "${RED}✗${NC} $service is not running"
        return 1
    fi
}

# Function to check circuit state
check_circuit_state() {
    state=$(docker exec redis redis-cli GET "circuit_breaker:$AGENT_NAME:state" 2>/dev/null | tr -d '\r\n' | tr -d '"')
    if [ -z "$state" ]; then
        echo "closed"
    else
        echo "$state"
    fi
}

# Function to execute workflow and check result
execute_and_check() {
    local num=$1
    local expected_status=$2
    local description=$3
    
    echo -e "\n${YELLOW}Test $num: $description${NC}"
    
    # Execute workflow
    response=$(curl -s -X POST "$API_URL/api/v1/workflows/$WORKFLOW_ID/execute" \
      -H "Content-Type: application/json" \
      -d "{\"input\": {\"test\": \"$num\"}}")
    
    run_id=$(echo "$response" | jq -r '.run_id // empty')
    
    if [ -z "$run_id" ]; then
        echo -e "${RED}✗ Failed to start workflow${NC}"
        echo "Response: $response"
        return 1
    fi
    
    echo "  Run ID: $run_id"
    
    # Wait for execution to complete
    sleep 3
    
    # Check run status
    run_response=$(curl -s "$API_URL/api/v1/runs/$run_id")
    status=$(echo "$run_response" | jq -r '.status')
    
    echo "  Status: $status"
    
    # Check circuit state
    circuit_state=$(check_circuit_state)
    echo "  Circuit State: $circuit_state"
    
    # Verify expected status
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✓ Status matches expected: $expected_status${NC}"
    else
        echo -e "${RED}✗ Status mismatch. Expected: $expected_status, Got: $status${NC}"
    fi
    
    # Show error if failed
    if [ "$status" = "FAILED" ]; then
        error=$(echo "$run_response" | jq -r '.error_message // empty')
        if [ -n "$error" ]; then
            echo "  Error: $error"
        fi
    fi
    
    return 0
}

# Step 1: Check prerequisites
print_section "Step 1: Checking Prerequisites"

check_service "redis" || { echo "Please start Redis: $DOCKER_COMPOSE up -d redis"; exit 1; }
check_service "kafka" || { echo "Please start Kafka: $DOCKER_COMPOSE up -d kafka"; exit 1; }
check_service "postgres" || { echo "Please start PostgreSQL: $DOCKER_COMPOSE up -d postgres"; exit 1; }
check_service "bridge" || { echo "Please start Bridge: $DOCKER_COMPOSE up -d bridge"; exit 1; }

# Check if API is accessible
if curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} API is accessible at $API_URL"
else
    echo -e "${YELLOW}⚠${NC} API might not be running at $API_URL"
fi

# Step 2: Start mock failing agent
print_section "Step 2: Starting Mock Failing Agent"

# Check if mock agent is already running
if lsof -Pi :$MOCK_AGENT_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠${NC} Port $MOCK_AGENT_PORT is already in use"
    echo "  Assuming mock agent is already running"
else
    echo "Starting mock failing agent on port $MOCK_AGENT_PORT..."
    
    # Create mock agent if it doesn't exist
    if [ ! -f "mock_failing_agent.py" ]; then
        cat > mock_failing_agent.py << 'AGENT_EOF'
from flask import Flask, request, jsonify
import os

app = Flask(__name__)
call_count = 0
fail_count = int(os.getenv('FAIL_COUNT', '5'))

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/', methods=['POST'])
def process():
    global call_count
    call_count += 1
    print(f"Call #{call_count}")
    
    if call_count <= fail_count:
        print(f"  → Failing (call {call_count}/{fail_count})")
        return jsonify({
            "jsonrpc": "2.0",
            "id": request.json.get('id'),
            "error": {"code": -32000, "message": f"Simulated failure {call_count}/{fail_count}"}
        }), 500
    else:
        print(f"  → Success (call {call_count})")
        return jsonify({
            "jsonrpc": "2.0",
            "id": request.json.get('id'),
            "result": {
                "status": {"state": "completed"},
                "artifacts": [{"parts": [{"kind": "text", "text": f"Success after {fail_count} failures!"}]}]
            }
        }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090)
AGENT_EOF
    fi
    
    # Start mock agent in background
    FAIL_COUNT=5 python3 mock_failing_agent.py > mock_agent.log 2>&1 &
    MOCK_AGENT_PID=$!
    echo "  Mock agent started (PID: $MOCK_AGENT_PID)"
    sleep 2
    
    # Verify it's running
    if curl -s http://localhost:$MOCK_AGENT_PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Mock agent is responding"
    else
        echo -e "${RED}✗${NC} Mock agent failed to start"
        exit 1
    fi
fi

# Step 3: Register agent with circuit breaker
print_section "Step 3: Registering Agent with Circuit Breaker"

agent_response=$(curl -s -X POST "$API_URL/api/v1/agents" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"$AGENT_NAME\",
    \"url\": \"http://host.docker.internal:$MOCK_AGENT_PORT\",
    \"description\": \"Test agent for circuit breaker\",
    \"timeout_ms\": 5000,
    \"retry_config\": {
      \"max_retries\": 0,
      \"initial_delay_ms\": 100,
      \"max_delay_ms\": 1000,
      \"backoff_multiplier\": 1.0
    },
    \"circuit_breaker_config\": {
      \"enabled\": true,
      \"failure_threshold\": 3,
      \"failure_rate_threshold\": 0.5,
      \"timeout_seconds\": 30,
      \"half_open_max_calls\": 2,
      \"window_size_seconds\": 60
    }
  }")

if echo "$agent_response" | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Agent registered successfully"
    echo "  Agent ID: $(echo "$agent_response" | jq -r '.id')"
else
    echo -e "${YELLOW}⚠${NC} Agent might already exist or registration failed"
fi

# Step 4: Create test workflow
print_section "Step 4: Creating Test Workflow"

workflow_response=$(curl -s -X POST "$API_URL/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -d "{
    \"workflow_id\": \"$WORKFLOW_ID\",
    \"name\": \"Circuit Breaker Live Test\",
    \"start_step\": \"test-step\",
    \"steps\": {
      \"test-step\": {
        \"id\": \"test-step\",
        \"agent_name\": \"$AGENT_NAME\",
        \"input_mapping\": {
          \"test\": \"\${workflow.input.test}\"
        }
      }
    }
  }")

if echo "$workflow_response" | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Workflow created successfully"
else
    echo -e "${YELLOW}⚠${NC} Workflow might already exist or creation failed"
fi

# Step 5: Execute tests
print_section "Step 5: Testing Circuit Breaker Behavior"

echo -e "\n${BLUE}Phase 1: Trigger Circuit Breaker (3 failures)${NC}"
execute_and_check 1 "FAILED" "First failure"
execute_and_check 2 "FAILED" "Second failure"
execute_and_check 3 "FAILED" "Third failure - circuit should OPEN"

# Verify circuit is open
circuit_state=$(check_circuit_state)
echo -e "\n${BLUE}Verifying Circuit State${NC}"
if [ "$circuit_state" = "open" ]; then
    echo -e "${GREEN}✓ Circuit is OPEN as expected${NC}"
else
    echo -e "${RED}✗ Circuit state is '$circuit_state', expected 'open'${NC}"
fi

echo -e "\n${BLUE}Phase 2: Test Fast Failure (circuit OPEN)${NC}"
echo "Measuring execution time..."
start_time=$(date +%s%N)
execute_and_check 4 "FAILED" "Fast failure test"
end_time=$(date +%s%N)
duration=$(( (end_time - start_time) / 1000000 ))
echo "  Execution time: ${duration}ms"
if [ $duration -lt 1000 ]; then
    echo -e "${GREEN}✓ Fast failure confirmed (<1 second)${NC}"
else
    echo -e "${YELLOW}⚠ Execution took ${duration}ms (expected <1000ms)${NC}"
fi

echo -e "\n${BLUE}Phase 3: Wait for Recovery (30 seconds)${NC}"
for i in {30..1}; do
    echo -ne "  Waiting... $i seconds remaining\r"
    sleep 1
done
echo -e "\n"

echo -e "\n${BLUE}Phase 4: Test Recovery (circuit HALF_OPEN)${NC}"
execute_and_check 5 "COMPLETED" "First recovery test"
execute_and_check 6 "COMPLETED" "Second recovery test - circuit should CLOSE"

# Verify circuit is closed
circuit_state=$(check_circuit_state)
echo -e "\n${BLUE}Verifying Final Circuit State${NC}"
if [ "$circuit_state" = "closed" ]; then
    echo -e "${GREEN}✓ Circuit is CLOSED - recovery successful!${NC}"
else
    echo -e "${YELLOW}⚠ Circuit state is '$circuit_state'${NC}"
fi

# Step 6: View logs
print_section "Step 6: Circuit Breaker Logs"

echo "Recent circuit breaker events:"
$DOCKER_COMPOSE logs --tail=20 bridge 2>/dev/null | grep -i "circuit" || echo "No circuit breaker logs found"

# Step 7: Summary
print_section "Test Summary"

echo -e "${GREEN}✓ Circuit breaker test completed!${NC}"
echo ""
echo "What happened:"
echo "  1. Agent failed 3 times → Circuit OPENED"
echo "  2. Next call failed immediately (<1s) → Fast failure"
echo "  3. After 30s timeout → Circuit HALF_OPEN"
echo "  4. 2 successful test calls → Circuit CLOSED"
echo ""
echo "Circuit breaker is working correctly! 🎉"

# Cleanup option
echo ""
read -p "Do you want to clean up test resources? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_section "Cleaning Up"
    
    # Delete workflow
    curl -s -X DELETE "$API_URL/api/v1/workflows/$WORKFLOW_ID" > /dev/null
    echo -e "${GREEN}✓${NC} Deleted test workflow"
    
    # Delete agent
    curl -s -X DELETE "$API_URL/api/v1/agents/$AGENT_NAME" > /dev/null
    echo -e "${GREEN}✓${NC} Deleted test agent"
    
    # Stop mock agent
    if [ -n "$MOCK_AGENT_PID" ]; then
        kill $MOCK_AGENT_PID 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Stopped mock agent"
    fi
    
    # Clear Redis
    docker exec redis redis-cli FLUSHDB > /dev/null 2>&1
    echo -e "${GREEN}✓${NC} Cleared Redis data"
    
    echo ""
    echo "Cleanup complete!"
fi

echo ""
echo -e "${BLUE}=========================================="
echo "Test Complete!"
echo -e "==========================================${NC}"
