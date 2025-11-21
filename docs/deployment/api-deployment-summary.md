# Deployment Configuration Summary

This document provides a quick overview of the deployment configuration for the Workflow Management API.

## Files Created/Updated

### Core Deployment Files

1. **`Dockerfile.api`** ✅
   - Production-ready Docker image
   - Multi-stage build for optimization
   - Non-root user for security
   - Health check included
   - Automatic migrations on startup

2. **`docker-compose.yml`** ✅
   - API service configuration
   - Health checks configured
   - Resource limits defined
   - Restart policy: `unless-stopped`
   - Profile-based deployment (`--profile api`)

3. **`docker-compose.prod.yml`** ✅
   - Production overrides
   - Enhanced resource limits
   - Production environment variables
   - Logging configuration
   - Multiple replicas support

### Documentation Files

4. **`api/DEPLOYMENT.md`** ✅
   - Complete deployment guide
   - Environment variable documentation
   - Docker deployment instructions
   - Production configuration
   - Health checks documentation
   - Monitoring setup
   - Troubleshooting guide

5. **`api/ENV_VARIABLES.md`** ✅
   - Detailed environment variable reference
   - Required vs optional variables
   - Data types and validation
   - Security recommendations
   - Example configurations
   - Production checklist

6. **`api/DEPLOYMENT_CHECKLIST.md`** ✅
   - Pre-deployment checklist
   - Configuration validation
   - Deployment steps
   - Post-deployment verification
   - Rollback procedures
   - Troubleshooting guide

### Deployment Scripts

7. **`deploy-api.sh`** ✅
   - Interactive deployment script
   - Command-line interface
   - Environment validation
   - Health check automation
   - Migration runner
   - Log viewer

### Updated Files

8. **`api/README.md`** ✅
   - Added deployment section
   - Links to deployment documentation
   - Quick start commands

## Deployment Options

### 1. Development Deployment

```bash
# Using deployment script (recommended)
./deploy-api.sh dev

# Or using docker-compose directly
docker-compose --profile api up -d
```

**Features:**
- Auto-reload enabled
- Debug logging
- Single worker
- Development CORS origins

### 2. Production Deployment

```bash
# Using deployment script (recommended)
./deploy-api.sh prod

# Or using docker-compose directly
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile api up -d
```

**Features:**
- Multiple workers (4+)
- JSON logging
- Resource limits
- Production CORS restrictions
- Enhanced security

### 3. Manual Docker Deployment

```bash
# Build image
docker build -f Dockerfile.api -t workflow-api:latest .

# Run container
docker run -d \
  --name workflow-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e KAFKA_BROKERS=kafka:29092 \
  --network orchestrator-network \
  workflow-api:latest
```

## Health Check Configuration

### Dockerfile Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1
```

**Parameters:**
- **Interval:** 30 seconds between checks
- **Timeout:** 10 seconds per check
- **Start Period:** 40 seconds grace period
- **Retries:** 3 consecutive failures before unhealthy

### Docker Compose Health Check

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Health Endpoints

1. **Basic Health:** `GET /health`
   - Checks if API is running
   - Used for liveness probe

2. **Readiness Check:** `GET /health/ready`
   - Checks database connectivity
   - Checks Kafka connectivity
   - Used for readiness probe

## Environment Variables

### Required Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `KAFKA_BROKERS` | Kafka broker addresses |

### Important Production Variables

| Variable | Default | Production Value |
|----------|---------|------------------|
| `API_WORKERS` | `1` | `4` or higher |
| `API_RELOAD` | `false` | `false` |
| `JWT_SECRET` | `dev-secret-key` | Strong random value |
| `LOG_LEVEL` | `INFO` | `INFO` or `WARNING` |
| `LOG_FORMAT` | `json` | `json` |
| `CORS_ORIGINS` | `http://localhost:3000` | Specific domains |

See [ENV_VARIABLES.md](./ENV_VARIABLES.md) for complete reference.

## Resource Configuration

### Development

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Production

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 1G
```

## Security Features

### Dockerfile Security

- ✅ Non-root user (`apiuser`)
- ✅ Minimal base image (`python:3.11-slim`)
- ✅ No unnecessary packages
- ✅ Security updates applied

### Configuration Security

- ✅ Strong JWT secrets required
- ✅ CORS restrictions enforced
- ✅ SSL database connections supported
- ✅ Secrets not in version control
- ✅ Environment-specific configurations

## Monitoring

### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

**Exposed Metrics:**
- Request count by endpoint
- Request latency (histogram)
- Active requests (gauge)
- Database connection pool stats
- Workflow execution metrics

### Logging

**Format:** JSON (production) or Text (development)

**Example Log Entry:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "api.routes.workflows",
  "message": "Workflow created",
  "workflow_id": "123e4567-e89b-12d3-a456-426614174000",
  "correlation_id": "req-abc123"
}
```

## Quick Commands

```bash
# Deploy development
./deploy-api.sh dev

# Deploy production
./deploy-api.sh prod

# Check status
docker-compose ps api
curl http://localhost:8000/health

# View logs
docker-compose logs -f api

# Run migrations
docker-compose exec api alembic upgrade head

# Stop services
docker-compose --profile api down

# Restart API
docker-compose restart api
```

## Verification Steps

After deployment, verify:

1. ✅ Container is running: `docker-compose ps api`
2. ✅ Health check passes: `curl http://localhost:8000/health`
3. ✅ Readiness check passes: `curl http://localhost:8000/health/ready`
4. ✅ Documentation accessible: http://localhost:8000/docs
5. ✅ Metrics available: `curl http://localhost:8000/metrics`
6. ✅ Database connected: Check readiness endpoint
7. ✅ Kafka connected: Check readiness endpoint

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Check environment
docker-compose exec api env | grep DATABASE_URL

# Verify dependencies
docker-compose ps postgres kafka
```

### Health Check Failing

```bash
# Manual health check
docker-compose exec api curl http://localhost:8000/health

# Check dependencies
curl http://localhost:8000/health/ready

# Increase start period
# Edit docker-compose.yml: start_period: 60s
```

### Database Connection Issues

```bash
# Test database connection
docker-compose exec postgres psql -U workflow_user -d workflow_db -c "SELECT 1;"

# Check DATABASE_URL
echo $DATABASE_URL

# Run migrations
docker-compose exec api alembic upgrade head
```

## Next Steps

1. Review [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions
2. Review [ENV_VARIABLES.md](./ENV_VARIABLES.md) for configuration options
3. Follow [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) for deployment
4. Set up monitoring and alerting
5. Configure backups for database
6. Set up CI/CD pipeline

## Support

- **Documentation:** [DEPLOYMENT.md](./DEPLOYMENT.md)
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Logs:** `docker-compose logs -f api`

---

**Configuration Status:** ✅ Complete  
**Last Updated:** 2024-01-15  
**Version:** 1.0.0
