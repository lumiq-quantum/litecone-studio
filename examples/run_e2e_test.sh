#!/bin/bash
# End-to-End Test Runner Script
# 
# This script orchestrates the complete end-to-end test:
# 1. Starts all required services (Kafka, PostgreSQL, mock agents)
# 2. Waits for services to be ready
# 3. Runs the executor and bridge
# 4. Executes the test script
# 5. Cleans up

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "End-to-End Workflow Execution Test"
echo "=========================================="

# Step 1: Start base services
echo -e "\n${YELLOW}Step 1: Starting base services (Kafka, PostgreSQL)${NC}"
docker-compose up -d zookeeper kafka postgres

# Wait for services to be ready
echo -e "\n${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Check Kafka
echo "Checking Kafka..."
timeout 30 bash -c 'until docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; do sleep 1; done' || {
    echo -e "${RED}Kafka failed to start${NC}"
    exit 1
}
echo -e "${GREEN}✓ Kafka is ready${NC}"

# Check PostgreSQL
echo "Checking PostgreSQL..."
timeout 30 bash -c 'until docker exec postgres pg_isready -U workflow_user &> /dev/null; do sleep 1; done' || {
    echo -e "${RED}PostgreSQL failed to start${NC}"
    exit 1
}
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"

# Initialize database schema
echo -e "\n${YELLOW}Initializing database schema...${NC}"
docker exec postgres psql -U workflow_user -d workflow_db -c "
CREATE TABLE IF NOT EXISTS workflow_runs (
  run_id VARCHAR(255) PRIMARY KEY,
  workflow_id VARCHAR(255) NOT NULL,
  workflow_name VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS step_executions (
  id SERIAL PRIMARY KEY,
  run_id VARCHAR(255) NOT NULL REFERENCES workflow_runs(run_id),
  step_id VARCHAR(255) NOT NULL,
  step_name VARCHAR(255) NOT NULL,
  agent_name VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL,
  input_data JSONB NOT NULL,
  output_data JSONB,
  started_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  error_message TEXT,
  UNIQUE(run_id, step_id)
);

CREATE INDEX IF NOT EXISTS idx_run_status ON workflow_runs(status);
CREATE INDEX IF NOT EXISTS idx_step_run_id ON step_executions(run_id);
CREATE INDEX IF NOT EXISTS idx_step_status ON step_executions(status);
" || {
    echo -e "${RED}Failed to initialize database${NC}"
    exit 1
}
echo -e "${GREEN}✓ Database schema initialized${NC}"

# Step 2: Start mock agents and agent registry
echo -e "\n${YELLOW}Step 2: Starting mock agents and agent registry${NC}"
docker-compose -f docker-compose.test.yml up -d research-agent writer-agent agent-registry

# Wait for mock agents to be ready
echo "Waiting for mock agents..."
sleep 5

# Check mock agents
for agent in research-agent writer-agent; do
    echo "Checking $agent..."
    timeout 30 bash -c "until curl -s http://localhost:808${agent: -1}/health &> /dev/null; do sleep 1; done" || {
        echo -e "${RED}$agent failed to start${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ $agent is ready${NC}"
done

# Check agent registry
echo "Checking agent-registry..."
timeout 30 bash -c 'until curl -s http://localhost:8080/health &> /dev/null; do sleep 1; done' || {
    echo -e "${RED}agent-registry failed to start${NC}"
    exit 1
}
echo -e "${GREEN}✓ agent-registry is ready${NC}"

# Step 3: Start bridge service
echo -e "\n${YELLOW}Step 3: Starting External Agent Executor (bridge)${NC}"
docker-compose --profile bridge up -d bridge

sleep 5
echo -e "${GREEN}✓ Bridge service started${NC}"

# Step 4: Start executor and run test
echo -e "\n${YELLOW}Step 4: Running workflow execution test${NC}"

# Generate unique run ID
RUN_ID="test-run-$(date +%s)"

# Read workflow files
WORKFLOW_PLAN=$(cat examples/sample_workflow.json)
WORKFLOW_INPUT=$(cat examples/sample_workflow_input.json)

# Start executor in background
echo "Starting executor with run_id: $RUN_ID"
docker-compose --profile executor up -d executor

# Set environment variables for executor
docker exec centralized-executor sh -c "
export RUN_ID='$RUN_ID'
export WORKFLOW_PLAN='$WORKFLOW_PLAN'
export WORKFLOW_INPUT='$WORKFLOW_INPUT'
python -m src.executor.centralized_executor
" &

EXECUTOR_PID=$!

# Wait for execution to complete (with timeout)
echo "Waiting for workflow execution to complete..."
TIMEOUT=120
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    # Check if workflow is complete in database
    STATUS=$(docker exec postgres psql -U workflow_user -d workflow_db -t -c "SELECT status FROM workflow_runs WHERE run_id = '$RUN_ID';" 2>/dev/null | xargs || echo "")
    
    if [ "$STATUS" = "COMPLETED" ]; then
        echo -e "${GREEN}✓ Workflow completed successfully${NC}"
        break
    elif [ "$STATUS" = "FAILED" ]; then
        echo -e "${RED}✗ Workflow failed${NC}"
        exit 1
    fi
    
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo -e "${RED}✗ Workflow execution timed out${NC}"
    exit 1
fi

# Step 5: Verify results
echo -e "\n${YELLOW}Step 5: Verifying results${NC}"

# Check workflow run record
echo "Checking workflow run record..."
docker exec postgres psql -U workflow_user -d workflow_db -c "SELECT * FROM workflow_runs WHERE run_id = '$RUN_ID';"

# Check step execution records
echo -e "\nChecking step execution records..."
docker exec postgres psql -U workflow_user -d workflow_db -c "SELECT step_id, agent_name, status FROM step_executions WHERE run_id = '$RUN_ID' ORDER BY started_at;"

# Step 6: Cleanup
echo -e "\n${YELLOW}Step 6: Cleaning up${NC}"
read -p "Do you want to stop all services? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose down
    docker-compose -f docker-compose.test.yml down
    echo -e "${GREEN}✓ Services stopped${NC}"
fi

echo -e "\n=========================================="
echo -e "${GREEN}✓ END-TO-END TEST COMPLETED${NC}"
echo -e "=========================================="
