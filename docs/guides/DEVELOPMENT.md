# Development Guide

This guide will help you set up and run the complete Workflow Management system locally.

## Prerequisites

- Python 3.11+
- Node.js 20.19+ or 22.12+
- PostgreSQL 14+
- Kafka (optional, for async execution)

## Quick Start

### 1. Start the Backend API

```bash
# Activate virtual environment
source venv/bin/activate

# Start the API server
./start_api.sh
```

The API will be available at: **http://localhost:8000**
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

### 2. Start the Frontend UI

```bash
# Navigate to frontend directory
cd workflow-ui

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

The UI will be available at: **http://localhost:5173**

## CORS Configuration

The API is now configured to allow **all origins** for development:

```env
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=false
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*
```

### For Production

Update `.env.api` to restrict CORS to specific origins:

```env
CORS_ORIGINS=https://your-domain.com,https://app.your-domain.com
CORS_ALLOW_CREDENTIALS=true
```

## Database Setup

### Using Docker

```bash
# Start PostgreSQL with Docker
docker run -d \
  --name workflow-postgres \
  -e POSTGRES_USER=workflow_user \
  -e POSTGRES_PASSWORD=workflow_pass \
  -e POSTGRES_DB=workflow_db \
  -p 5432:5432 \
  postgres:14
```

### Manual Setup

```sql
-- Create database and user
CREATE DATABASE workflow_db;
CREATE USER workflow_user WITH PASSWORD 'workflow_pass';
GRANT ALL PRIVILEGES ON DATABASE workflow_db TO workflow_user;
```

### Run Migrations

```bash
# Apply database migrations
alembic upgrade head
```

## Environment Variables

### Backend (.env.api)

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Database
DATABASE_URL=postgresql://workflow_user:workflow_pass@localhost:5432/workflow_db

# CORS (Development)
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=false

# Security (Change in production!)
JWT_SECRET=dev-secret-key-change-in-production
```

### Frontend (workflow-ui/.env)

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_POLLING_INTERVAL=2000
VITE_APP_NAME=Workflow Manager
```

## Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run specific test file
pytest tests/test_agents.py
```

### Frontend Tests

```bash
cd workflow-ui

# Run tests
npm test

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

## Common Issues

### CORS Errors

**Problem**: Browser shows CORS errors when calling API

**Solution**:
1. Ensure API server is running
2. Check `.env.api` has `CORS_ORIGINS=*`
3. Restart the API server after changing CORS settings
4. Clear browser cache and reload

### Database Connection Errors

**Problem**: API fails to connect to database

**Solution**:
1. Verify PostgreSQL is running: `pg_isready`
2. Check database credentials in `.env.api`
3. Ensure database exists: `psql -l`
4. Test connection: `psql postgresql://workflow_user:workflow_pass@localhost:5432/workflow_db`

### Port Already in Use

**Problem**: Port 8000 or 5173 is already in use

**Solution**:
```bash
# Find process using port
lsof -i :8000
lsof -i :5173

# Kill the process
kill -9 <PID>

# Or use different ports
API_PORT=8001 ./start_api.sh
npm run dev -- --port 5174
```

### Frontend Can't Connect to API

**Problem**: Frontend shows "Unable to connect to server"

**Solution**:
1. Verify API is running: `curl http://localhost:8000/health`
2. Check `VITE_API_URL` in `workflow-ui/.env`
3. Ensure no firewall blocking localhost connections
4. Check browser console for detailed error messages

## Development Workflow

### 1. Create a New Feature

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes to backend
cd api/
# Edit files...

# Make changes to frontend
cd workflow-ui/
# Edit files...

# Run tests
pytest  # Backend
npm test  # Frontend

# Commit changes
git add .
git commit -m "Add my feature"
```

### 2. Database Changes

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Review migration file
cat alembic/versions/<revision_id>_add_new_table.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### 3. API Changes

When adding new endpoints:

1. Update models in `api/models/`
2. Update schemas in `api/schemas/`
3. Update repository in `api/repositories/`
4. Update service in `api/services/`
5. Update routes in `api/routes/`
6. Add tests in `tests/`
7. Update OpenAPI docs (automatic)

### 4. Frontend Changes

When adding new features:

1. Create components in `workflow-ui/src/components/`
2. Add API calls in `workflow-ui/src/services/api/`
3. Create hooks in `workflow-ui/src/hooks/`
4. Add pages in `workflow-ui/src/pages/`
5. Update routes in `workflow-ui/src/App.tsx`
6. Add tests in `__tests__/` directories

## Debugging

### Backend Debugging

```bash
# Enable debug logging
LOG_LEVEL=DEBUG ./start_api.sh

# Use Python debugger
import pdb; pdb.set_trace()

# View logs
tail -f logs/api.log
```

### Frontend Debugging

```bash
# Enable verbose logging
VITE_LOG_LEVEL=debug npm run dev

# Use browser DevTools
# - Console for logs
# - Network tab for API calls
# - React DevTools for component inspection
```

## Performance Optimization

### Backend

- Use database connection pooling (already configured)
- Enable query caching for frequently accessed data
- Use async/await for I/O operations
- Monitor with Prometheus metrics at `/metrics`

### Frontend

- Use React Query for data caching (already configured)
- Lazy load routes and components
- Optimize images and assets
- Use production build for testing: `npm run build && npm run preview`

## Useful Commands

```bash
# Backend
python -m api.main  # Start API directly
alembic current  # Show current migration
alembic history  # Show migration history
pytest -v  # Verbose test output

# Frontend
npm run lint  # Check code style
npm run format  # Format code
npm run type-check  # Check TypeScript types
npm run build  # Build for production

# Database
psql workflow_db  # Connect to database
pg_dump workflow_db > backup.sql  # Backup database
psql workflow_db < backup.sql  # Restore database

# Docker
docker-compose up -d  # Start all services
docker-compose logs -f api  # View API logs
docker-compose down  # Stop all services
```

## Next Steps

1. **Set up Kafka** for async workflow execution
2. **Configure authentication** for production use
3. **Set up monitoring** with Prometheus and Grafana
4. **Deploy to staging** environment
5. **Set up CI/CD** pipeline

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Tailwind CSS](https://tailwindcss.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Support

For issues or questions:
- Check the troubleshooting section above
- Review API documentation at `/docs`
- Check application logs
- Create an issue in the project repository
