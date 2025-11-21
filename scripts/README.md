# Scripts

This directory contains all shell scripts and utility scripts for the project.

## Quick Start Scripts (Root Level)

These remain at the project root for easy access:
- `quick-start.sh` - Fast setup and test execution
- `cleanup.sh` - Clean up Docker containers and volumes

## API Management Scripts

### Starting/Stopping
- `start_api.sh` - Start the API server
- `start.sh` - Start all services
- `restart-api.sh` - Restart the API server
- `quick-restart-api.sh` - Quick API restart
- `check-api-status.sh` - Check API health status

### Deployment
- `deploy-api.sh` - Deploy API to production
- `deploy_parallel_execution.sh` - Deploy parallel execution feature

## Database & Migration Scripts

- `run-migrations.sh` - Run database migrations
- `wait-and-migrate.sh` - Wait for database and run migrations
- `fix-multiple-heads.sh` - Fix Alembic multiple heads issue
- `verify_parallel_execution_migration.py` - Verify parallel execution migration

## Testing Scripts

- `test_circuit_breaker_live.sh` - Live circuit breaker testing
- `test_circuit_breaker_simple.sh` - Simple circuit breaker test
- `test-step-by-step.sh` - Step-by-step testing guide
- `run_e2e_test.sh` - Run end-to-end tests

## Workflow Management Scripts

- `migrate_workflows.py` - Migrate workflows to new format
- `register_agents.py` - Register agents with the system

## UI Scripts

- `ui-build.sh` - Build the UI (formerly workflow-ui/build.sh)
- `ui-deploy.sh` - Deploy the UI (formerly workflow-ui/deploy.sh)

## Troubleshooting Scripts

- `fix-and-rebuild.sh` - Fix issues and rebuild services

## Configuration

- `agents.yaml.example` - Example agent configuration

## Usage Examples

### Start the system
```bash
./start.sh
```

### Run migrations
```bash
./run-migrations.sh
```

### Test circuit breaker
```bash
./test_circuit_breaker_simple.sh
```

### Deploy to production
```bash
./deploy-api.sh
```

## Adding New Scripts

When adding new scripts:
1. Place them in this directory
2. Make them executable: `chmod +x script-name.sh`
3. Add documentation here
4. Use clear, descriptive names
5. Include usage comments at the top of the script
