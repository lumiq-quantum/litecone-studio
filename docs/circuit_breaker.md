# Circuit Breaker Pattern

## Overview

The Circuit Breaker pattern prevents cascading failures by automatically stopping calls to failing agents. When an agent repeatedly fails, the circuit breaker "opens" and immediately rejects subsequent calls without attempting to invoke the agent. After a timeout period, the circuit breaker enters a "half-open" state to test if the agent has recovered.

## States

The circuit breaker has three states:

### CLOSED (Normal Operation)
- All calls go through to the agent
- Failures are tracked in a sliding window
- If failure thresholds are exceeded, transitions to OPEN

### OPEN (Failing)
- All calls are immediately rejected with `CircuitBreakerOpenError`
- No HTTP requests are made to the agent
- After timeout period elapses, transitions to HALF_OPEN

### HALF_OPEN (Testing Recovery)
- Limited number of test calls are allowed through
- If test calls succeed, transitions back to CLOSED
- If any test call fails, transitions back to OPEN

## State Transitions

```
CLOSED ──(failures exceed threshold)──> OPEN
  ↑                                       │
  │                                       │
  │                                       │
  └──(test calls succeed)── HALF_OPEN <──┘
                               │
                               │
                               └──(test call fails)──> OPEN
```

## Configuration

Circuit breakers can be configured globally or per-agent:

### Global Configuration (Environment Variables)

```bash
# Enable/disable circuit breaker globally
CIRCUIT_BREAKER_ENABLED=true

# Number of consecutive failures before opening circuit
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5

# Failure rate (0.0-1.0) threshold for opening circuit
CIRCUIT_BREAKER_FAILURE_RATE_THRESHOLD=0.5

# Time to keep circuit open before attempting reset (seconds)
CIRCUIT_BREAKER_TIMEOUT_SECONDS=60

# Maximum test calls allowed in half-open state
CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS=3

# Sliding window size for failure rate calculation (seconds)
CIRCUIT_BREAKER_WINDOW_SIZE_SECONDS=120
```

### Per-Agent Configuration (Agent Registry)

Agents can override global settings with custom configuration:

```json
{
  "name": "UnreliableAgent",
  "url": "http://unreliable-service:8080",
  "circuit_breaker_config": {
    "enabled": true,
    "failure_threshold": 3,
    "failure_rate_threshold": 0.7,
    "timeout_seconds": 30,
    "half_open_max_calls": 2,
    "window_size_seconds": 60
  }
}
```

## How It Works

### 1. Failure Detection

The circuit breaker tracks call results in a sliding time window stored in Redis. Two thresholds determine when to open the circuit:

**Consecutive Failures**: If the last N calls all failed, open the circuit.
```
Example: failure_threshold=5
Last 5 calls: [FAIL, FAIL, FAIL, FAIL, FAIL] → OPEN
```

**Failure Rate**: If the failure rate exceeds the threshold, open the circuit.
```
Example: failure_rate_threshold=0.5, window_size=120s
Last 10 calls in 120s: [FAIL, FAIL, FAIL, FAIL, FAIL, OK, OK, OK, OK, OK]
Failure rate: 50% → OPEN
```

### 2. Circuit Opening

When thresholds are exceeded:
1. Circuit state changes to OPEN
2. Open timestamp is recorded
3. Monitoring event is published
4. All subsequent calls fail immediately with `CircuitBreakerOpenError`

### 3. Recovery Testing

After the timeout period:
1. Circuit transitions to HALF_OPEN
2. Limited test calls are allowed (e.g., 3 calls)
3. If all test calls succeed → Circuit closes (CLOSED)
4. If any test call fails → Circuit reopens (OPEN)

### 4. Shared State

Circuit breaker state is stored in Redis, enabling:
- State sharing across multiple executor instances
- Persistence across restarts
- Distributed coordination

## Usage Examples

### Example 1: Normal Operation

```python
# Agent is healthy, all calls go through
result = await executor.invoke_agent(agent_metadata, task)
# Circuit remains CLOSED
```

### Example 2: Agent Starts Failing

```python
# First 4 failures are tracked
for i in range(4):
    try:
        await executor.invoke_agent(agent_metadata, task)
    except Exception:
        pass  # Circuit still CLOSED

# 5th failure opens the circuit
try:
    await executor.invoke_agent(agent_metadata, task)
except Exception:
    pass  # Circuit transitions to OPEN

# Subsequent calls fail immediately
try:
    await executor.invoke_agent(agent_metadata, task)
except CircuitBreakerOpenError:
    print("Circuit is open, agent is unavailable")
```

### Example 3: Recovery

```python
# Wait for timeout period (e.g., 60 seconds)
await asyncio.sleep(60)

# Circuit transitions to HALF_OPEN
# First test call succeeds
result1 = await executor.invoke_agent(agent_metadata, task)

# Second test call succeeds
result2 = await executor.invoke_agent(agent_metadata, task)

# Third test call succeeds
result3 = await executor.invoke_agent(agent_metadata, task)

# Circuit transitions back to CLOSED
# Normal operation resumes
```

## Monitoring

Circuit breaker state changes are logged with structured logging:

```json
{
  "level": "warning",
  "message": "Circuit breaker OPENED for agent 'UnreliableAgent' due to failures",
  "agent_name": "UnreliableAgent",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

```json
{
  "level": "info",
  "message": "Circuit breaker transitioned to CLOSED for agent 'UnreliableAgent' after 3 successful test calls",
  "agent_name": "UnreliableAgent",
  "success_count": 3,
  "timestamp": "2024-01-15T10:31:30Z"
}
```

## Benefits

1. **Prevents Cascading Failures**: Stops calling failing services before they bring down the entire system
2. **Fast Failure**: Immediately rejects calls when circuit is open, reducing latency
3. **Automatic Recovery**: Tests service health and automatically resumes when recovered
4. **Resource Protection**: Prevents wasting resources on calls that will likely fail
5. **Distributed Coordination**: Shares state across multiple executor instances via Redis

## Best Practices

### 1. Tune Thresholds for Your Use Case

- **High-traffic services**: Use failure rate threshold (e.g., 50% over 2 minutes)
- **Low-traffic services**: Use consecutive failure threshold (e.g., 5 failures)
- **Critical services**: Lower thresholds (e.g., 3 failures, 30s timeout)
- **Non-critical services**: Higher thresholds (e.g., 10 failures, 120s timeout)

### 2. Set Appropriate Timeout

- Too short: Circuit reopens before service recovers
- Too long: Delays recovery and wastes time
- Recommended: 30-120 seconds depending on service recovery time

### 3. Monitor Circuit Breaker Events

Set up alerts for:
- Circuit opening (indicates service degradation)
- Circuit staying open for extended periods (indicates persistent issues)
- Frequent open/close cycles (indicates unstable service)

### 4. Combine with Retry Logic

Circuit breaker works best with retry logic:
1. Retry handles transient failures (network blips)
2. Circuit breaker handles persistent failures (service down)

### 5. Test Recovery Behavior

Ensure your services can handle:
- Sudden traffic spikes when circuit closes
- Partial traffic during half-open state

## Troubleshooting

### Circuit Opens Too Frequently

**Symptoms**: Circuit opens and closes repeatedly

**Solutions**:
- Increase `failure_threshold` or `failure_rate_threshold`
- Increase `window_size_seconds` to smooth out transient failures
- Increase `timeout_seconds` to give service more time to recover

### Circuit Stays Open Too Long

**Symptoms**: Circuit remains open even after service recovers

**Solutions**:
- Decrease `timeout_seconds`
- Increase `half_open_max_calls` to test recovery more thoroughly
- Check if service is actually recovered

### Circuit Doesn't Open When Expected

**Symptoms**: Calls continue to failing service

**Solutions**:
- Verify `CIRCUIT_BREAKER_ENABLED=true`
- Check Redis connectivity
- Verify failure thresholds are configured correctly
- Check logs for circuit breaker events

### Redis Connection Issues

**Symptoms**: Circuit breaker not working, Redis errors in logs

**Solutions**:
- Verify `REDIS_URL` is correct
- Ensure Redis is running and accessible
- Check network connectivity
- Verify Redis authentication if configured

## Architecture

### Components

```
┌─────────────────────────────────────────┐
│   ExternalAgentExecutor                 │
│                                         │
│   ┌─────────────────────────────────┐  │
│   │  CircuitBreakerManager          │  │
│   │                                 │  │
│   │  ┌──────────────────────────┐  │  │
│   │  │  CircuitBreaker (Agent1) │  │  │
│   │  └──────────────────────────┘  │  │
│   │  ┌──────────────────────────┐  │  │
│   │  │  CircuitBreaker (Agent2) │  │  │
│   │  └──────────────────────────┘  │  │
│   │                                 │  │
│   │  ┌──────────────────────────┐  │  │
│   │  │  CircuitBreakerStateStore│  │  │
│   │  │         (Redis)           │  │  │
│   │  └──────────────────────────┘  │  │
│   └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
                  │
                  ▼
            ┌──────────┐
            │  Redis   │
            └──────────┘
```

### Redis Data Structure

```
# Circuit state
circuit_breaker:{agent_name}:state = "closed" | "open" | "half_open"

# Call history (sorted set with timestamp as score)
circuit_breaker:{agent_name}:calls = {
  "1705315800.123:1": 1705315800.123,  # timestamp:success
  "1705315801.456:0": 1705315801.456,  # timestamp:failure
  ...
}

# Open timestamp
circuit_breaker:{agent_name}:open_timestamp = "2024-01-15T10:30:00"

# Half-open counters
circuit_breaker:{agent_name}:half_open_success = 2
circuit_breaker:{agent_name}:half_open_calls = 2
```

## Integration with Workflow Execution

Circuit breaker is transparent to workflow execution:

```python
# Workflow step invokes agent
try:
    result = await executor.execute_step(step)
    # Success - circuit remains closed or closes if was half-open
except CircuitBreakerOpenError as e:
    # Circuit is open - step fails immediately
    # Workflow can handle failure (retry, skip, fail)
    logger.error(f"Agent unavailable: {e}")
except Exception as e:
    # Other errors - circuit may open if threshold exceeded
    logger.error(f"Agent error: {e}")
```

## Future Enhancements

Potential improvements for future versions:

1. **Metrics Dashboard**: Visualize circuit breaker states and transitions
2. **Manual Control**: API endpoints to manually open/close circuits
3. **Adaptive Thresholds**: Automatically adjust thresholds based on traffic patterns
4. **Bulkhead Pattern**: Limit concurrent calls per agent
5. **Fallback Strategies**: Automatic fallback to alternative agents
6. **Health Checks**: Proactive health checks instead of waiting for timeout

## References

- [Martin Fowler - Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Microsoft - Circuit Breaker Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
- [Netflix Hystrix](https://github.com/Netflix/Hystrix/wiki/How-it-Works#CircuitBreaker)
