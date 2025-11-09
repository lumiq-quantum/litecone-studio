# Deployment Checklist

Use this checklist to ensure a successful deployment of the Workflow Management API.

## Pre-Deployment

### Development Environment

- [ ] `.env.api` file exists and is configured
- [ ] Database is accessible (PostgreSQL)
- [ ] Kafka is accessible
- [ ] Docker and Docker Compose are installed
- [ ] All required ports are available (8000, 5432, 9092)

### Production Environment

- [ ] `.env.api.production` file exists and is configured
- [ ] Production database is set up with SSL
- [ ] Kafka cluster is accessible
- [ ] Load balancer is configured (if applicable)
- [ ] SSL certificates are in place (if using HTTPS)
- [ ] Monitoring tools are configured (Prometheus, Grafana)
- [ ] Log aggregation is set up (ELK, CloudWatch, etc.)

## Configuration Validation

### Required Variables

- [ ] `DATABASE_URL` is set and valid
- [ ] `KAFKA_BROKERS` is set and reachable
- [ ] Database connection uses SSL in production
- [ ] Kafka brokers are reachable from API container

### Security Configuration

- [ ] `JWT_SECRET` is changed from default value
- [ ] `JWT_SECRET` is at least 32 characters long
- [ ] `JWT_SECRET` is different per environment
- [ ] `CORS_ORIGINS` specifies exact domains (not `*`)
- [ ] `API_RELOAD` is set to `false` in production
- [ ] Strong database password is used
- [ ] Secrets are not committed to version control

### Performance Configuration

- [ ] `API_WORKERS` is set appropriately (recommended: 2 x CPU cores + 1)
- [ ] `DATABASE_POOL_SIZE` is configured (recommended: workers * 2)
- [ ] `DATABASE_MAX_OVERFLOW` is configured (recommended: pool_size * 2)
- [ ] Resource limits are set in docker-compose (CPU, memory)

### Logging Configuration

- [ ] `LOG_LEVEL` is set to `INFO` or `WARNING` in production
- [ ] `LOG_FORMAT` is set to `json` for production
- [ ] Log rotation is configured
- [ ] Logs are being collected by monitoring system

## Deployment Steps

### 1. Build and Test

- [ ] Docker image builds successfully
  ```bash
  docker build -f Dockerfile.api -t workflow-api:latest .
  ```
- [ ] No build errors or warnings
- [ ] Image size is reasonable (< 1GB)

### 2. Database Migrations

- [ ] Backup existing database (production only)
- [ ] Test migrations in staging environment
- [ ] Run migrations successfully
  ```bash
  docker-compose exec api alembic upgrade head
  ```
- [ ] Verify database schema is correct
- [ ] Test rollback procedure (staging only)

### 3. Start Services

- [ ] Start infrastructure services (Postgres, Kafka)
  ```bash
  docker-compose up -d postgres kafka
  ```
- [ ] Wait for services to be ready (30-60 seconds)
- [ ] Start API service
  ```bash
  docker-compose --profile api up -d
  ```
- [ ] Check container status
  ```bash
  docker-compose ps api
  ```

### 4. Health Checks

- [ ] Basic health check passes
  ```bash
  curl http://localhost:8000/health
  ```
- [ ] Readiness check passes
  ```bash
  curl http://localhost:8000/health/ready
  ```
- [ ] Docker health check shows healthy
  ```bash
  docker inspect workflow-management-api | grep Health
  ```
- [ ] All dependencies are connected (database, Kafka)

### 5. Functional Testing

- [ ] API documentation is accessible
  - [ ] Swagger UI: http://localhost:8000/docs
  - [ ] ReDoc: http://localhost:8000/redoc
  - [ ] OpenAPI spec: http://localhost:8000/openapi.json
- [ ] Create test agent successfully
- [ ] Create test workflow successfully
- [ ] Execute test workflow successfully
- [ ] Monitor test workflow run
- [ ] Verify data is persisted in database

### 6. Integration Testing

- [ ] API can publish to Kafka
- [ ] Executor service receives messages
- [ ] Workflow execution completes successfully
- [ ] Run status is updated in database
- [ ] Audit logs are created
- [ ] Metrics are being collected

## Post-Deployment

### Monitoring

- [ ] Prometheus metrics endpoint is accessible
  ```bash
  curl http://localhost:8000/metrics
  ```
- [ ] Metrics are being scraped by Prometheus
- [ ] Grafana dashboards are displaying data
- [ ] Alerts are configured and working
- [ ] Log aggregation is working

### Performance

- [ ] Response times are acceptable (< 200ms for most endpoints)
- [ ] Database connection pool is not exhausted
- [ ] No memory leaks detected
- [ ] CPU usage is within expected range
- [ ] Kafka message throughput is adequate

### Security

- [ ] API is only accessible through intended channels
- [ ] Authentication is working (if enabled)
- [ ] CORS is properly configured
- [ ] No sensitive data in logs
- [ ] SSL/TLS is working (if configured)

### Documentation

- [ ] API documentation is up to date
- [ ] Environment variables are documented
- [ ] Deployment procedures are documented
- [ ] Runbook is available for operations team
- [ ] Contact information is available for support

## Rollback Plan

If deployment fails, follow these steps:

### 1. Stop New Version

```bash
docker-compose --profile api down
```

### 2. Rollback Database (if needed)

```bash
# Restore from backup
docker-compose exec postgres psql -U workflow_user -d workflow_db < backup.sql

# Or rollback migrations
docker-compose exec api alembic downgrade -1
```

### 3. Start Previous Version

```bash
# Checkout previous version
git checkout <previous-tag>

# Start services
docker-compose --profile api up -d
```

### 4. Verify Rollback

- [ ] Health checks pass
- [ ] API is functional
- [ ] Data integrity is maintained
- [ ] Users can access the system

## Troubleshooting

### Common Issues

| Issue | Check | Solution |
|-------|-------|----------|
| Container won't start | `docker-compose logs api` | Check environment variables and dependencies |
| Health check failing | `curl http://localhost:8000/health` | Increase start_period or check dependencies |
| Database connection error | `docker-compose ps postgres` | Verify DATABASE_URL and database is running |
| Kafka connection error | `docker-compose ps kafka` | Verify KAFKA_BROKERS and Kafka is running |
| Slow response times | `curl http://localhost:8000/metrics` | Increase workers or database pool size |
| Out of memory | `docker stats` | Increase memory limits or reduce workers |

### Getting Help

1. Check logs: `docker-compose logs -f api`
2. Check health: `curl http://localhost:8000/health/ready`
3. Check metrics: `curl http://localhost:8000/metrics`
4. Review [Deployment Guide](./DEPLOYMENT.md)
5. Review [Troubleshooting section](./DEPLOYMENT.md#troubleshooting)

## Sign-off

### Development Deployment

- [ ] Deployed by: ________________
- [ ] Date: ________________
- [ ] Version: ________________
- [ ] All checks passed: Yes / No
- [ ] Notes: ________________

### Production Deployment

- [ ] Deployed by: ________________
- [ ] Approved by: ________________
- [ ] Date: ________________
- [ ] Version: ________________
- [ ] All checks passed: Yes / No
- [ ] Rollback plan tested: Yes / No
- [ ] Monitoring confirmed: Yes / No
- [ ] Notes: ________________

---

## Quick Commands Reference

```bash
# Deploy development
./deploy-api.sh dev

# Deploy production
./deploy-api.sh prod

# Check status
./deploy-api.sh status

# View logs
./deploy-api.sh logs

# Run migrations
./deploy-api.sh migrate

# Check health
./deploy-api.sh health

# Stop services
./deploy-api.sh stop
```

---

**Last Updated:** 2024-01-15  
**Version:** 1.0.0
