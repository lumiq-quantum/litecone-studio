# Circuit Breaker Deployment Guide

## Overview

This guide covers deploying the Circuit Breaker feature for the Workflow Orchestrator. The circuit breaker prevents cascading failures by automatically stopping calls to failing agents.

## Prerequisites

- Docker and Docker Compose installed
- Redis 7.x or higher
- Existing workflow orchestrator deployment

## Quick Start

### 1. Install Redis Dependency

```bash
pip install redis==5.0.1
```

Or update your requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Start Redis

Using Docker Compose (recommended):
```bash
docker-compose up -d redis
```

Or standalone Docker:
```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine redis-server --appendonly yes
```

### 3. Configure Environment Variables

Update your `.env` file:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_TTL_SECONDS=3600

# Circuit Breaker Configuration
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_FAILURE_RATE_THRESHOLD=0.5
CIRCUIT_BREAKER_TIMEOUT_SECONDS=60
CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS=3
CIRCUIT_BREAKER_WINDOW_SIZE_SECONDS=120
```

### 4. Restart Bridge Service

```bash
# Using Docker Compose
docker-compose restart bridge

# Or rebuild if needed
docker-compose up -d --build bridge
```

### 5. Verify Deployment

Check logs for successful initialization:
```bash
docker-compose logs bridge | grep "Circuit Breaker"
```

Expected output:
```
bridge | INFO: Initialized CircuitBreakerManager
bridge | INFO: CircuitBreakerManager initialized with Redis connection
```

## Configuration Details

### Global Configuration

Set default circuit breaker behavior for all agents:

| Variable | Default | Description |
|----------|---------|-------------|
| `CIRCUIT_BREAKER_ENABLED` | `true` | Enable/disable circuit breaker globally |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | `5` | Consecutive failures before opening |
| `CIRCUIT_BREAKER_FAILURE_RATE_THRESHOLD` | `0.5` | Failure rate (0.0-1.0) threshold |
| `CIRCUIT_BREAKER_TIMEOUT_SECONDS` | `60` | Time circuit stays open |
| `CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS` | `3` | Test calls in half-open state |
| `CIRCUIT_BREAKER_WINDOW_SIZE_SECONDS` | `120` | Sliding window for failure rate |

### Per-Agent Configuration

Override defaults for specific agents in the Agent Registry:

```json
{
  "name": "CriticalAgent",
  "url": "http://critical-service:8080",
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

## Production Deployment

### 1. Redis High Availability

For production, use Redis Sentinel or Redis Cluster:

#### Redis Sentinel (Recommended)

```yaml
# docker-compose.prod.yml
services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-master-data:/data
    networks:
      - orchestrator-network

  redis-sentinel-1:
    image: redis:7-alpine
    command: >
      redis-sentinel /etc/redis/sentinel.conf
      --sentinel monitor mymaster redis-master 6379 2
      --sentinel down-after-milliseconds mymaster 5000
      --sentinel parallel-syncs mymaster 1
      --sentinel failover-timeout mymaster 10000
    depends_on:
      - redis-master
    networks:
      - orchestrator-network

  redis-sentinel-2:
    image: redis:7-alpine
    command: >
      redis-sentinel /etc/redis/sentinel.conf
      --sentinel monitor mymaster redis-master 6379 2
      --sentinel down-after-milliseconds mymaster 5000
      --sentinel parallel-syncs mymaster 1
      --sentinel failover-timeout mymaster 10000
    depends_on:
      - redis-master
    networks:
      - orchestrator-network

  redis-sentinel-3:
    image: redis:7-alpine
    command: >
      redis-sentinel /etc/redis/sentinel.conf
      --sentinel monitor mymaster redis-master 6379 2
      --sentinel down-after-milliseconds mymaster 5000
      --sentinel parallel-syncs mymaster 1
      --sentinel failover-timeout mymaster 10000
    depends_on:
      - redis-master
    networks:
      - orchestrator-network
```

Update `REDIS_URL`:
```bash
REDIS_URL=redis://redis-sentinel-1:26379,redis-sentinel-2:26379,redis-sentinel-3:26379/mymaster
```

### 2. Redis Persistence

Configure Redis persistence for durability:

```bash
# Append-only file (AOF) - recommended
docker run -d \
  --name redis \
  -v redis-data:/data \
  redis:7-alpine \
  redis-server --appendonly yes --appendfsync everysec
```

### 3. Resource Limits

Set appropriate resource limits:

```yaml
services:
  redis:
    image: redis:7-alpine
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 4. Monitoring

Monitor Redis and circuit breaker metrics:

```bash
# Redis metrics
docker exec redis redis-cli INFO stats

# Circuit breaker state
docker exec redis redis-cli KEYS "circuit_breaker:*"
```

## Testing

### 1. Test Circuit Breaker Functionality

Create a test workflow with a failing agent:

```json
{
  "workflow_id": "circuit-breaker-test",
  "steps": {
    "step-1": {
      "id": "step-1",
      "agent_name": "FailingAgent",
      "input_mapping": {
        "text": "test"
      }
    }
  }
}
```

Execute multiple times to trigger circuit breaker:

```bash
# Execute 5 times to open circuit
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/workflows/circuit-breaker-test/execute \
    -H "Content-Type: application/json" \
    -d '{"input": {}}'
  sleep 1
done

# 6th execution should fail immediately with circuit breaker error
curl -X POST http://localhost:8000/api/v1/workflows/circuit-breaker-test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'
```

### 2. Verify Circuit State

Check Redis for circuit state:

```bash
docker exec redis redis-cli GET "circuit_breaker:FailingAgent:state"
# Expected: "open"
```

### 3. Test Recovery

Wait for timeout period (default 60s) and execute again:

```bash
sleep 60

# Circuit should transition to half-open
curl -X POST http://localhost:8000/api/v1/workflows/circuit-breaker-test/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'
```

## Troubleshooting

### Issue: Circuit Breaker Not Working

**Symptoms**: Calls continue to failing agents

**Solutions**:
1. Check Redis connectivity:
   ```bash
   docker exec bridge redis-cli -u $REDIS_URL PING
   ```

2. Verify environment variables:
   ```bash
   docker exec bridge env | grep CIRCUIT_BREAKER
   ```

3. Check logs:
   ```bash
   docker-compose logs bridge | grep -i circuit
   ```

### Issue: Redis Connection Errors

**Symptoms**: `ConnectionError` in logs

**Solutions**:
1. Verify Redis is running:
   ```bash
   docker ps | grep redis
   ```

2. Check network connectivity:
   ```bash
   docker exec bridge ping redis
   ```

3. Verify REDIS_URL format:
   ```bash
   # Correct formats:
   redis://localhost:6379/0
   redis://redis:6379/0
   redis://:password@redis:6379/0
   ```

### Issue: Circuit Opens Too Frequently

**Symptoms**: Circuit opens and closes repeatedly

**Solutions**:
1. Increase failure threshold:
   ```bash
   CIRCUIT_BREAKER_FAILURE_THRESHOLD=10
   ```

2. Increase window size:
   ```bash
   CIRCUIT_BREAKER_WINDOW_SIZE_SECONDS=300
   ```

3. Adjust failure rate threshold:
   ```bash
   CIRCUIT_BREAKER_FAILURE_RATE_THRESHOLD=0.7
   ```

### Issue: Circuit Stays Open Too Long

**Symptoms**: Circuit doesn't recover after service is fixed

**Solutions**:
1. Decrease timeout:
   ```bash
   CIRCUIT_BREAKER_TIMEOUT_SECONDS=30
   ```

2. Manually reset circuit:
   ```bash
   docker exec redis redis-cli DEL "circuit_breaker:AgentName:state"
   docker exec redis redis-cli DEL "circuit_breaker:AgentName:open_timestamp"
   ```

## Monitoring and Alerts

### 1. Circuit Breaker Metrics

Monitor these Redis keys:

```bash
# Circuit states
redis-cli KEYS "circuit_breaker:*:state"

# Call history
redis-cli KEYS "circuit_breaker:*:calls"

# Open timestamps
redis-cli KEYS "circuit_breaker:*:open_timestamp"
```

### 2. Log Monitoring

Set up alerts for circuit breaker events:

```bash
# Circuit opened
docker-compose logs -f bridge | grep "Circuit breaker OPENED"

# Circuit closed
docker-compose logs -f bridge | grep "Circuit breaker transitioned to CLOSED"

# Circuit breaker errors
docker-compose logs -f bridge | grep "CircuitBreakerOpenError"
```

### 3. Prometheus Metrics (Future)

Example metrics to expose:

```
# Circuit breaker state (0=closed, 1=open, 2=half-open)
circuit_breaker_state{agent="AgentName"} 0

# Total calls through circuit breaker
circuit_breaker_calls_total{agent="AgentName",result="success"} 1000
circuit_breaker_calls_total{agent="AgentName",result="failure"} 50

# Circuit breaker state transitions
circuit_breaker_transitions_total{agent="AgentName",from="closed",to="open"} 5
```

## Rollback

If you need to disable circuit breaker:

### 1. Disable Globally

```bash
# Update .env
CIRCUIT_BREAKER_ENABLED=false

# Restart bridge
docker-compose restart bridge
```

### 2. Disable Per-Agent

Update agent configuration in Agent Registry:

```json
{
  "name": "AgentName",
  "circuit_breaker_config": {
    "enabled": false
  }
}
```

### 3. Remove Redis (Optional)

```bash
# Stop Redis
docker-compose stop redis

# Remove Redis data
docker volume rm orchestrator_redis-data
```

## Performance Considerations

### Redis Performance

- **Memory**: Circuit breaker uses minimal memory (~1KB per agent)
- **Latency**: Redis operations add <1ms latency per call
- **Throughput**: Redis can handle 100K+ ops/sec

### Optimization Tips

1. **Use Redis pipelining** for batch operations (future enhancement)
2. **Set appropriate TTL** for call history to limit memory usage
3. **Use Redis Cluster** for high-throughput scenarios (>10K calls/sec)

## Security

### 1. Redis Authentication

Enable Redis authentication:

```bash
# Start Redis with password
docker run -d \
  --name redis \
  redis:7-alpine \
  redis-server --requirepass your-strong-password

# Update REDIS_URL
REDIS_URL=redis://:your-strong-password@redis:6379/0
```

### 2. Network Isolation

Isolate Redis on private network:

```yaml
services:
  redis:
    networks:
      - private-network
  
  bridge:
    networks:
      - private-network
      - public-network

networks:
  private-network:
    internal: true
  public-network:
```

### 3. TLS/SSL

Use Redis with TLS:

```bash
REDIS_URL=rediss://redis:6380/0
```

## Next Steps

1. Review [Circuit Breaker Documentation](docs/circuit_breaker.md)
2. Configure per-agent thresholds based on SLAs
3. Set up monitoring and alerts
4. Test failure scenarios in staging
5. Gradually roll out to production

## Support

For issues or questions:
- Check logs: `docker-compose logs bridge`
- Review documentation: `docs/circuit_breaker.md`
- Check Redis: `docker exec redis redis-cli INFO`
