# Testing Guide

This guide explains how to test the Centralized Executor and HTTP-Kafka Bridge using the provided testing tools.

## Testing Tools

### Mock Agent (`mock_agent.py`)

A configurable HTTP server that simulates A2A-compliant agents for testing.

**Features:**
- Accepts A2A-compliant HTTP POST requests
- Returns mock responses based on agent name
- Configurable delay simulation
- Configurable error modes (4xx, 5xx, timeout)
- Health check endpoint

**Configuration via environment variables:**

```bash
AGENT_NAME=ResearchAgent      # Agent name (affects response format)
AGENT_PORT=8080               # HTTP port
AGENT_DELAY_MS=100            # Simulated processing delay
AGENT_ERROR_MODE=none         # Error mode: none, 4xx, 5xx, timeout
AGENT_ERROR_RATE=0.0          # Error probability (0.0 to 1.0)
```

**Running mock agents:**

```bash
# Start ResearchAgent
AGENT_NAME=ResearchAgent AGENT_PORT=8081 python examples/mock_agent.py

# Start WriterAgent
AGENT_NAME=WriterAgent AGENT_PORT=8082 python examples/mock_agent.py
```

**Test the agent:**

```bash
curl -X POST http://localhost:8081 \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-123",
    "input": {
      "topic": "AI in Healthcare",
      "depth": "comprehensive"
    }
  }'
```

### End-to-End Test Script (`e2e_test.py`)

Comprehensive test that verifies the complete workflow execution.

**What it tests:**
- Workflow submission
- Step execution via Kafka
- Database persistence
- Monitoring updates
- Result verification

**Usage:**

```bash
# Ensure services are running
docker-compose up -d

# Run the test
python examples/e2e_test.py
```

### Simplified Test (`simple_e2e_test.py`)

A simpler version that tests workflow execution without requiring full Docker setup.

**Usage:**

```bash
# Requires only Kafka and PostgreSQL
python examples/simple_e2e_test.py
```

### Automated Test Runner (`run_e2e_test.sh`)

Bash script that orchestrates the complete end-to-end test.

**What it does:**
1. Starts all required services (Kafka, PostgreSQL, mock agents)
2. Initializes database schema
3. Starts executor and bridge services
4. Executes test workflow
5. Verifies results
6. Offers cleanup

**Usage:**

```bash
./examples/run_e2e_test.sh
```

## Testing Scenarios

### 1. Basic Workflow Execution

Test a successful 2-step workflow:

```bash
# Start services
docker-compose up -d
docker-compose -f docker-compose.test.yml up -d

# Run test
python examples/e2e_test.py
```

### 2. Test with Processing Delays

Simulate slow agents:

```bash
# Start agents with delays
AGENT_NAME=ResearchAgent AGENT_DELAY_MS=2000 AGENT_PORT=8081 python examples/mock_agent.py &
AGENT_NAME=WriterAgent AGENT_DELAY_MS=3000 AGENT_PORT=8082 python examples/mock_agent.py &

# Run workflow
python examples/simple_e2e_test.py
```

### 3. Test Error Handling

Simulate agent failures:

```bash
# 50% chance of 5xx errors
AGENT_NAME=ResearchAgent AGENT_ERROR_MODE=5xx AGENT_ERROR_RATE=0.5 AGENT_PORT=8081 python examples/mock_agent.py &

# Run workflow (should retry and potentially fail)
python examples/simple_e2e_test.py
```

### 4. Test Timeout Handling

Simulate agent timeouts:

```bash
# Agent will timeout
AGENT_NAME=ResearchAgent AGENT_ERROR_MODE=timeout AGENT_PORT=8081 python examples/mock_agent.py &

# Run workflow (should timeout and fail)
python examples/simple_e2e_test.py
```

### 5. Test Workflow Resume

Test stateful resume after failure:

```bash
# 1. Start workflow (will fail at step 2)
AGENT_NAME=WriterAgent AGENT_ERROR_MODE=5xx AGENT_ERROR_RATE=1.0 AGENT_PORT=8082 python examples/mock_agent.py &
python examples/simple_e2e_test.py

# 2. Fix the agent and restart with same run_id
AGENT_NAME=WriterAgent AGENT_PORT=8082 python examples/mock_agent.py &
# Executor should skip completed step 1 and retry step 2
```

## Verifying Results

### Check Workflow Status

Query the database:

```bash
docker exec postgres psql -U workflow_user -d workflow_db -c \
  "SELECT * FROM workflow_runs WHERE run_id = 'your-run-id';"
```

### Check Step Executions

```bash
docker exec postgres psql -U workflow_user -d workflow_db -c \
  "SELECT step_id, agent_name, status, input_data, output_data 
   FROM step_executions WHERE run_id = 'your-run-id' ORDER BY started_at;"
```

### Monitor Kafka Messages

```bash
# Monitor task messages
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orchestrator.tasks.http \
  --from-beginning

# Monitor result messages
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic results.topic \
  --from-beginning

# Monitor status updates
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic workflow.monitoring.updates \
  --from-beginning
```

## Docker Compose Testing

### Start All Services

```bash
# Base services (Kafka, PostgreSQL)
docker-compose up -d

# Test services (mock agents, agent registry)
docker-compose -f docker-compose.test.yml up -d

# Application services
docker-compose --profile bridge up -d
docker-compose --profile executor up -d
```

### Check Service Health

```bash
# Kafka
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# PostgreSQL
docker exec postgres pg_isready -U workflow_user

# Mock agents
curl http://localhost:8081/health
curl http://localhost:8082/health

# Agent registry
curl http://localhost:8080/health
curl http://localhost:8080/agents/ResearchAgent
```

### View Logs

```bash
# Executor logs
docker-compose logs -f executor

# Bridge logs
docker-compose logs -f bridge

# Mock agent logs
docker-compose -f docker-compose.test.yml logs -f research-agent
```

## Troubleshooting

### Services Not Starting

Check service logs:
```bash
docker-compose logs kafka
docker-compose logs postgres
docker-compose -f docker-compose.test.yml logs research-agent
```

### Workflow Not Executing

1. Check if bridge is consuming tasks:
```bash
docker-compose logs bridge
```

2. Check if mock agents are responding:
```bash
curl http://localhost:8081/health
curl http://localhost:8082/health
```

3. Check agent registry:
```bash
curl http://localhost:8080/agents/ResearchAgent
```

### Database Connection Issues

Verify database is accessible:
```bash
docker exec postgres pg_isready -U workflow_user
```

Check connection string in `.env` file.

### Kafka Connection Issues

Check if Kafka is ready:
```bash
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

Check topic creation:
```bash
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

## Performance Testing

### Load Testing

Test with multiple concurrent workflows:

```bash
# Start services
docker-compose up -d
docker-compose -f docker-compose.test.yml up -d

# Run multiple workflows in parallel
for i in {1..10}; do
  RUN_ID="load-test-$i" python examples/simple_e2e_test.py &
done

wait
```

### Latency Testing

Measure end-to-end latency:

```bash
# Add timing to test script
time python examples/simple_e2e_test.py
```

## Cleanup

Stop all services:

```bash
docker-compose down
docker-compose -f docker-compose.test.yml down
```

Remove volumes:

```bash
docker-compose down -v
```

Clean up database:

```bash
docker exec postgres psql -U workflow_user -d workflow_db -c "TRUNCATE workflow_runs, step_executions CASCADE;"
```
