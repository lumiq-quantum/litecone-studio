# Docker Compose Commands

This project now uses a unified `docker-compose.yml` file with profiles to manage different service combinations.

## Quick Start Commands

### Start Everything (Full Stack)
```bash
docker compose --profile api --profile consumer --profile ui up -d
```

### Start Core Infrastructure Only (Kafka, Postgres, Zookeeper)
```bash
docker compose up -d
```

### Start API + UI (Most Common for Development)
```bash
docker compose --profile api --profile ui up -d
```

### Start with Test Agents
```bash
docker compose --profile api --profile consumer --profile test up -d
```

### Production Deployment
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile api --profile consumer --profile ui up -d
```

## Rebuild Without Cache

### Rebuild API Only
```bash
docker compose stop api
docker compose rm -f api
docker compose build --no-cache api
docker compose --profile api up -d
```

### Rebuild UI Only
```bash
docker compose stop workflow-ui
docker compose rm -f workflow-ui
docker compose build --no-cache workflow-ui
docker compose --profile ui up -d
```

### Rebuild Everything
```bash
docker compose down -v
docker compose build --no-cache
docker compose --profile api --profile consumer --profile ui up -d
```

## Service Profiles

- **No profile**: Core infrastructure (Zookeeper, Kafka, Postgres)
- **api**: Workflow Management API
- **consumer**: Execution Consumer
- **executor**: Centralized Executor
- **bridge**: External Agent Executor
- **ui**: Workflow UI (React frontend)
- **test**: Mock agents for testing

## Individual Service Management

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f workflow-ui
```

### Stop Services
```bash
# Stop all
docker compose down

# Stop specific profile
docker compose --profile api down
```

### Check Status
```bash
docker compose ps
```

## Access Points

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **UI**: http://localhost:3000
- **Postgres**: localhost:5432
- **Kafka**: localhost:9092
- **Mock Agent Registry**: http://localhost:8080 (test profile)

## Environment Variables

Create these files in the root directory:
- `.env` - For executor/consumer services
- `.env.api` - For API service

For UI configuration, set these in your shell or `.env` file:
- `VITE_API_URL` (default: http://localhost:8000/api/v1)
- `VITE_POLLING_INTERVAL` (default: 2000)
- `VITE_APP_NAME` (default: Workflow Manager)
