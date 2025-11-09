# Workflow Management API - Deployment Guide

## Overview

This guide covers deploying the Workflow Management API in various environments, including Docker, Kubernetes, and bare metal deployments.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Docker Deployment](#docker-deployment)
3. [Production Configuration](#production-configuration)
4. [Health Checks](#health-checks)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

---

## Environment Variables

### Required Variables

These variables **must** be configured for the API to function:

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` | ✅ Yes |
| `KAFKA_BROKERS` | Comma-separated Kafka broker addresses | `kafka:29092` or `broker1:9092,broker2:9092` | ✅ Yes |

### Application Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `API_TITLE` | API title shown in documentation | `Workflow Management API` | `My Workflow API` |
| `API_VERSION` | API version | `1.0.0` | `2.0.0` |
| `API_DESCRIPTION` | API description | `REST API for managing workflow orchestration` | Custom description |
| `API_PREFIX` | API route prefix | `/api/v1` | `/api/v2` |
| `API_HOST` | Host to bind to | `0.0.0.0` | `127.0.0.1` |
| `API_PORT` | Port to listen on | `8000` | `8080` |
| `API_RELOAD` | Enable auto-reload (dev only) | `false` | `true` |
| `API_WORKERS` | Number of worker processes | `1` | `4` |

### Database Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DATABASE_URL` | Full PostgreSQL connection URL | - | `postgresql://user:pass@localhost:5432/workflow_db` |
| `DATABASE_POOL_SIZE` | Connection pool size | `10` | `20` |
| `DATABASE_MAX_OVERFLOW` | Max overflow connections | `20` | `40` |
| `DATABASE_ECHO` | Log SQL queries (debug) | `false` | `true` |

### Kafka Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `KAFKA_BROKERS` | Kafka broker addresses | - | `localhost:9092` |
| `KAFKA_EXECUTION_TOPIC` | Topic for execution requests | `workflow.execution.requests` | `prod.workflow.execution` |
| `KAFKA_CANCELLATION_TOPIC` | Topic for cancellation requests | `workflow.cancellation.requests` | `prod.workflow.cancellation` |

### Authentication Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `JWT_SECRET` | Secret key for JWT signing | - | `your-secret-key-min-32-chars` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` | `HS256` |
| `JWT_EXPIRATION_MINUTES` | JWT token expiration time | `60` | `1440` (24 hours) |
| `API_KEY_HEADER` | Header name for API key auth | `X-API-Key` | `X-Custom-API-Key` |

> ⚠️ **Security Warning**: Always use strong, randomly generated secrets in production. Never commit secrets to version control.

### CORS Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000` | `https://app.example.com,https://admin.example.com` |
| `CORS_ALLOW_CREDENTIALS` | Allow credentials in CORS | `true` | `false` |
| `CORS_ALLOW_METHODS` | Allowed HTTP methods | `*` | `GET,POST,PUT,DELETE` |
| `CORS_ALLOW_HEADERS` | Allowed headers | `*` | `Content-Type,Authorization` |

### Logging Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | Log output format | `json` | `text`, `json` |

### Pagination Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DEFAULT_PAGE_SIZE` | Default items per page | `20` | `50` |
| `MAX_PAGE_SIZE` | Maximum items per page | `100` | `200` |

### Feature Flags

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENABLE_METRICS` | Enable Prometheus metrics | `true` | `false` |
| `ENABLE_AUDIT_LOGGING` | Enable audit logging | `true` | `false` |

---

## Docker Deployment

### Using Docker Compose (Recommended)

The API is configured in `docker-compose.yml` with all dependencies.

#### 1. Development Deployment

```bash
# Start all services including the API
docker-compose --profile api up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose --profile api down
```

#### 2. Production Deployment

```bash
# Create production environment file
cp .env.api.example .env.api.production

# Edit production settings
nano .env.api.production

# Start with production config
docker-compose --profile api --env-file .env.api.production up -d
```

### Using Docker Directly

```bash
# Build the image
docker build -f Dockerfile.api -t workflow-api:latest .

# Run the container
docker run -d \
  --name workflow-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e KAFKA_BROKERS=kafka:29092 \
  --network orchestrator-network \
  workflow-api:latest
```

### Docker Compose Service Configuration

The API service in `docker-compose.yml`:

```yaml
api:
  build:
    context: .
    dockerfile: Dockerfile.api
  container_name: workflow-management-api
  depends_on:
    - postgres
    - kafka
  ports:
    - "8000:8000"
  environment:
    - DATABASE_URL=postgresql://workflow_user:workflow_pass@postgres:5432/workflow_db
    - KAFKA_BROKERS=kafka:29092
    - API_HOST=0.0.0.0
    - API_PORT=8000
  env_file:
    - .env.api
  networks:
    - orchestrator-network
  profiles:
    - api
  healthcheck:
    test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

---

## Production Configuration

### 1. Environment File Setup

Create a production environment file:

```bash
# Copy the example file
cp .env.api.example .env.api.production

# Edit with production values
nano .env.api.production
```

### 2. Production Environment Variables

**Minimum production configuration:**

```bash
# Application
API_TITLE=Workflow Management API
API_VERSION=1.0.0
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
API_WORKERS=4

# Database (use strong credentials!)
DATABASE_URL=postgresql://prod_user:STRONG_PASSWORD@db-host:5432/workflow_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_ECHO=false

# Kafka
KAFKA_BROKERS=kafka-1:9092,kafka-2:9092,kafka-3:9092
KAFKA_EXECUTION_TOPIC=prod.workflow.execution.requests
KAFKA_CANCELLATION_TOPIC=prod.workflow.cancellation.requests

# Authentication (CRITICAL: Use strong secrets!)
JWT_SECRET=CHANGE_THIS_TO_RANDOM_64_CHAR_STRING_MIN
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
API_KEY_HEADER=X-API-Key

# CORS (restrict to your domains)
CORS_ORIGINS=https://app.example.com,https://admin.example.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH
CORS_ALLOW_HEADERS=Content-Type,Authorization,X-API-Key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Pagination
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100

# Features
ENABLE_METRICS=true
ENABLE_AUDIT_LOGGING=true
```

### 3. Security Best Practices

#### Generate Strong Secrets

```bash
# Generate JWT secret (64 characters)
openssl rand -hex 32

# Or using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

#### Secure Database Connection

```bash
# Use SSL for database connections
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Or with certificate verification
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=verify-full&sslrootcert=/path/to/ca.crt
```

#### Restrict CORS Origins

```bash
# Only allow specific domains
CORS_ORIGINS=https://app.example.com,https://admin.example.com

# Never use * in production
# CORS_ORIGINS=*  # ❌ INSECURE
```

### 4. Performance Tuning

#### Worker Processes

```bash
# Calculate workers: (2 x CPU cores) + 1
# For 4 CPU cores:
API_WORKERS=9

# For high-traffic APIs, consider:
API_WORKERS=16
```

#### Database Connection Pool

```bash
# Formula: (workers * 2) + overflow
# For 4 workers:
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

### 5. Running Migrations

Always run database migrations before starting the API:

```bash
# In Docker
docker-compose exec api alembic upgrade head

# Locally
alembic upgrade head
```

---

## Health Checks

The API provides multiple health check endpoints for monitoring and orchestration.

### 1. Basic Health Check

**Endpoint:** `GET /health`

**Purpose:** Liveness probe - checks if the API process is running

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Usage:**
```bash
curl http://localhost:8000/health
```

### 2. Readiness Check

**Endpoint:** `GET /health/ready`

**Purpose:** Readiness probe - checks if the API can serve traffic (includes dependency checks)

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "connected",
    "kafka": "connected"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Usage:**
```bash
curl http://localhost:8000/health/ready
```

### 3. Docker Health Check

The `Dockerfile.api` includes a built-in health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1
```

**Configuration:**
- **Interval:** Check every 30 seconds
- **Timeout:** Fail if check takes longer than 10 seconds
- **Start Period:** Wait 40 seconds before first check (allows startup time)
- **Retries:** Mark unhealthy after 3 consecutive failures

### 4. Kubernetes Health Checks

Example Kubernetes deployment with health checks:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workflow-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: workflow-api:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 40
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
```

---

## Monitoring

### 1. Prometheus Metrics

**Endpoint:** `GET /metrics`

**Metrics Exposed:**
- Request count by endpoint and status code
- Request latency (histogram)
- Active requests (gauge)
- Database connection pool stats
- Workflow execution metrics

**Usage:**
```bash
curl http://localhost:8000/metrics
```

### 2. Prometheus Configuration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'workflow-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### 3. Logging

The API uses structured JSON logging for easy parsing:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "api.routes.workflows",
  "message": "Workflow created",
  "workflow_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user@example.com",
  "correlation_id": "req-abc123"
}
```

**View logs:**
```bash
# Docker Compose
docker-compose logs -f api

# Docker
docker logs -f workflow-management-api

# Filter by level
docker-compose logs api | grep ERROR
```

---

## Troubleshooting

### API Not Starting

**Symptoms:** Container exits immediately or fails to start

**Solutions:**

1. **Check database connection:**
   ```bash
   # Test database connectivity
   docker-compose exec postgres psql -U workflow_user -d workflow_db -c "SELECT 1;"
   ```

2. **Verify environment variables:**
   ```bash
   docker-compose exec api env | grep DATABASE_URL
   ```

3. **Check logs:**
   ```bash
   docker-compose logs api
   ```

4. **Run migrations:**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

### Health Check Failing

**Symptoms:** Container marked as unhealthy

**Solutions:**

1. **Check health endpoint manually:**
   ```bash
   docker-compose exec api curl http://localhost:8000/health
   ```

2. **Increase start period:**
   ```yaml
   healthcheck:
     start_period: 60s  # Increase from 40s
   ```

3. **Check dependencies:**
   ```bash
   docker-compose exec api curl http://localhost:8000/health/ready
   ```

### Database Connection Issues

**Symptoms:** `sqlalchemy.exc.OperationalError`

**Solutions:**

1. **Verify PostgreSQL is running:**
   ```bash
   docker-compose ps postgres
   ```

2. **Check connection string:**
   ```bash
   echo $DATABASE_URL
   ```

3. **Test connection:**
   ```bash
   docker-compose exec api python -c "from api.database import engine; engine.connect()"
   ```

### Kafka Connection Issues

**Symptoms:** Workflow execution fails, Kafka errors in logs

**Solutions:**

1. **Verify Kafka is running:**
   ```bash
   docker-compose ps kafka
   ```

2. **Check broker connectivity:**
   ```bash
   docker-compose exec api python -c "from kafka import KafkaProducer; KafkaProducer(bootstrap_servers='kafka:29092')"
   ```

3. **Verify topics exist:**
   ```bash
   docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:29092
   ```

### Performance Issues

**Symptoms:** Slow response times, high latency

**Solutions:**

1. **Increase worker processes:**
   ```bash
   API_WORKERS=8
   ```

2. **Tune database pool:**
   ```bash
   DATABASE_POOL_SIZE=30
   DATABASE_MAX_OVERFLOW=60
   ```

3. **Enable query logging to identify slow queries:**
   ```bash
   DATABASE_ECHO=true
   LOG_LEVEL=DEBUG
   ```

4. **Check metrics:**
   ```bash
   curl http://localhost:8000/metrics | grep latency
   ```

---

## Additional Resources

- [API Documentation](./API_DOCUMENTATION.md)
- [OpenAPI Specification](http://localhost:8000/openapi.json)
- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)
- [Database Setup](./DATABASE_SETUP.md)

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `docker-compose logs api`
3. Check health endpoints: `/health` and `/health/ready`
4. Verify environment variables are set correctly
