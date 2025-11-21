# Circuit Breaker Quick Reference

## TL;DR

Circuit breaker is **configured at the agent level** and works **automatically** with all workflows. No workflow changes needed!

## Quick Setup (3 Steps)

### 1. Configure Agent (UI)
```
Agents → Create Agent → Circuit Breaker Section
✓ Enabled
Failure Threshold: 5
Failure Rate: 0.5
Timeout: 60s
```

### 2. Create Workflow (No Changes)
```json
{
  "steps": {
    "my-step": {
      "agent_name": "MyAgent",
      "input_mapping": {...}
    }
  }
}
```

### 3. Execute Workflow
```bash
curl -X POST http://localhost:8000/api/v1/workflows/my-workflow/execute
```

**That's it!** Circuit breaker now protects all calls to `MyAgent`.

## How It Works

```
Normal Operation (Circuit CLOSED)
─────────────────────────────────
Workflow → Agent → ✓ Success
Workflow → Agent → ✓ Success
Workflow → Agent → ✓ Success

Agent Starts Failing
────────────────────
Workflow → Agent → ✗ Fail (1/5)
Workflow → Agent → ✗ Fail (2/5)
Workflow → Agent → ✗ Fail (3/5)
Workflow → Agent → ✗ Fail (4/5)
Workflow → Agent → ✗ Fail (5/5) → Circuit OPENS!

Circuit Open (Fast Failure)
───────────────────────────
Workflow → ✗ Immediate fail (<1ms, no HTTP call)
Workflow → ✗ Immediate fail (<1ms, no HTTP call)

After 60 seconds...
──────────────────
Workflow → Agent → ✓ Test call 1 (Circuit HALF_OPEN)
Workflow → Agent → ✓ Test call 2
Workflow → Agent → ✓ Test call 3 → Circuit CLOSES!

Back to Normal
──────────────
Workflow → Agent → ✓ Success
```

## Configuration Presets

### Critical Service (Aggressive)
```json
{
  "failure_threshold": 2,
  "failure_rate_threshold": 0.8,
  "timeout_seconds": 30,
  "half_open_max_calls": 1,
  "window_size_seconds": 60
}
```
**Use for**: Payment gateways, authentication services

### Standard Service (Balanced)
```json
{
  "failure_threshold": 5,
  "failure_rate_threshold": 0.5,
  "timeout_seconds": 60,
  "half_open_max_calls": 3,
  "window_size_seconds": 120
}
```
**Use for**: Data APIs, processing services (DEFAULT)

### Non-Critical Service (Lenient)
```json
{
  "failure_threshold": 10,
  "failure_rate_threshold": 0.3,
  "timeout_seconds": 120,
  "half_open_max_calls": 5,
  "window_size_seconds": 300
}
```
**Use for**: Logging, analytics, notifications

## Common Commands

### Check Circuit State
```bash
# View all circuit breaker states
docker exec redis redis-cli KEYS "circuit_breaker:*:state"

# Check specific agent
docker exec redis redis-cli GET "circuit_breaker:MyAgent:state"
# Returns: "closed", "open", or "half_open"
```

### View Circuit Breaker Logs
```bash
# All circuit breaker events
docker-compose logs bridge | grep -i "circuit breaker"

# Circuit opened events
docker-compose logs bridge | grep "Circuit breaker OPENED"

# Circuit closed events
docker-compose logs bridge | grep "transitioned to CLOSED"
```

### Manually Reset Circuit
```bash
# Reset circuit state
docker exec redis redis-cli DEL "circuit_breaker:MyAgent:state"
docker exec redis redis-cli DEL "circuit_breaker:MyAgent:open_timestamp"

# Clear call history
docker exec redis redis-cli DEL "circuit_breaker:MyAgent:calls"
```

### Test Circuit Breaker
```bash
# Execute workflow multiple times to trigger circuit breaker
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/workflows/test/execute \
    -H "Content-Type: application/json" \
    -d '{"input": {}}'
  sleep 1
done

# Check if circuit opened
docker exec redis redis-cli GET "circuit_breaker:TestAgent:state"
```

## Configuration Fields

| Field | Default | Description |
|-------|---------|-------------|
| `enabled` | `true` | Enable/disable circuit breaker |
| `failure_threshold` | `5` | Consecutive failures before opening |
| `failure_rate_threshold` | `0.5` | Failure rate (0.0-1.0) to trigger opening |
| `timeout_seconds` | `60` | Time circuit stays open |
| `half_open_max_calls` | `3` | Test calls during recovery |
| `window_size_seconds` | `120` | Sliding window for failure rate |

## Error Messages

### "Circuit breaker is OPEN for agent 'AgentName'"
**Meaning**: Agent has failed repeatedly, circuit is protecting the system  
**Action**: Wait for timeout period or fix the agent and manually reset

### "Circuit breaker is HALF_OPEN, max calls reached"
**Meaning**: Circuit is testing recovery but limit reached  
**Action**: Wait a moment, circuit will transition based on test results

## Workflow Integration Examples

### Simple Workflow
```json
{
  "steps": {
    "step-1": {
      "agent_name": "ProtectedAgent",
      "input_mapping": {"data": "${workflow.input}"}
    }
  }
}
```
✅ Circuit breaker protects `ProtectedAgent` automatically

### Parallel Workflow
```json
{
  "steps": {
    "parallel-block": {
      "type": "parallel",
      "parallel_steps": ["step-a", "step-b", "step-c"]
    },
    "step-a": {"agent_name": "AgentA"},
    "step-b": {"agent_name": "AgentB"},
    "step-c": {"agent_name": "AgentC"}
  }
}
```
✅ Each agent has independent circuit breaker

### Conditional Workflow
```json
{
  "steps": {
    "check": {
      "type": "conditional",
      "condition": {"expression": "${step-1.status} == 'SUCCESS'"},
      "then_step": "primary-agent",
      "else_step": "fallback-agent"
    },
    "primary-agent": {"agent_name": "PrimaryAgent"},
    "fallback-agent": {"agent_name": "FallbackAgent"}
  }
}
```
✅ If `PrimaryAgent` circuit is open, workflow can use `FallbackAgent`

### Loop Workflow
```json
{
  "steps": {
    "loop": {
      "type": "loop",
      "collection": "${workflow.input.items}",
      "loop_body": ["process-item"]
    },
    "process-item": {"agent_name": "ProcessorAgent"}
  }
}
```
✅ Circuit breaker protects each iteration

## Monitoring Dashboard (Future)

```
┌─────────────────────────────────────────────────────┐
│ Circuit Breaker Status                              │
├─────────────────────────────────────────────────────┤
│ Agent Name          State      Last Transition      │
│ ─────────────────────────────────────────────────── │
│ PaymentGateway      🟢 CLOSED   2 min ago           │
│ DataProcessor       🟢 CLOSED   5 min ago           │
│ UnreliableService   🔴 OPEN     30 sec ago          │
│ EmailService        🟡 HALF_OPEN Testing...         │
└─────────────────────────────────────────────────────┘
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Circuit opens too quickly | Increase `failure_threshold` or `failure_rate_threshold` |
| Circuit stays open too long | Decrease `timeout_seconds` |
| Circuit doesn't open | Decrease thresholds or check if enabled |
| Need to force reset | Use Redis DEL commands above |

## Key Benefits

✅ **Transparent** - No workflow changes needed  
✅ **Automatic** - Detects failures and recovers automatically  
✅ **Fast** - Fails in <1ms when circuit is open  
✅ **Distributed** - State shared across all executors  
✅ **Configurable** - Per-agent customization  
✅ **Production-Ready** - Battle-tested pattern  

## Learn More

- **Full Documentation**: [docs/circuit_breaker.md](../docs/circuit_breaker.md)
- **Usage Guide**: [CIRCUIT_BREAKER_USAGE_GUIDE.md](CIRCUIT_BREAKER_USAGE_GUIDE.md)
- **Deployment**: [CIRCUIT_BREAKER_DEPLOYMENT.md](../CIRCUIT_BREAKER_DEPLOYMENT.md)
- **UI Guide**: [workflow-ui/CIRCUIT_BREAKER_UI.md](../workflow-ui/CIRCUIT_BREAKER_UI.md)
