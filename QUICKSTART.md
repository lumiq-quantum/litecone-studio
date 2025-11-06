# Quick Start Guide

Get the Centralized Executor up and running in 2 minutes!

## Fastest Way to Test

Run the automated quick-start script:

```bash
./quick-start.sh
```

This will:
1. ✅ Start Kafka and PostgreSQL
2. ✅ Start mock agents (ResearchAgent, WriterAgent)
3. ✅ Start the HTTP-Kafka Bridge
4. ✅ Execute a sample 2-step workflow
5. ✅ Show you the results

## Manual Step-by-Step

If you prefer to run each step manually:

### 1. Start Infrastructure
```bash
docker-compose up -d zookeeper kafka postgres
```

### 2. Start Mock Agents
```bash
docker-compose -f docker-compose.test.yml up -d
```

### 3. Start Bridge
```bash
docker-compose --profile bridge up -d
```

### 4. Run a Workflow
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

## Verify Results

Check the database:
```bash
docker exec -it postgres psql -U workflow_user -d workflow_db

# In psql:
SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT 1;
SELECT * FROM step_executions WHERE run_id = 'YOUR_RUN_ID' ORDER BY started_at;
\q
```

## View Logs

```bash
# Bridge logs
docker-compose logs bridge

# Agent logs
docker-compose -f docker-compose.test.yml logs research-agent writer-agent

# All logs
docker-compose logs -f
```

## Cleanup

Stop all services:
```bash
./cleanup.sh
```

Remove volumes (deletes database data):
```bash
./cleanup.sh --volumes
```

## What's Running?

After quick-start, you'll have:

| Service | Port | Description |
|---------|------|-------------|
| Kafka | 9092 | Message broker |
| PostgreSQL | 5432 | Workflow state database |
| ResearchAgent | 8081 | Mock agent #1 |
| WriterAgent | 8082 | Mock agent #2 |
| Agent Registry | 8080 | Agent metadata service |
| Bridge | - | HTTP-Kafka adapter (no exposed port) |

## Test Different Scenarios

### Test with Error Handling
```bash
# Stop an agent to simulate failure
docker stop writer-agent

# Run workflow (will fail at step 2)
export RUN_ID="error-test-$(date +%s)"
# ... run executor ...

# Restart agent and retry with same RUN_ID
docker start writer-agent
# ... run executor with same RUN_ID ...
# It will skip completed steps and retry failed ones!
```

### Test with Custom Workflow

Create your own workflow:
```bash
cat > my_workflow.json << 'EOF'
{
  "workflow_id": "my-test",
  "name": "my-workflow",
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

cat > my_input.json << 'EOF'
{
  "topic": "Kubernetes"
}
EOF

export WORKFLOW_PLAN=$(cat my_workflow.json)
export WORKFLOW_INPUT=$(cat my_input.json)
# ... run executor ...
```

## Troubleshooting

**Services not starting?**
```bash
# Check Docker
docker ps

# Check logs
docker-compose logs kafka
docker-compose logs postgres
```

**Workflow stuck?**
```bash
# Check bridge is running
docker-compose logs bridge

# Check agents are responding
curl http://localhost:8081/health
curl http://localhost:8082/health
```

**Database issues?**
```bash
# Check PostgreSQL
docker exec postgres pg_isready -U workflow_user

# Clear database
docker exec postgres psql -U workflow_user -d workflow_db -c \
  "TRUNCATE workflow_runs, step_executions CASCADE;"
```

## Next Steps

- 📖 Read [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md) for detailed testing scenarios
- 📖 See [README.md](README.md) for architecture overview
- 📖 Check [WORKFLOW_FORMAT.md](WORKFLOW_FORMAT.md) for workflow syntax
- 📖 Review [A2A_AGENT_INTERFACE.md](A2A_AGENT_INTERFACE.md) for agent implementation

## Common Commands

```bash
# Start everything
./quick-start.sh

# Stop everything
./cleanup.sh

# View all logs
docker-compose logs -f

# Restart a service
docker-compose restart bridge

# Check service status
docker-compose ps

# Access database
docker exec -it postgres psql -U workflow_user -d workflow_db

# Monitor Kafka topics
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orchestrator.tasks.http \
  --from-beginning
```

## Support

For issues or questions:
1. Check the logs: `docker-compose logs`
2. Review [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md)
3. Check [examples/TESTING.md](examples/TESTING.md)
