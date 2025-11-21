# Circuit Breaker Usage Guide

## Overview

The circuit breaker works **transparently** with your workflows. You configure it at the **agent level**, and it automatically protects all workflows that use that agent. No changes to workflow definitions are needed!

## How It Works

```
Workflow Definition (No Changes Needed)
         ↓
    Uses Agent
         ↓
Agent Has Circuit Breaker Config
         ↓
Circuit Breaker Protects All Calls
```

## Step-by-Step Guide

### Step 1: Configure Agent with Circuit Breaker

First, register your agent with circuit breaker configuration:

#### Option A: Using the UI

1. Navigate to **Agents** page
2. Click **Create Agent**
3. Fill in basic info:
   - Name: `UnreliableProcessorAgent`
   - URL: `https://unreliable-service.example.com/process`
4. Scroll to **Circuit Breaker** section
5. Configure settings:
   ```
   Enabled: ✓
   Failure Threshold: 5
   Failure Rate: 0.5
   Timeout: 60s
   Half-Open Calls: 3
   Window Size: 120s
   ```
6. Click **Create Agent**

#### Option B: Using the API

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "UnreliableProcessorAgent",
    "url": "https://unreliable-service.example.com/process",
    "description": "Data processor with circuit breaker protection",
    "timeout_ms": 30000,
    "retry_config": {
      "max_retries": 3,
      "initial_delay_ms": 1000,
      "max_delay_ms": 10000,
      "backoff_multiplier": 2.0
    },
    "circuit_breaker_config": {
      "enabled": true,
      "failure_threshold": 5,
      "failure_rate_threshold": 0.5,
      "timeout_seconds": 60,
      "half_open_max_calls": 3,
      "window_size_seconds": 120
    }
  }'
```

### Step 2: Create Your Workflow (No Special Configuration)

Your workflow definition remains **exactly the same**. Just reference the agent:

```json
{
  "workflow_id": "data-processing-with-circuit-breaker",
  "name": "Data Processing Workflow",
  "steps": {
    "process-data": {
      "id": "process-data",
      "agent_name": "UnreliableProcessorAgent",
      "input_mapping": {
        "data": "${workflow.input.data}"
      }
    }
  }
}
```

### Step 3: Execute Your Workflow

Execute the workflow normally:

```bash
curl -X POST http://localhost:8000/api/v1/workflows/data-processing-with-circuit-breaker/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "data": {"items": [1, 2, 3, 4, 5]}
    }
  }'
```

### Step 4: Circuit Breaker Works Automatically

The circuit breaker now protects your workflow:

#### Scenario 1: Agent is Healthy
```
Workflow Execution 1: ✓ Success (circuit: CLOSED)
Workflow Execution 2: ✓ Success (circuit: CLOSED)
Workflow Execution 3: ✓ Success (circuit: CLOSED)
```

#### Scenario 2: Agent Starts Failing
```
Workflow Execution 1: ✗ Failed (circuit: CLOSED, failure 1/5)
Workflow Execution 2: ✗ Failed (circuit: CLOSED, failure 2/5)
Workflow Execution 3: ✗ Failed (circuit: CLOSED, failure 3/5)
Workflow Execution 4: ✗ Failed (circuit: CLOSED, failure 4/5)
Workflow Execution 5: ✗ Failed (circuit: CLOSED, failure 5/5)
                      → Circuit OPENS!
```

#### Scenario 3: Circuit is Open
```
Workflow Execution 6: ✗ Failed immediately (circuit: OPEN)
                      "Circuit breaker is OPEN for agent 'UnreliableProcessorAgent'"
                      No HTTP call made - fails in <1ms

Workflow Execution 7: ✗ Failed immediately (circuit: OPEN)
                      Still within 60s timeout period
```

#### Scenario 4: Recovery Testing
```
After 60 seconds...

Workflow Execution 8: Attempting... (circuit: HALF_OPEN, test call 1/3)
                      ✓ Success! Test call 1 passed

Workflow Execution 9: Attempting... (circuit: HALF_OPEN, test call 2/3)
                      ✓ Success! Test call 2 passed

Workflow Execution 10: Attempting... (circuit: HALF_OPEN, test call 3/3)
                       ✓ Success! Test call 3 passed
                       → Circuit CLOSES!

Workflow Execution 11: ✓ Success (circuit: CLOSED)
                       Normal operation resumed
```

## Complete Example

### 1. Register Agents

```bash
# Reliable agent (no special circuit breaker config needed)
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DataFetcherAgent",
    "url": "https://api.example.com/fetch"
  }'

# Unreliable agent (with aggressive circuit breaker)
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "UnreliableProcessorAgent",
    "url": "https://unreliable-service.example.com/process",
    "circuit_breaker_config": {
      "enabled": true,
      "failure_threshold": 3,
      "failure_rate_threshold": 0.7,
      "timeout_seconds": 30,
      "half_open_max_calls": 2,
      "window_size_seconds": 60
    }
  }'

# Storage agent (with lenient circuit breaker)
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "StorageAgent",
    "url": "https://storage.example.com/store",
    "circuit_breaker_config": {
      "enabled": true,
      "failure_threshold": 10,
      "failure_rate_threshold": 0.3,
      "timeout_seconds": 120,
      "half_open_max_calls": 5,
      "window_size_seconds": 300
    }
  }'
```

### 2. Create Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @examples/circuit_breaker_workflow_example.json
```

### 3. Execute Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/data-processing-with-circuit-breaker/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "data_source": "database",
      "query": "SELECT * FROM users",
      "validation_schema": "user_schema_v1",
      "processing_options": {
        "transform": "normalize",
        "filter": "active_only"
      },
      "destination": "s3://bucket/processed/"
    }
  }'
```

### 4. Monitor Execution

```bash
# Get run status
curl http://localhost:8000/api/v1/runs/{run_id}

# Check logs for circuit breaker events
docker-compose logs bridge | grep -i circuit
```

## Real-World Scenarios

### Scenario 1: E-commerce Order Processing

**Agents:**
- `PaymentGatewayAgent` - Critical, aggressive circuit breaker
- `InventoryAgent` - Important, moderate circuit breaker
- `EmailAgent` - Non-critical, lenient circuit breaker

**Configuration:**

```json
{
  "PaymentGatewayAgent": {
    "circuit_breaker_config": {
      "enabled": true,
      "failure_threshold": 2,
      "failure_rate_threshold": 0.8,
      "timeout_seconds": 30,
      "half_open_max_calls": 1,
      "window_size_seconds": 60
    }
  },
  "InventoryAgent": {
    "circuit_breaker_config": {
      "enabled": true,
      "failure_threshold": 5,
      "failure_rate_threshold": 0.5,
      "timeout_seconds": 60,
      "half_open_max_calls": 3,
      "window_size_seconds": 120
    }
  },
  "EmailAgent": {
    "circuit_breaker_config": {
      "enabled": true,
      "failure_threshold": 10,
      "failure_rate_threshold": 0.3,
      "timeout_seconds": 120,
      "half_open_max_calls": 5,
      "window_size_seconds": 300
    }
  }
}
```

**Workflow:**

```json
{
  "workflow_id": "order-processing",
  "steps": {
    "validate-order": {
      "id": "validate-order",
      "agent_name": "ValidationAgent",
      "input_mapping": {
        "order": "${workflow.input.order}"
      },
      "next_step": "check-inventory"
    },
    "check-inventory": {
      "id": "check-inventory",
      "agent_name": "InventoryAgent",
      "input_mapping": {
        "items": "${validate-order.output.items}"
      },
      "next_step": "process-payment"
    },
    "process-payment": {
      "id": "process-payment",
      "agent_name": "PaymentGatewayAgent",
      "input_mapping": {
        "amount": "${validate-order.output.total}",
        "payment_method": "${workflow.input.payment_method}"
      },
      "next_step": "send-confirmation"
    },
    "send-confirmation": {
      "id": "send-confirmation",
      "agent_name": "EmailAgent",
      "input_mapping": {
        "to": "${workflow.input.customer_email}",
        "order_id": "${workflow.input.order_id}"
      }
    }
  }
}
```

**Behavior:**
- If `PaymentGatewayAgent` fails 2 times → Circuit opens immediately (critical)
- If `InventoryAgent` fails 5 times → Circuit opens (important)
- If `EmailAgent` fails 10 times → Circuit opens (non-critical, can tolerate more failures)

### Scenario 2: Data Pipeline with Fallback

**Workflow with Conditional Logic:**

```json
{
  "workflow_id": "data-pipeline-with-fallback",
  "steps": {
    "fetch-from-primary": {
      "id": "fetch-from-primary",
      "agent_name": "PrimaryDataSourceAgent",
      "input_mapping": {
        "query": "${workflow.input.query}"
      },
      "next_step": "check-primary-success"
    },
    "check-primary-success": {
      "id": "check-primary-success",
      "type": "conditional",
      "condition": {
        "expression": "${fetch-from-primary.status} == 'SUCCESS'"
      },
      "then_step": "process-data",
      "else_step": "fetch-from-secondary"
    },
    "fetch-from-secondary": {
      "id": "fetch-from-secondary",
      "agent_name": "SecondaryDataSourceAgent",
      "input_mapping": {
        "query": "${workflow.input.query}"
      },
      "next_step": "process-data"
    },
    "process-data": {
      "id": "process-data",
      "agent_name": "ProcessorAgent",
      "input_mapping": {
        "data": "${fetch-from-primary.output.data || fetch-from-secondary.output.data}"
      }
    }
  }
}
```

**Behavior:**
- Try primary data source
- If circuit is open or call fails → Automatically try secondary
- Circuit breaker prevents wasting time on failing primary source

### Scenario 3: Parallel Processing with Circuit Breaker

**Workflow:**

```json
{
  "workflow_id": "parallel-processing-protected",
  "steps": {
    "parallel-fetch": {
      "id": "parallel-fetch",
      "type": "parallel",
      "parallel_steps": ["fetch-users", "fetch-orders", "fetch-products"],
      "next_step": "aggregate-results"
    },
    "fetch-users": {
      "id": "fetch-users",
      "agent_name": "UserServiceAgent",
      "input_mapping": {
        "filter": "${workflow.input.user_filter}"
      }
    },
    "fetch-orders": {
      "id": "fetch-orders",
      "agent_name": "OrderServiceAgent",
      "input_mapping": {
        "filter": "${workflow.input.order_filter}"
      }
    },
    "fetch-products": {
      "id": "fetch-products",
      "agent_name": "ProductServiceAgent",
      "input_mapping": {
        "filter": "${workflow.input.product_filter}"
      }
    },
    "aggregate-results": {
      "id": "aggregate-results",
      "agent_name": "AggregatorAgent",
      "input_mapping": {
        "users": "${fetch-users.output}",
        "orders": "${fetch-orders.output}",
        "products": "${fetch-products.output}"
      }
    }
  }
}
```

**Behavior:**
- All three services called in parallel
- If `OrderServiceAgent` circuit is open → That parallel step fails immediately
- Other parallel steps continue normally
- Circuit breaker prevents one failing service from slowing down the entire parallel block

## Monitoring Circuit Breaker

### Check Circuit Breaker State

```bash
# View circuit breaker state in Redis
docker exec redis redis-cli KEYS "circuit_breaker:*:state"

# Get state for specific agent
docker exec redis redis-cli GET "circuit_breaker:UnreliableProcessorAgent:state"
```

### View Circuit Breaker Logs

```bash
# Filter logs for circuit breaker events
docker-compose logs bridge | grep -i "circuit breaker"

# Example output:
# Circuit breaker OPENED for agent 'UnreliableProcessorAgent' due to failures
# Circuit breaker transitioned to HALF_OPEN for agent 'UnreliableProcessorAgent'
# Circuit breaker transitioned to CLOSED for agent 'UnreliableProcessorAgent' after 3 successful test calls
```

### Monitor Workflow Failures

```bash
# Get failed runs
curl http://localhost:8000/api/v1/runs?status=FAILED

# Check if failure was due to circuit breaker
curl http://localhost:8000/api/v1/runs/{run_id}
# Look for error message: "Circuit breaker is OPEN for agent '...'"
```

## Best Practices

### 1. Configure Based on Agent Characteristics

**Critical Services** (payment, authentication):
```json
{
  "failure_threshold": 2,
  "failure_rate_threshold": 0.8,
  "timeout_seconds": 30
}
```

**Standard Services** (data fetching, processing):
```json
{
  "failure_threshold": 5,
  "failure_rate_threshold": 0.5,
  "timeout_seconds": 60
}
```

**Non-Critical Services** (logging, analytics):
```json
{
  "failure_threshold": 10,
  "failure_rate_threshold": 0.3,
  "timeout_seconds": 120
}
```

### 2. Combine with Retry Logic

Circuit breaker works best with retry configuration:

```json
{
  "retry_config": {
    "max_retries": 3,
    "initial_delay_ms": 1000,
    "max_delay_ms": 10000,
    "backoff_multiplier": 2.0
  },
  "circuit_breaker_config": {
    "enabled": true,
    "failure_threshold": 5,
    "failure_rate_threshold": 0.5,
    "timeout_seconds": 60
  }
}
```

**Flow:**
1. Call fails → Retry 3 times with backoff
2. All retries fail → Count as 1 failure for circuit breaker
3. After 5 such failures → Circuit opens
4. Circuit open → No retries attempted (fails immediately)

### 3. Test Circuit Breaker Behavior

```bash
# Simulate failing agent
# Execute workflow 5+ times to trigger circuit breaker
for i in {1..6}; do
  echo "Execution $i"
  curl -X POST http://localhost:8000/api/v1/workflows/test-workflow/execute \
    -H "Content-Type: application/json" \
    -d '{"input": {}}'
  sleep 1
done

# Check circuit state
docker exec redis redis-cli GET "circuit_breaker:TestAgent:state"
```

### 4. Disable for Development

During development, you may want to disable circuit breaker:

```json
{
  "circuit_breaker_config": {
    "enabled": false
  }
}
```

Or globally:
```bash
CIRCUIT_BREAKER_ENABLED=false
```

## Troubleshooting

### Issue: Workflow Fails with "Circuit breaker is OPEN"

**Cause**: Agent has failed repeatedly, circuit is protecting the system

**Solution**:
1. Check agent health: `curl https://agent-url/health`
2. Fix the underlying issue
3. Wait for timeout period (default 60s)
4. Circuit will automatically test recovery
5. Or manually reset: `docker exec redis redis-cli DEL "circuit_breaker:AgentName:state"`

### Issue: Circuit Opens Too Quickly

**Cause**: Thresholds are too aggressive

**Solution**: Increase thresholds
```json
{
  "failure_threshold": 10,
  "failure_rate_threshold": 0.3,
  "timeout_seconds": 120
}
```

### Issue: Circuit Doesn't Open When Expected

**Cause**: Thresholds are too lenient

**Solution**: Decrease thresholds
```json
{
  "failure_threshold": 3,
  "failure_rate_threshold": 0.7,
  "timeout_seconds": 30
}
```

## Summary

The circuit breaker is **completely transparent** to your workflows:

1. ✅ **No workflow changes needed** - Just reference the agent
2. ✅ **Configure at agent level** - Via UI or API
3. ✅ **Automatic protection** - Works for all workflows using that agent
4. ✅ **Automatic recovery** - Tests and resumes when agent is healthy
5. ✅ **Fast failure** - Fails immediately when circuit is open (<1ms)

The circuit breaker makes your workflows more resilient without any additional complexity!
