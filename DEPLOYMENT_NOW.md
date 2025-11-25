# Deploy Right Now - Quick Guide

## 🚀 Deploy All Services Immediately

You have 3 options to deploy right now:

---

## Option 1: Use Standalone Production File (RECOMMENDED)

I've created a standalone production-ready file for you.

```bash
# Deploy all services
docker-compose -f docker-compose.prod.standalone.yml up -d

# Check status
docker-compose -f docker-compose.prod.standalone.yml ps

# View logs
docker-compose -f docker-compose.prod.standalone.yml logs -f
```

**What this does:**
- ✅ Starts all infrastructure (Kafka, PostgreSQL, Redis)
- ✅ Starts all application services (API, Consumer, Bridge, UI)
- ✅ Includes health checks
- ✅ Includes resource limits
- ✅ Production-ready configuration

**File:** `docker-compose.prod.standalone.yml`

---

## Option 2: Use Base File with Profiles

Use the base docker-compose.yml file:

```bash
# Start infrastructure first
docker-compose up -d zookeeper kafka postgres redis

# Wait 10 seconds for Kafka to be ready
sleep 10

# Start application services
docker-compose --profile api --profile consumer --profile bridge --profile ui up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**What this does:**
- ✅ Starts all services
- ⚠️ Builds images locally (slower first time)
- ⚠️ Missing some resource limits

---

## Option 3: Use Override File (Current Setup)

Use both files together:

```bash
# Deploy with production overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml \
  --profile api --profile consumer --profile bridge --profile ui up -d

# Check status
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

**What this does:**
- ✅ Starts all services
- ✅ Applies production resource limits
- ⚠️ Builds images locally

---

## 🎯 My Recommendation

**Use Option 1** - The standalone file I created:

```bash
docker-compose -f docker-compose.prod.standalone.yml up -d
```

This is:
- ✅ Production-ready
- ✅ Has all fixes
- ✅ Easy to use
- ✅ Complete and standalone

---

## 📋 After Deployment

### 1. Verify Services

```bash
# Check all services are running
docker-compose -f docker-compose.prod.standalone.yml ps

# Should see:
# - zookeeper (running)
# - kafka (running)
# - postgres (running, healthy)
# - redis (running, healthy)
# - api (running, healthy)
# - consumer (running)
# - bridge (running)
# - ui (running, healthy)
```

### 2. Check Health

```bash
# API health
curl http://localhost:8000/health

# UI
curl http://localhost:3000/

# Database
docker exec postgres pg_isready -U workflow_user

# Redis
docker exec redis redis-cli ping
```

### 3. View Logs

```bash
# All services
docker-compose -f docker-compose.prod.standalone.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.standalone.yml logs -f api
```

### 4. Monitor Resources

```bash
# Real-time resource usage
docker stats

# Should see all services with their CPU and memory usage
```

---

## 🔧 Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose -f docker-compose.prod.standalone.yml logs service-name

# Restart service
docker-compose -f docker-compose.prod.standalone.yml restart service-name

# Rebuild and restart
docker-compose -f docker-compose.prod.standalone.yml up -d --build service-name
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker exec postgres pg_isready -U workflow_user

# Check connection
docker exec postgres psql -U workflow_user -d workflow_db -c "SELECT 1;"

# View logs
docker-compose -f docker-compose.prod.standalone.yml logs postgres
```

### Kafka Issues

```bash
# Check Kafka logs
docker-compose -f docker-compose.prod.standalone.yml logs kafka

# Wait longer for Kafka to be ready (it takes 30-60 seconds)
sleep 30
```

### Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :8000
sudo lsof -i :3000

# Stop conflicting service or change port in docker-compose file
```

---

## 📊 Resource Usage

With all services running:

```
Service          CPU    RAM     
─────────────────────────────────
Kafka            2      4 GB    
PostgreSQL       2      4 GB    
Redis            1      2 GB    
API              4      4 GB    
Consumer         2      2 GB    
Bridge           2      2 GB    
UI               1      512 MB  
─────────────────────────────────
Total (Limits)   14     18.5 GB
```

**Your Machine Should Have:**
- CPU: 16+ cores
- RAM: 32+ GB
- Disk: 50+ GB SSD

---

## 🎉 Success Criteria

After deployment, you should be able to:

- ✅ Access UI at http://localhost:3000
- ✅ Access API at http://localhost:8000
- ✅ See API docs at http://localhost:8000/docs
- ✅ All services show as "healthy" or "running"
- ✅ Create and execute workflows

---

## 🔄 Future: Use CI/CD Generated File

After you commit and push changes, CI/CD will generate a new `docker-compose.prod.yml` that:
- Uses published images from GHCR (no local building)
- Has version tags
- Is automatically updated on each release

Then you can use:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📚 Documentation

- [DOCKER_COMPOSE_REVIEW.md](DOCKER_COMPOSE_REVIEW.md) - Detailed review
- [docs/deployment/DOCKER_COMPOSE_PROD_GUIDE.md](docs/deployment/DOCKER_COMPOSE_PROD_GUIDE.md) - Production guide
- [MACHINE_SIZING_QUICK_REFERENCE.md](MACHINE_SIZING_QUICK_REFERENCE.md) - Machine sizing

---

**Ready to deploy?** Run:
```bash
docker-compose -f docker-compose.prod.standalone.yml up -d
```
