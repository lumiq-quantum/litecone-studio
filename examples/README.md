# Examples and Testing

This directory contains example workflows, mock agents, and comprehensive testing tools for the Centralized Executor and HTTP-Kafka Bridge.

## Quick Start

### Run End-to-End Test

The easiest way to test the complete system:

```bash
./examples/run_e2e_test.sh
```

This automated script will:
1. Start all required services (Kafka, PostgreSQL, mock agents)
2. Initialize the database
3. Execute a test workflow
4. Verify results
5. Offer cleanup

### Manual Testing

For more control over the testing process:

```bash
# 1. Start base services
docker-compose up -d

# 2. Start test services (mock agents)
docker-compose -f docker-compose.test.yml up -d

# 3. Start bridge
docker-compose --profile bridge up -d

# 4. Run test
python examples/e2e_test.py
```

## Files Overview

### Workflow Definitions
- **`sample_workflow.json`** - 2-step research-and-write workflow
- **`sample_workflow_input.json`** - Example input data

### Testing Tools
- **`mock_agent.py`** - Configurable mock A2A agent server
- **`e2e_test.py`** - Comprehensive end-to-end test
- **`simple_e2e_test.py`** - Simplified test (minimal dependencies)
- **`run_e2e_test.sh`** - Automated test runner script

### Documentation
- **`TESTING.md`** - Comprehensive testing guide
- **`workflow_README.md`** - Workflow structure documentation
- **`config_example.py`** - Configuration examples
- **`logging_example.py`** - Logging examples

## Mock Agent

The mock agent simulates A2A-compliant HTTP agents for testing.

### Basic Usage

```bash
# Start ResearchAgent on port 8081
AGENT_NAME=ResearchAgent AGENT_PORT=8081 python examples/mock_agent.py

# Start WriterAgent on port 8082
AGENT_NAME=WriterAgent AGENT_PORT=8082 python examples/mock_agent.py
```

### Test Agent

```bash
curl -X POST http://localhost:8081 \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-123",
    "input": {"topic": "AI", "depth": "basic"}
  }'
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_NAME` | MockAgent | Agent name (affects response format) |
| `AGENT_PORT` | 8080 | HTTP port |
| `AGENT_DELAY_MS` | 0 | Simulated processing delay |
| `AGENT_ERROR_MODE` | none | Error mode: none, 4xx, 5xx, timeout |
| `AGENT_ERROR_RATE` | 0.0 | Error probability (0.0 to 1.0) |

### Testing Error Scenarios

```bash
# Simulate 50% failure rate with 5xx errors
AGENT_NAME=ResearchAgent \
  AGENT_ERROR_MODE=5xx \
  AGENT_ERROR_RATE=0.5 \
  python examples/mock_agent.py

# Simulate timeouts
AGENT_NAME=ResearchAgent \
  AGENT_ERROR_MODE=timeout \
  python examples/mock_agent.py
```

## Testing Scenarios

### 1. Successful Workflow

```bash
./examples/run_e2e_test.sh
```

### 2. Workflow with Delays

```bash
# Start slow agents
AGENT_NAME=ResearchAgent AGENT_DELAY_MS=2000 AGENT_PORT=8081 python examples/mock_agent.py &
AGENT_NAME=WriterAgent AGENT_DELAY_MS=3000 AGENT_PORT=8082 python examples/mock_agent.py &

# Run test
python examples/simple_e2e_test.py
```

### 3. Error Handling

```bash
# Start failing agent
AGENT_NAME=ResearchAgent AGENT_ERROR_MODE=5xx AGENT_ERROR_RATE=1.0 AGENT_PORT=8081 python examples/mock_agent.py &

# Run test (should fail and retry)
python examples/simple_e2e_test.py
```

### 4. Workflow Resume

Test stateful resume after failure:

```bash
# 1. Run with failing WriterAgent
AGENT_NAME=WriterAgent AGENT_ERROR_MODE=5xx AGENT_ERROR_RATE=1.0 AGENT_PORT=8082 python examples/mock_agent.py &
RUN_ID="resume-test-001" python examples/simple_e2e_test.py

# 2. Fix agent and rerun with same RUN_ID
AGENT_NAME=WriterAgent AGENT_PORT=8082 python examples/mock_agent.py &
RUN_ID="resume-test-001" python examples/simple_e2e_test.py
# Should skip completed step 1 and retry step 2
```

## Verifying Results

### Database Queries

```bash
# Check workflow status
docker exec postgres psql -U workflow_user -d workflow_db -c \
  "SELECT * FROM workflow_runs WHERE run_id = 'your-run-id';"

# Check step executions
docker exec postgres psql -U workflow_user -d workflow_db -c \
  "SELECT step_id, agent_name, status FROM step_executions 
   WHERE run_id = 'your-run-id' ORDER BY started_at;"
```

### Kafka Monitoring

```bash
# Monitor tasks
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orchestrator.tasks.http \
  --from-beginning

# Monitor results
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic results.topic \
  --from-beginning
```

## Docker Services

### Base Services

```bash
# Start Kafka and PostgreSQL
docker-compose up -d zookeeper kafka postgres
```

### Test Services

```bash
# Start mock agents and agent registry
docker-compose -f docker-compose.test.yml up -d
```

### Application Services

```bash
# Start bridge
docker-compose --profile bridge up -d

# Start executor (for specific workflow)
docker-compose --profile executor up -d
```

### Health Checks

```bash
# Check all services
curl http://localhost:8081/health  # ResearchAgent
curl http://localhost:8082/health  # WriterAgent
curl http://localhost:8080/health  # Agent Registry
docker exec postgres pg_isready -U workflow_user
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose logs kafka
docker-compose logs postgres
docker-compose -f docker-compose.test.yml logs research-agent
```

### Workflow Not Executing

```bash
# Check bridge is consuming
docker-compose logs bridge

# Check agents are responding
curl http://localhost:8081/health
curl http://localhost:8082/health

# Check agent registry
curl http://localhost:8080/agents/ResearchAgent
```

### Database Issues

```bash
# Check database connection
docker exec postgres pg_isready -U workflow_user

# Verify schema
docker exec postgres psql -U workflow_user -d workflow_db -c "\dt"
```

## Cleanup

```bash
# Stop all services
docker-compose down
docker-compose -f docker-compose.test.yml down

# Remove volumes
docker-compose down -v

# Clean database
docker exec postgres psql -U workflow_user -d workflow_db -c \
  "TRUNCATE workflow_runs, step_executions CASCADE;"
```

## More Information

- See **`TESTING.md`** for comprehensive testing guide
- See **`workflow_README.md`** for workflow structure details
- See **`../README.md`** for project overview
