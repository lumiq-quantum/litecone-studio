# Resource Requirements & Machine Sizing Guide

This guide helps you determine the appropriate machine size for running the Workflow Orchestrator platform.

## Quick Answer

### Minimum Requirements (Development/Testing)
- **CPU:** 4 cores
- **RAM:** 8 GB
- **Disk:** 20 GB SSD
- **Use Case:** Local development, testing, small workflows

### Recommended (Production - Light Load)
- **CPU:** 8 cores
- **RAM:** 16 GB
- **Disk:** 50 GB SSD
- **Use Case:** Small production deployments, <100 workflows/day

### Recommended (Production - Medium Load)
- **CPU:** 16 cores
- **RAM:** 32 GB
- **Disk:** 100 GB SSD
- **Use Case:** Medium production deployments, 100-1000 workflows/day

### Recommended (Production - High Load)
- **CPU:** 32+ cores
- **RAM:** 64+ GB
- **Disk:** 200+ GB SSD
- **Use Case:** Large production deployments, >1000 workflows/day

---

## Detailed Resource Breakdown

### Infrastructure Services

#### Kafka + Zookeeper
- **CPU:** 2-4 cores
- **RAM:** 2-4 GB
- **Disk:** 10-50 GB (depends on message retention)
- **Notes:** 
  - Kafka is memory-intensive
  - Disk I/O is critical for performance
  - SSD strongly recommended

#### PostgreSQL
- **CPU:** 2-4 cores
- **RAM:** 2-4 GB
- **Disk:** 10-100 GB (depends on workflow history)
- **Notes:**
  - RAM for caching is important
  - Connection pooling helps with many concurrent workflows
  - Regular backups recommended

#### Redis
- **CPU:** 1-2 cores
- **RAM:** 512 MB - 2 GB
- **Disk:** 1-5 GB
- **Notes:**
  - Primarily in-memory
  - Used for circuit breaker state
  - Persistence enabled for reliability

### Application Services

#### API Service
- **CPU:** 1-2 cores per instance
- **RAM:** 512 MB - 2 GB per instance
- **Notes:**
  - Can scale horizontally
  - Resource limits: 2 CPU, 2GB RAM (configured)
  - Handles REST API requests

#### Executor Service
- **CPU:** 1-2 cores per instance
- **RAM:** 512 MB - 1 GB per instance
- **Notes:**
  - Ephemeral, spawned per workflow
  - Multiple can run concurrently
  - Memory usage depends on workflow complexity

#### Bridge Service
- **CPU:** 1-2 cores per instance
- **RAM:** 512 MB - 1 GB per instance
- **Notes:**
  - Handles HTTP calls to agents
  - Can scale horizontally
  - Network I/O intensive

#### Consumer Service
- **CPU:** 1-2 cores per instance
- **RAM:** 512 MB - 1 GB per instance
- **Notes:**
  - Spawns executor instances
  - Can scale horizontally
  - Kafka consumer group for load balancing

#### UI Service
- **CPU:** 0.5-1 core
- **RAM:** 256-512 MB
- **Notes:**
  - Static files served by nginx
  - Very lightweight
  - Can handle many concurrent users

---

## Cloud Provider Recommendations

### AWS EC2

#### Development/Testing
```
Instance Type: t3.xlarge
- vCPUs: 4
- RAM: 16 GB
- Cost: ~$0.17/hour (~$122/month)
- Storage: 50 GB gp3 EBS
```

#### Production - Small
```
Instance Type: t3.2xlarge
- vCPUs: 8
- RAM: 32 GB
- Cost: ~$0.33/hour (~$240/month)
- Storage: 100 GB gp3 EBS
```

#### Production - Medium
```
Instance Type: m5.4xlarge
- vCPUs: 16
- RAM: 64 GB
- Cost: ~$0.77/hour (~$560/month)
- Storage: 200 GB gp3 EBS
```

#### Production - High Load
```
Instance Type: m5.8xlarge or c5.9xlarge
- vCPUs: 32-36
- RAM: 64-72 GB
- Cost: ~$1.54-1.84/hour (~$1,120-1,340/month)
- Storage: 500 GB gp3 EBS
```

### Google Cloud (GCE)

#### Development/Testing
```
Machine Type: n2-standard-4
- vCPUs: 4
- RAM: 16 GB
- Cost: ~$0.19/hour (~$140/month)
- Storage: 50 GB SSD
```

#### Production - Small
```
Machine Type: n2-standard-8
- vCPUs: 8
- RAM: 32 GB
- Cost: ~$0.39/hour (~$285/month)
- Storage: 100 GB SSD
```

#### Production - Medium
```
Machine Type: n2-standard-16
- vCPUs: 16
- RAM: 64 GB
- Cost: ~$0.78/hour (~$570/month)
- Storage: 200 GB SSD
```

### Azure

#### Development/Testing
```
VM Size: Standard_D4s_v3
- vCPUs: 4
- RAM: 16 GB
- Cost: ~$0.19/hour (~$140/month)
- Storage: 50 GB Premium SSD
```

#### Production - Small
```
VM Size: Standard_D8s_v3
- vCPUs: 8
- RAM: 32 GB
- Cost: ~$0.38/hour (~$280/month)
- Storage: 100 GB Premium SSD
```

#### Production - Medium
```
VM Size: Standard_D16s_v3
- vCPUs: 16
- RAM: 64 GB
- Cost: ~$0.77/hour (~$560/month)
- Storage: 200 GB Premium SSD
```

### DigitalOcean

#### Development/Testing
```
Droplet: CPU-Optimized 4 vCPU
- vCPUs: 4
- RAM: 8 GB
- Cost: $84/month
- Storage: 100 GB SSD
```

#### Production - Small
```
Droplet: CPU-Optimized 8 vCPU
- vCPUs: 8
- RAM: 16 GB
- Cost: $168/month
- Storage: 200 GB SSD
```

#### Production - Medium
```
Droplet: CPU-Optimized 16 vCPU
- vCPUs: 16
- RAM: 32 GB
- Cost: $336/month
- Storage: 400 GB SSD
```

---

## Resource Allocation by Service

### Typical Production Setup (16 vCPU, 32 GB RAM)

```yaml
Service              CPU    RAM     Instances
─────────────────────────────────────────────
Kafka + Zookeeper    3      4 GB    1
PostgreSQL           2      4 GB    1
Redis                1      1 GB    1
API                  2      2 GB    2
Consumer             2      2 GB    2
Bridge               2      2 GB    2
UI                   1      512 MB  1
Executor (dynamic)   2      2 GB    1-5
─────────────────────────────────────────────
Total Reserved       15     17.5 GB
Buffer               1      14.5 GB (for executor scaling)
```

---

## Scaling Strategies

### Vertical Scaling (Scale Up)
**When to use:**
- Single machine deployment
- Simpler management
- Lower complexity

**Limits:**
- Single point of failure
- Maximum machine size
- Downtime for upgrades

### Horizontal Scaling (Scale Out)
**When to use:**
- High availability required
- Need to handle variable load
- Want zero-downtime deployments

**Services that scale horizontally:**
- ✅ API (multiple instances behind load balancer)
- ✅ Consumer (Kafka consumer group)
- ✅ Bridge (multiple instances)
- ✅ Executor (spawned on demand)
- ✅ UI (multiple instances behind load balancer)

**Services that don't scale horizontally (single instance):**
- ❌ Kafka (requires cluster setup for HA)
- ❌ PostgreSQL (requires replication for HA)
- ❌ Redis (requires cluster/sentinel for HA)

---

## Storage Requirements

### Database (PostgreSQL)

#### Workflow Runs Table
```
Average row size: ~2 KB
Retention: 90 days
Workflows per day: 1000

Storage = 2 KB × 1000 × 90 = 180 MB
```

#### Step Executions Table
```
Average row size: ~1 KB
Steps per workflow: 5
Retention: 90 days
Workflows per day: 1000

Storage = 1 KB × 5 × 1000 × 90 = 450 MB
```

**Total for 1000 workflows/day:** ~1 GB/90 days

### Kafka

#### Message Retention
```
Average message size: 10 KB
Messages per workflow: 10
Retention: 7 days
Workflows per day: 1000

Storage = 10 KB × 10 × 1000 × 7 = 700 MB
```

**Total for 1000 workflows/day:** ~1 GB/week

### Redis

#### Circuit Breaker State
```
Per agent: ~1 KB
Number of agents: 100

Storage = 1 KB × 100 = 100 KB
```

**Total:** Negligible (<1 MB)

### Recommended Disk Allocation

| Component | Development | Production |
|-----------|-------------|------------|
| PostgreSQL | 10 GB | 50-100 GB |
| Kafka | 10 GB | 20-50 GB |
| Redis | 1 GB | 5 GB |
| Logs | 5 GB | 20 GB |
| System | 10 GB | 20 GB |
| **Total** | **36 GB** | **115-195 GB** |

---

## Network Requirements

### Bandwidth

#### Typical Workflow
- Request size: 10 KB
- Response size: 50 KB
- Total per workflow: 60 KB

#### For 1000 workflows/day
- Daily: 60 MB
- Monthly: 1.8 GB
- Bandwidth: Minimal

#### For 10,000 workflows/day
- Daily: 600 MB
- Monthly: 18 GB
- Bandwidth: Low

**Recommendation:** Standard cloud network (1 Gbps) is more than sufficient.

### Ports Required

```
External (Internet-facing):
- 8000: API (HTTPS recommended)
- 3000: UI (HTTPS recommended)

Internal (Docker network):
- 2181: Zookeeper
- 9092: Kafka
- 5432: PostgreSQL
- 6379: Redis
```

---

## Performance Benchmarks

### Expected Throughput

#### Small Machine (4 CPU, 8 GB RAM)
- Workflows/hour: 100-500
- Concurrent workflows: 5-10
- API requests/sec: 50-100

#### Medium Machine (8 CPU, 16 GB RAM)
- Workflows/hour: 500-2000
- Concurrent workflows: 10-20
- API requests/sec: 100-500

#### Large Machine (16 CPU, 32 GB RAM)
- Workflows/hour: 2000-5000
- Concurrent workflows: 20-50
- API requests/sec: 500-1000

### Latency

- API response time: 50-200ms
- Workflow start time: 100-500ms
- Step execution overhead: 50-100ms

---

## Monitoring & Alerts

### Key Metrics to Monitor

#### System Resources
- CPU usage (alert at >80%)
- Memory usage (alert at >85%)
- Disk usage (alert at >80%)
- Disk I/O (alert at saturation)

#### Application Metrics
- Workflow success rate
- Average workflow duration
- Queue depth (Kafka lag)
- Database connection pool usage
- API response times

#### Infrastructure Health
- Kafka broker health
- PostgreSQL replication lag (if using HA)
- Redis memory usage
- Container restart count

---

## Cost Optimization Tips

### 1. Use Spot/Preemptible Instances
- Save 60-80% on compute costs
- Suitable for non-critical environments
- Use for development/staging

### 2. Right-Size Your Instances
- Start small and scale up
- Monitor actual usage
- Don't over-provision

### 3. Use Reserved Instances
- Save 30-50% for production
- Commit to 1-3 years
- Suitable for stable workloads

### 4. Optimize Storage
- Use gp3 instead of gp2 on AWS
- Enable compression in PostgreSQL
- Set appropriate Kafka retention

### 5. Scale Down Non-Production
- Stop dev/test environments after hours
- Use smaller instances for staging
- Automate start/stop schedules

---

## Deployment Checklist

### Before Deployment

- [ ] Choose appropriate machine size
- [ ] Provision storage (SSD recommended)
- [ ] Configure firewall rules
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Set resource limits in docker-compose

### After Deployment

- [ ] Verify all services are running
- [ ] Check resource usage
- [ ] Run test workflows
- [ ] Monitor for 24 hours
- [ ] Adjust resources if needed
- [ ] Set up alerts

---

## Example Deployment Commands

### Using Published Images (Recommended)

```bash
# Pull images from GHCR
docker pull ghcr.io/YOUR_USERNAME/orchestrator-api:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-executor:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-bridge:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-consumer:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-ui:latest

# Start with production compose file
docker-compose -f docker-compose.prod.yml up -d
```

### Resource Monitoring

```bash
# Monitor resource usage
docker stats

# Check logs
docker-compose logs -f

# View specific service
docker stats workflow-management-api
```

---

## Troubleshooting

### High CPU Usage
- Check for infinite loops in workflows
- Review parallel execution limits
- Scale horizontally (add more instances)

### High Memory Usage
- Check for memory leaks
- Review workflow data sizes
- Increase memory limits
- Add swap space (temporary)

### Disk Full
- Clean up old logs
- Reduce Kafka retention
- Archive old workflow data
- Increase disk size

### Slow Performance
- Check database query performance
- Review Kafka lag
- Optimize workflow definitions
- Add indexes to database
- Scale up or out

---

## Summary

### Quick Sizing Guide

| Workload | Machine Size | Monthly Cost (AWS) |
|----------|--------------|-------------------|
| Development | 4 CPU, 8 GB | ~$100-150 |
| Small Production | 8 CPU, 16 GB | ~$250-300 |
| Medium Production | 16 CPU, 32 GB | ~$550-600 |
| Large Production | 32 CPU, 64 GB | ~$1,100-1,400 |

### Recommendations

1. **Start with 8 CPU, 16 GB RAM** for production
2. **Use SSD storage** for better performance
3. **Monitor resource usage** for first week
4. **Scale up or out** based on actual usage
5. **Set up alerts** for resource thresholds
6. **Plan for growth** - easier to scale up than down

---

## Need Help?

- Review [Deployment Guide](DEPLOYMENT_GUIDE.md)
- Check [CI/CD Setup](CICD_SETUP.md)
- See [Troubleshooting](../testing/MANUAL_TESTING_GUIDE.md)
