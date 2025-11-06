# Manual Testing Guide

This guide will walk you through manually testing the Centralized Executor and HTTP-Kafka Bridge system.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local testing)
- Terminal access

## Step 1: Set Up Environment

1. **Copy the environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Review the .env file** (optional - defaults should work):
   ```bash
   cat .env
   ```

## Step 2: Start Infrastructure Services

Start Kafka, Zookeeper, and PostgreSQL:

```bash
docker-compose up -d zookeeper kafka postgres
```

**Wait for services to be ready** (about 30 seconds):
```bash
# Check Kafka
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Check PostgreSQL
docker exec postgres pg_isready -U workflow_user
```

## Step 3: Start Test Services (Mock Agents)

Start the mock agents and agent registry:

```bash
docker-compose -f docker-compose.test.yml up -d
```

**Verify agents are running:**
```bash
# Check ResearchAgent
curl http://localhost:8081/health

# Check WriterAgent
curl http://localhost:8082/health

# Check Agent Registry
curl http://localhost:8080/health
curl http://localhost:8080/agents/ResearchAgent
```

Expected response from agent registry:
```json
{
  "name": "ResearchAgent",
  "url": "http://research-agent:8080",
  "auth_config": null,
  "timeout": 30000,
  "retry_config": {
    "max_retries": 3,
    "initial_delay_ms": 100,
    "max_delay_ms": 5000,
    "backoff_multiplier": 2.0
  }
}
```

## Step 4: Start the HTTP-Kafka Bridge

Start the bridge service that will handle agent invocations:

```bash
docker-compose --profile bridge up -d
```

**Monitor bridge logs:**
```bash
docker-compose logs -f bridge
```

You should see:
```
Starting External Agent Executor (HTTP-Kafka Bridge)
Kafka consumer connected to topic 'orchestrator.tasks.http'
```

Press `Ctrl+C` to stop following logs (bridge keeps running).

## Step 5: Run a Workflow

Now let's execute a workflow! You have two options:

### Option A: Using Docker (Recommended)

1. **Set environment variables for the executor:**
   ```bash
   export RUN_ID="manual-test-$(date +%s)"
   export WORKFLOW_PLAN=$(cat examples/sample_workflow.json)
   export WORKFLOW_INPUT=$(cat examples/sample_workflow_input.json)
   ```

2. **Run the executor:**
   ```bash
   docker-compose run --rm \
     -e RUN_ID="$RUN_ID" \
     -e WORKFLOW_PLAN="$WORKFLOW_PLAN" \
     -e WORKFLOW_INPUT="$WORKFLOW_INPUT" \
     -e KAFKA_BROKERS=kafka:29092 \
     -e DATABASE_URL=postgresql://workflow_user:workflow_pass@postgres:5432/workflow_db \
     -e AGENT_REGISTRY_URL=http://agent-registry:8080 \
     -e LOG_LEVEL=INFO \
     -e LOG_FORMAT=text \
     executor
   ```

### Option B: Using Python Locally

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export RUN_ID="manual-test-$(date +%s)"
   export WORKFLOW_PLAN=$(cat examples/sample_workflow.json)
   export WORKFLOW_INPUT=$(cat examples/sample_workflow_input.json)
   export KAFKA_BROKERS=localhost:9092
   export DATABASE_URL=postgresql://workflow_user:workflow_pass@localhost:5432/workflow_db
   export AGENT_REGISTRY_URL=http://localhost:8080
   export LOG_LEVEL=INFO
   export LOG_FORMAT=text
   ```

3. **Run the executor:**
   ```bash
   python -m src.executor.centralized_executor
   ```

## Step 6: Monitor Execution

### Watch Executor Output

You should see logs like:
```
Starting Centralized Executor
Configuration loaded for run_id=manual-test-1234567890
Loaded workflow plan: research-and-write (v1.0.0), 2 steps
Initializing executor components...
Starting workflow execution...
Executing step 'step-1' (agent: ResearchAgent)
Published agent task for step 'step-1'
Received agent result for step 'step-1'
Step 'step-1' completed successfully
Executing step 'step-2' (agent: WriterAgent)
Published agent task for step 'step-2'
Received agent result for step 'step-2'
Step 'step-2' completed successfully
Workflow execution completed successfully
```

### Monitor Kafka Messages (Optional)

In separate terminals:

**Watch tasks being published:**
```bash
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orchestrator.tasks.http \
  --from-beginning
```

**Watch results being published:**
```bash
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic results.topic \
  --from-beginning
```

**Watch monitoring updates:**
```bash
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic workflow.monitoring.updates \
  --from-beginning
```

## Step 7: Verify Results in Database

Check the workflow execution in the database:

```bash
# Connect to PostgreSQL
docker exec -it postgres psql -U workflow_user -d workflow_db
```

**Query workflow runs:**
```sql
SELECT run_id, workflow_id, status, created_at, completed_at 
FROM workflow_runs 
ORDER BY created_at DESC 
LIMIT 5;
```

**Query step executions:**
```sql
SELECT step_id, agent_name, status, started_at, completed_at
FROM step_executions 
WHERE run_id = 'YOUR_RUN_ID_HERE'
ORDER BY started_at;
```

**View step input/output data:**
```sql
SELECT step_id, agent_name, input_data, output_data
FROM step_executions 
WHERE run_id = 'YOUR_RUN_ID_HERE'
ORDER BY started_at;
```

Exit psql with `\q`

## Step 8: Test Different Scenarios

### Test 1: Workflow with Delays

Restart mock agents with delays:
```bash
docker-compose -f docker-compose.test.yml down
docker-compose -f docker-compose.test.yml up -d
```

Then run another workflow (repeat Step 5).

### Test 2: Test Error Handling

1. **Stop one of the agents to simulate failure:**
   ```bash
   docker stop writer-agent
   ```

2. **Run a workflow** (it should fail at step 2):
   ```bash
   export RUN_ID="error-test-$(date +%s)"
   # Run executor again (Option A or B from Step 5)
   ```

3. **Restart the agent:**
   ```bash
   docker start writer-agent
   ```

4. **Resume the workflow with the same RUN_ID:**
   ```bash
   # Use the same RUN_ID from step 2
   # Run executor again - it should skip step 1 and retry step 2
   ```

### Test 3: Test with Custom Workflow

1. **Create your own workflow JSON:**
   ```bash
   cat > my_workflow.json << 'EOF'
   {
     "workflow_id": "my-workflow-001",
     "name": "my-custom-workflow",
     "version": "1.0.0",
     "start_step": "step-1",
     "steps": {
       "step-1": {
         "id": "step-1",
         "agent_name": "ResearchAgent",
         "next_step": null,
         "input_mapping": {
           "topic": "${workflow.input.topic}"
         }
       }
     }
   }
   EOF
   ```

2. **Create input data:**
   ```bash
   cat > my_input.json << 'EOF'
   {
     "topic": "Machine Learning"
   }
   EOF
   ```

3. **Run with your workflow:**
   ```bash
   export RUN_ID="custom-test-$(date +%s)"
   export WORKFLOW_PLAN=$(cat my_workflow.json)
   export WORKFLOW_INPUT=$(cat my_input.json)
   # Run executor (Option A or B from Step 5)
   ```

## Step 9: View Logs

### Bridge Logs
```bash
docker-compose logs bridge
```

### Mock Agent Logs
```bash
docker-compose -f docker-compose.test.yml logs research-agent
docker-compose -f docker-compose.test.yml logs writer-agent
```

### Kafka Logs
```bash
docker-compose logs kafka
```

### PostgreSQL Logs
```bash
docker-compose logs postgres
```

## Step 10: Cleanup

When you're done testing:

```bash
# Stop all services
docker-compose down
docker-compose -f docker-compose.test.yml down

# Remove volumes (clears database data)
docker-compose down -v

# Remove all containers and networks
docker-compose down --remove-orphans
docker-compose -f docker-compose.test.yml down --remove-orphans
```

## Troubleshooting

### Issue: Kafka not ready
**Solution:** Wait 30-60 seconds after starting Kafka, then check:
```bash
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Issue: Database connection failed
**Solution:** Check PostgreSQL is running:
```bash
docker exec postgres pg_isready -U workflow_user
```

### Issue: Agent Registry not responding
**Solution:** Restart the agent registry:
```bash
docker-compose -f docker-compose.test.yml restart agent-registry
```

### Issue: Bridge not consuming messages
**Solution:** Check bridge logs and restart:
```bash
docker-compose logs bridge
docker-compose restart bridge
```

### Issue: Workflow stuck/timeout
**Solution:** 
1. Check all services are running
2. Check bridge logs for errors
3. Verify agents are responding: `curl http://localhost:8081/health`

## Advanced Testing

### Test with JSON Logging

Set `LOG_FORMAT=json` for structured logs:
```bash
export LOG_FORMAT=json
# Run executor
```

### Test with Debug Logging

Set `LOG_LEVEL=DEBUG` for verbose output:
```bash
export LOG_LEVEL=DEBUG
# Run executor
```

### Monitor All Kafka Topics

```bash
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Clear Database Between Tests

```bash
docker exec postgres psql -U workflow_user -d workflow_db -c \
  "TRUNCATE workflow_runs, step_executions CASCADE;"
```

## Next Steps

- Review the [README.md](README.md) for architecture details
- Check [WORKFLOW_FORMAT.md](WORKFLOW_FORMAT.md) for workflow syntax
- See [A2A_AGENT_INTERFACE.md](A2A_AGENT_INTERFACE.md) for agent implementation
- Explore [examples/TESTING.md](examples/TESTING.md) for automated testing

## Quick Reference

**Start everything:**
```bash
docker-compose up -d
docker-compose -f docker-compose.test.yml up -d
docker-compose --profile bridge up -d
```

**Run a workflow:**
```bash
export RUN_ID="test-$(date +%s)"
export WORKFLOW_PLAN=$(cat examples/sample_workflow.json)
export WORKFLOW_INPUT=$(cat examples/sample_workflow_input.json)
docker-compose run --rm \
  -e RUN_ID="$RUN_ID" \
  -e WORKFLOW_PLAN="$WORKFLOW_PLAN" \
  -e WORKFLOW_INPUT="$WORKFLOW_INPUT" \
  -e KAFKA_BROKERS=kafka:29092 \
  -e DATABASE_URL=postgresql://workflow_user:workflow_pass@postgres:5432/workflow_db \
  -e AGENT_REGISTRY_URL=http://agent-registry:8080 \
  -e LOG_FORMAT=text \
  executor
```

**Stop everything:**
```bash
docker-compose down
docker-compose -f docker-compose.test.yml down
```
