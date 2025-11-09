# Workflow Management API

FastAPI-based REST API for managing the Centralized Executor and HTTP-Kafka Bridge system.

## Quick Start

### Using Docker Compose

1. Ensure you have the `.env.api` file configured (copy from `.env.api.example` if needed):
   ```bash
   cp .env.api.example .env.api
   # Edit .env.api with your configuration
   ```

2. Start the API service along with dependencies:
   ```bash
   docker compose --profile api up -d
   ```

3. The API will be available at `http://localhost:8000`

4. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - OpenAPI spec: http://localhost:8000/openapi.json

### Local Development

1. Install dependencies:
   ```bash
   pip install -r api/requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.api.example .env.api
   # Edit .env.api with your local configuration
   ```

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

4. Start the development server:
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Configuration

All configuration is managed through environment variables in `.env.api`. See `.env.api.example` for available options.

### Key Configuration Options

- `DATABASE_URL`: PostgreSQL connection string
- `KAFKA_BROKERS`: Kafka broker addresses
- `JWT_SECRET`: Secret key for JWT token generation (change in production!)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)

## Docker Compose Profiles

The API service uses the `api` profile. You can start different combinations:

```bash
# Start only infrastructure (Kafka, Postgres)
docker compose up -d

# Start API with infrastructure
docker compose --profile api up -d

# Start everything (API, Executor, Bridge)
docker compose --profile api --profile executor --profile bridge up -d
```

## Health Checks

- Basic health: `GET /health`
- Readiness check: `GET /health/ready`
- Metrics: `GET /metrics` (if enabled)

## Network

The API service is connected to the `orchestrator-network` bridge network, allowing it to communicate with:
- PostgreSQL database
- Kafka message broker
- Executor service (when running)
- Bridge service (when running)

## Development

The Dockerfile includes automatic database migration on startup. For local development, run migrations manually:

```bash
alembic upgrade head
```

To create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

## Security Notes

- The default `.env.api` includes a development JWT secret. **Change this in production!**
- Authentication is currently configured but can be disabled for initial development
- CORS is configured for local development origins by default

## Documentation

- **[Deployment Guide](./DEPLOYMENT.md)** - Complete deployment instructions for development and production
- **[Environment Variables Reference](./ENV_VARIABLES.md)** - Detailed documentation of all configuration options
- **[API Documentation](../API_DOCUMENTATION.md)** - Complete API endpoint documentation
- **[Database Setup](./DATABASE_SETUP.md)** - Database configuration and migration guide

## Deployment

For production deployment, see the [Deployment Guide](./DEPLOYMENT.md) which covers:
- Environment variable configuration
- Docker deployment
- Production best practices
- Health checks and monitoring
- Troubleshooting

Quick deployment using the deployment script:

```bash
# Interactive mode
./deploy-api.sh

# Command line mode
./deploy-api.sh dev        # Deploy development
./deploy-api.sh prod       # Deploy production
./deploy-api.sh status     # Check status
./deploy-api.sh logs       # View logs
```
