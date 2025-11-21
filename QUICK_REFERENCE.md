# Quick Reference Guide

Fast access to commonly used files and commands.

## 🚀 Quick Start

```bash
./quick-start.sh              # Start everything and run test
```

## 📖 Essential Documentation

| What | Where |
|------|-------|
| **Getting Started** | [docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md) |
| **API Reference** | [docs/api/API_DOCUMENTATION.md](docs/api/API_DOCUMENTATION.md) |
| **Workflow Format** | [docs/guides/WORKFLOW_FORMAT.md](docs/guides/WORKFLOW_FORMAT.md) |
| **Deployment** | [docs/deployment/DEPLOYMENT_GUIDE.md](docs/deployment/DEPLOYMENT_GUIDE.md) |
| **Testing** | [docs/testing/MANUAL_TESTING_GUIDE.md](docs/testing/MANUAL_TESTING_GUIDE.md) |

## 🔧 Common Scripts

| Task | Command |
|------|---------|
| **Start API** | `./scripts/start_api.sh` |
| **Restart API** | `./scripts/restart-api.sh` |
| **Run Migrations** | `./scripts/run-migrations.sh` |
| **Test Circuit Breaker** | `./scripts/test_circuit_breaker_simple.sh` |
| **Deploy API** | `./scripts/deploy-api.sh` |
| **Build UI** | `./scripts/ui-build.sh` |

## 🧪 Running Tests

```bash
# All tests
pytest tests/

# Specific test
pytest tests/test_circuit_breaker.py

# With coverage
pytest tests/ --cov=src --cov-report=html

# E2E test
python tests/e2e_test.py
```

## 🐳 Docker Commands

```bash
# Start infrastructure
docker-compose up -d zookeeper kafka postgres redis

# Start all services
docker-compose --profile executor --profile bridge --profile consumer up -d

# View logs
docker-compose logs -f

# Stop everything
./cleanup.sh

# Rebuild services
docker-compose build
```

## 📂 Project Structure

```
.
├── docs/          # All documentation (organized by category)
├── tests/         # All test files
├── scripts/       # All shell scripts and utilities
├── src/           # Source code
├── api/           # REST API service
├── workflow-ui/   # React UI
├── examples/      # Example workflows
└── migrations/    # Database migrations
```

## 🔍 Finding Things

| Looking for... | Check... |
|----------------|----------|
| **Documentation** | `docs/README.md` |
| **Scripts** | `scripts/README.md` |
| **Tests** | `tests/README.md` |
| **Examples** | `examples/README.md` |
| **Project Structure** | `PROJECT_STRUCTURE.md` |
| **Cleanup Details** | `CLEANUP_SUMMARY.md` |

## 🌟 Features

| Feature | Documentation |
|---------|---------------|
| **Parallel Execution** | [docs/features/parallel_execution.md](docs/features/parallel_execution.md) |
| **Conditional Logic** | [docs/features/conditional_logic.md](docs/features/conditional_logic.md) |
| **Loop Execution** | [docs/features/loop_execution.md](docs/features/loop_execution.md) |
| **Fork-Join** | [docs/features/fork_join_pattern.md](docs/features/fork_join_pattern.md) |
| **Circuit Breaker** | [docs/features/circuit_breaker.md](docs/features/circuit_breaker.md) |

## 🔗 API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# API docs (Swagger)
open http://localhost:8000/docs

# List workflows
curl http://localhost:8000/api/v1/workflows

# Execute workflow
curl -X POST http://localhost:8000/api/v1/workflows/{id}/execute \
  -H "Content-Type: application/json" \
  -d '{"input_data": {...}}'

# Get run status
curl http://localhost:8000/api/v1/runs/{run_id}
```

## 🛠️ Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Start development environment
docker-compose up -d

# Run API in development mode
uvicorn api.main:app --reload

# Run UI in development mode
cd workflow-ui && npm start
```

## 📊 Monitoring

```bash
# Check API status
./scripts/check-api-status.sh

# View executor logs
docker-compose logs executor

# View bridge logs
docker-compose logs bridge

# View all logs
docker-compose logs -f
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **API won't start** | Check `./scripts/check-api-status.sh` |
| **Database errors** | Run `./scripts/run-migrations.sh` |
| **Multiple heads** | Run `./scripts/fix-multiple-heads.sh` |
| **Services not responding** | Run `./scripts/fix-and-rebuild.sh` |
| **Need fresh start** | Run `./cleanup.sh --volumes` then `./quick-start.sh` |

## 📝 Creating Workflows

1. See format: [docs/guides/WORKFLOW_FORMAT.md](docs/guides/WORKFLOW_FORMAT.md)
2. Check examples: `examples/*.json`
3. Validate with API: POST to `/api/v1/workflows`
4. Test execution: POST to `/api/v1/workflows/{id}/execute`

## 🎯 Next Steps

1. **New to the project?** → [docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md)
2. **Setting up development?** → [docs/guides/DEVELOPMENT.md](docs/guides/DEVELOPMENT.md)
3. **Deploying to production?** → [docs/deployment/DEPLOYMENT_GUIDE.md](docs/deployment/DEPLOYMENT_GUIDE.md)
4. **Writing tests?** → [tests/README.md](tests/README.md)
5. **Need help?** → Check [docs/README.md](docs/README.md) for full documentation index

---

**Tip:** Bookmark this file for quick access to common tasks!
