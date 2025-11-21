# JSON-RPC 2.0 Development Deployment - Quick Reference

## Service Endpoints

| Service | URL | Status |
|---------|-----|--------|
| ResearchAgent | http://localhost:8081 | ✓ Running |
| WriterAgent | http://localhost:8082 | ✓ Running |
| Agent Registry | http://localhost:8080 | ✓ Running |
| Kafka | localhost:9092 | ✓ Running |
| PostgreSQL | localhost:5432 | ✓ Running |
| Bridge | (internal) | ✓ Running |

## Quick Commands

### Check Service Status
```bash
docker compose ps
docker compose -f docker-compose.test.yml ps
```

### View Bridge Logs
```bash
docker compose logs bridge --tail 50 -f
```

### View Agent Logs
```bash
docker compose -f docker-compose.test.yml logs research-agent --tail 50 -f
docker compose -f docker-compose.test.yml logs writer-agent --tail 50 -f
```

### Test Agent Directly
```bash
# Health check
curl http://localhost:8081/health | python3 -m json.tool

# JSON-RPC request
curl -X POST http://localhost:8081 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-001",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "messageId": "msg-001",
        "parts": [{"kind": "text", "text": "test"}]
      }
    }
  }' | python3 -m json.tool
```

### Send Task via Kafka
```bash
# Using kafka-console-producer
docker exec -i kafka kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic orchestrator.tasks.http << EOF
{
  "run_id": "test-$(date +%s)",
  "task_id": "$(uuidgen)",
  "agent_name": "ResearchAgent",
  "input_data": {"topic": "Test"},
  "correlation_id": "$(uuidgen)"
}
EOF
```

### View Results from Kafka
```bash
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic results.topic \
  --from-beginning \
  --max-messages 5
```

### Run Test Scripts
```bash
# Workflow test
python3 test_workflow_jsonrpc.py

# Error scenarios test
python3 test_error_scenarios.py
```

## Kafka Topics

| Topic | Purpose | Producer | Consumer |
|-------|---------|----------|----------|
| orchestrator.tasks.http | Agent tasks | Executor | Bridge |
| results.topic | Task results | Bridge | Executor |

## JSON-RPC 2.0 Request Format

```json
{
  "jsonrpc": "2.0",
  "id": "<task_id>",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "messageId": "msg-<task_id>",
      "parts": [
        {
          "kind": "text",
          "text": "<input_data_as_json>"
        }
      ]
    }
  }
}
```

## JSON-RPC 2.0 Response Format

```json
{
  "jsonrpc": "2.0",
  "id": "<task_id>",
  "result": {
    "status": {
      "state": "completed",
      "message": "Task completed successfully"
    },
    "artifacts": [
      {
        "kind": "result",
        "parts": [
          {
            "kind": "text",
            "text": "<output_data>"
          }
        ],
        "metadata": {...}
      }
    ],
    "history": [
      {
        "role": "user",
        "messageId": "msg-<task_id>",
        "parts": [...]
      },
      {
        "role": "agent",
        "messageId": "agent-msg-<task_id>",
        "parts": [...]
      }
    ],
    "metadata": {...}
  }
}
```

## Troubleshooting

### Bridge Not Processing Tasks
```bash
# Check bridge logs
docker compose logs bridge --tail 100

# Check Kafka connectivity
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Restart bridge
docker compose restart bridge
```

### Agent Not Responding
```bash
# Check agent health
curl http://localhost:8081/health

# Check agent logs
docker compose -f docker-compose.test.yml logs research-agent --tail 50

# Restart agent
docker compose -f docker-compose.test.yml restart research-agent
```

### No Results in Kafka
```bash
# Check if bridge is publishing
docker compose logs bridge | grep "Publishing result"

# Check Kafka topic
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic results.topic \
  --from-beginning
```

## Cleanup

### Stop All Services
```bash
docker compose down
docker compose -f docker-compose.test.yml down
```

### Remove Volumes
```bash
docker compose down -v
```

### Full Cleanup
```bash
./cleanup.sh
```

## Files Created During Deployment

- `deployment_verification.md` - Deployment verification details
- `error_scenarios_test_results.md` - Error testing results
- `DEPLOYMENT_SUMMARY.md` - Complete deployment summary
- `DEPLOYMENT_QUICK_REFERENCE.md` - This file
- `test_jsonrpc_deployment.py` - Test script
- `test_workflow_jsonrpc.py` - Workflow test script
- `test_error_scenarios.py` - Error test script

## Next Steps

1. Review test results in verification documents
2. Run additional manual tests if needed
3. Proceed to Task 5: Update unit tests
4. Proceed to Task 6: Update integration tests
5. Prepare for production deployment (Task 11)
