# API-Executor Integration Quick Start

This guide will help you quickly set up and test the integration between the Workflow Management API and the Centralized Executor.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for running tests)
- Required Python packages: `kafka-python`, `psycopg2-binary`, `requests`

## Step 1: Start Core Services

Start Kafka and PostgreSQL:

```bash
docker-compose up -d kafka postgres
```

Wait for services to be ready (about 30 seconds):

```bash
# Check Kafka
docker-compose logs kafka | grep "started (kafka.server.KafkaServer)"

# Check PostgreSQL
docker-compose logs postgres | grep "database system is ready to accept connections"
```

## Step 2: Run Database Migrations

Apply database migrations to create the required tables:

```bash
# If using the API service
docker-compose --profile api run --rm api alembic upgrade head

# Or manually with alembic
cd api
alembic upgrade head
```

## Step 3: Start the Execution Consumer

Start the execution consumer service that will process workflow execution requests:

```bash
docker-compose --profile consumer up -d execution-consumer
```

Check the logs to ensure it's running:

```bash
docker-compose logs -f execution-consumer
```

You should see:
```
Starting Execution Consumer Service
Initializing Kafka consumer
Kafka consumer initialized successfully
Starting ExecutionConsumer main loop
```

## Step 4: Start the API (Optional)

If you want to test via the REST API:

```bash
docker-compose --profile api up -d api
```

Check the API is running:

```bash
curl http://localhost:8000/health
```

## Step 5: Start the Bridge Service (Optional)

If your workflow uses HTTP agents:

```bash
docker-compose --profile bridge up -d bridge
```

## Step 6: Run Integration Test

Run the integration test to verify everything is working:

```bash
# Install test dependencies
pip install kafka-python psycopg2-binary requests

# Run the test
python test_api_executor_integration.py
```

Expected output:
```
============================================================
API-Executor Integration Test
============================================================
Connecting to database...
✓ Database connected
Connecting to Kafka at localhost:9092
✓ Kafka connected

Creating test workflow via API...
✓ Workflow created with ID: 123e4567-e89b-12d3-a456-426614174000

Triggering workflow execution...
✓ Execution request published for run_id: run-123e4567-e89b-12d3-a456-426614174000

Monitoring execution (timeout: 120s)...
  Status: PENDING
  Status: RUNNING
  Status: COMPLETED
  Completed at: 2024-01-15 10:30:45.123456

✓ Workflow completed successfully

Verifying database records...
✓ Workflow run record found:
  - run_id: run-123e4567-e89b-12d3-a456-426614174000
  - workflow_id: wf-integration-test-workflow-1
  - status: COMPLETED
  - created_at: 2024-01-15 10:30:00.123456
  - completed_at: 2024-01-15 10:30:45.123456

✓ Found 1 step execution records:
  - Step step1 (test-agent): COMPLETED
    Input keys: ['test_input']
    Output keys: ['result']

✓ Database records verified

Cleaning up...
✓ Cleanup complete

============================================================
✓ INTEGRATION TEST PASSED
============================================================

The API-Executor integration is working correctly:
- Execution requests are consumed from Kafka
- Executor processes workflows
- Run status is written back to database
```

## Step 7: Test via API (Optional)

If you started the API service, you can test the full flow:

### 1. Create a workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-test-workflow",
    "description": "My test workflow",
    "start_step": "step1",
    "steps": {
      "step1": {
        "id": "step1",
        "agent_name": "echo-agent",
        "next_step": null,
        "input_mapping": {
          "message": "$.workflow_input.message"
        }
      }
    }
  }'
```

Save the `id` from the response.

### 2. Trigger execution

```bash
curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "message": "Hello, World!"
    }
  }'
```

Save the `run_id` from the response.

### 3. Monitor execution

```bash
# Get run status
curl http://localhost:8000/api/v1/runs/{run_id}

# Get step executions
curl http://localhost:8000/api/v1/runs/{run_id}/steps
```

### 4. Cancel execution (if needed)

```bash
curl -X POST http://localhost:8000/api/v1/runs/{run_id}/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Testing cancellation"
  }'
```

## Troubleshooting

### Execution Consumer Not Starting

Check logs:
```bash
docker-compose logs execution-consumer
```

Common issues:
- Kafka not ready: Wait longer for Kafka to start
- Database connection failed: Check DATABASE_URL in .env
- Missing environment variables: Check .env file

### Workflow Stuck in PENDING

Check if execution consumer is running:
```bash
docker-compose ps execution-consumer
```

Check Kafka topic for messages:
```bash
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic workflow.execution.requests \
  --from-beginning
```

### Workflow Failed

Check the error message in the database:
```sql
SELECT run_id, workflow_name, status, error_message
FROM workflow_runs
WHERE status = 'FAILED'
ORDER BY created_at DESC
LIMIT 5;
```

Check executor logs:
```bash
docker-compose logs execution-consumer | grep ERROR
```

### Database Connection Issues

Verify PostgreSQL is running:
```bash
docker-compose ps postgres
```

Test connection:
```bash
docker-compose exec postgres psql -U workflow_user -d workflow_db -c "SELECT 1;"
```

## Stopping Services

Stop all services:
```bash
docker-compose --profile api --profile consumer --profile bridge down
```

Stop and remove volumes (WARNING: deletes all data):
```bash
docker-compose --profile api --profile consumer --profile bridge down -v
```

## Next Steps

- Read [API_EXECUTOR_INTEGRATION.md](API_EXECUTOR_INTEGRATION.md) for detailed architecture
- Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API reference
- See [WORKFLOW_FORMAT.md](WORKFLOW_FORMAT.md) for workflow definition format
- Review [TESTING_ARCHITECTURE.md](TESTING_ARCHITECTURE.md) for testing guidelines

## Architecture Overview

```
API → Kafka (execution requests) → Execution Consumer → Centralized Executor → Database
                                                              ↓
                                                         Kafka (agent tasks)
                                                              ↓
                                                         Bridge Service
                                                              ↓
                                                         HTTP Agents
```

The integration enables:
1. **Asynchronous Execution**: API returns immediately, executor processes in background
2. **Scalability**: Multiple consumer instances can process workflows in parallel
3. **Reliability**: Kafka provides message persistence and delivery guarantees
4. **Observability**: Database tracks execution state, Kafka provides real-time updates
5. **Fault Tolerance**: Workflows can be retried from last completed step
