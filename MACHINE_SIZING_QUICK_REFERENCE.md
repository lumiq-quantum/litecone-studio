# Machine Sizing Quick Reference

## TL;DR - What Machine Do I Need?

### 🧪 Development/Testing
```
CPU:  4 cores
RAM:  8 GB
Disk: 20 GB SSD
Cost: ~$100/month
```
**Use for:** Local development, testing, demos

### 🚀 Production - Small
```
CPU:  8 cores
RAM:  16 GB
Disk: 50 GB SSD
Cost: ~$250/month
```
**Use for:** <100 workflows/day, small team

### 🏢 Production - Medium (Recommended)
```
CPU:  16 cores
RAM:  32 GB
Disk: 100 GB SSD
Cost: ~$550/month
```
**Use for:** 100-1000 workflows/day, medium team

### 🏭 Production - Large
```
CPU:  32+ cores
RAM:  64+ GB
Disk: 200+ GB SSD
Cost: ~$1,100+/month
```
**Use for:** >1000 workflows/day, large team

---

## Cloud Provider Quick Picks

### AWS
| Size | Instance Type | vCPU | RAM | Cost/Month |
|------|---------------|------|-----|------------|
| Dev | t3.xlarge | 4 | 16 GB | ~$122 |
| Small | t3.2xlarge | 8 | 32 GB | ~$240 |
| Medium | m5.4xlarge | 16 | 64 GB | ~$560 |
| Large | m5.8xlarge | 32 | 128 GB | ~$1,120 |

### Google Cloud
| Size | Machine Type | vCPU | RAM | Cost/Month |
|------|--------------|------|-----|------------|
| Dev | n2-standard-4 | 4 | 16 GB | ~$140 |
| Small | n2-standard-8 | 8 | 32 GB | ~$285 |
| Medium | n2-standard-16 | 16 | 64 GB | ~$570 |
| Large | n2-standard-32 | 32 | 128 GB | ~$1,140 |

### Azure
| Size | VM Size | vCPU | RAM | Cost/Month |
|------|---------|------|-----|------------|
| Dev | Standard_D4s_v3 | 4 | 16 GB | ~$140 |
| Small | Standard_D8s_v3 | 8 | 32 GB | ~$280 |
| Medium | Standard_D16s_v3 | 16 | 64 GB | ~$560 |
| Large | Standard_D32s_v3 | 32 | 128 GB | ~$1,120 |

### DigitalOcean
| Size | Droplet | vCPU | RAM | Cost/Month |
|------|---------|------|-----|------------|
| Dev | CPU-Opt 4 | 4 | 8 GB | $84 |
| Small | CPU-Opt 8 | 8 | 16 GB | $168 |
| Medium | CPU-Opt 16 | 16 | 32 GB | $336 |
| Large | CPU-Opt 32 | 32 | 64 GB | $672 |

---

## What's Running?

### Infrastructure (Always Running)
- **Kafka + Zookeeper** - Message broker (3-4 CPU, 4 GB RAM)
- **PostgreSQL** - Database (2-4 CPU, 4 GB RAM)
- **Redis** - Cache/Circuit breaker (1 CPU, 1 GB RAM)

### Application Services
- **API** - REST API (1-2 CPU, 1-2 GB RAM)
- **Consumer** - Workflow consumer (1-2 CPU, 1 GB RAM)
- **Bridge** - HTTP-Kafka bridge (1-2 CPU, 1 GB RAM)
- **UI** - Web interface (0.5 CPU, 512 MB RAM)
- **Executor** - Workflow executor (1-2 CPU, 1 GB RAM per workflow)

---

## Quick Deployment

### 1. Choose Your Machine
Pick from the table above based on your workload.

### 2. Install Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### 3. Pull Images
```bash
docker pull ghcr.io/YOUR_USERNAME/orchestrator-api:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-executor:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-bridge:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-consumer:latest
docker pull ghcr.io/YOUR_USERNAME/orchestrator-ui:latest
```

### 4. Start Services
```bash
# Copy environment files
cp .env.example .env
cp .env.api.example .env.api

# Start all services
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Verify
```bash
# Check services
docker-compose ps

# Check resource usage
docker stats

# Access UI
open http://YOUR_SERVER_IP:3000
```

---

## Resource Usage by Workload

### Light Load (<100 workflows/day)
```
Typical Usage:
- CPU: 20-40%
- RAM: 8-12 GB
- Disk I/O: Low
- Network: <1 Mbps

Recommended: 8 CPU, 16 GB RAM
```

### Medium Load (100-1000 workflows/day)
```
Typical Usage:
- CPU: 40-70%
- RAM: 16-24 GB
- Disk I/O: Medium
- Network: 1-5 Mbps

Recommended: 16 CPU, 32 GB RAM
```

### Heavy Load (>1000 workflows/day)
```
Typical Usage:
- CPU: 70-90%
- RAM: 32-48 GB
- Disk I/O: High
- Network: 5-10 Mbps

Recommended: 32 CPU, 64 GB RAM
```

---

## Storage Needs

### Database Growth
```
1000 workflows/day = ~1 GB/90 days
10,000 workflows/day = ~10 GB/90 days
```

### Kafka Retention
```
1000 workflows/day = ~1 GB/week
10,000 workflows/day = ~10 GB/week
```

### Recommended Disk
- **Development:** 20-50 GB
- **Production:** 100-200 GB
- **High Volume:** 500+ GB

**Always use SSD for better performance!**

---

## Scaling Tips

### When to Scale Up (Vertical)
- ✅ CPU usage consistently >80%
- ✅ Memory usage consistently >85%
- ✅ Workflows taking longer to complete
- ✅ API response times increasing

### When to Scale Out (Horizontal)
- ✅ Need high availability
- ✅ Variable workload patterns
- ✅ Want zero-downtime deployments
- ✅ Hit single-machine limits

### Services That Scale Horizontally
- ✅ API (add more instances)
- ✅ Consumer (Kafka consumer group)
- ✅ Bridge (add more instances)
- ✅ Executor (spawned on demand)

---

## Cost Optimization

### Save 60-80%
- Use spot/preemptible instances for dev/test
- Stop non-production environments after hours

### Save 30-50%
- Use reserved instances for production
- Commit to 1-3 year terms

### Save 20-30%
- Right-size your instances
- Monitor and adjust based on actual usage
- Use gp3 instead of gp2 storage (AWS)

---

## Monitoring Checklist

### Set Alerts For:
- [ ] CPU usage >80%
- [ ] Memory usage >85%
- [ ] Disk usage >80%
- [ ] Workflow failure rate >5%
- [ ] API response time >1s
- [ ] Kafka lag >1000 messages

### Monitor Daily:
- [ ] Resource usage trends
- [ ] Workflow success rate
- [ ] Average workflow duration
- [ ] Error logs
- [ ] Database size
- [ ] Kafka disk usage

---

## Common Issues

### "Out of Memory"
**Solution:** Increase RAM or add swap
```bash
# Add 4GB swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### "Disk Full"
**Solution:** Clean up or increase disk
```bash
# Clean Docker
docker system prune -a

# Check disk usage
df -h
du -sh /var/lib/docker/*
```

### "High CPU Usage"
**Solution:** Scale up or optimize workflows
```bash
# Check what's using CPU
docker stats

# Scale up instance size
# Or add more instances
```

---

## Quick Commands

### Check Resource Usage
```bash
# Overall system
htop

# Docker containers
docker stats

# Disk usage
df -h
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100
```

### Restart Services
```bash
# All services
docker-compose restart

# Specific service
docker-compose restart api
```

---

## Need More Details?

See the complete guide: [docs/deployment/RESOURCE_REQUIREMENTS.md](docs/deployment/RESOURCE_REQUIREMENTS.md)

---

**Last Updated:** 2024-11-21  
**Recommended Starting Point:** 8 CPU, 16 GB RAM, 50 GB SSD
