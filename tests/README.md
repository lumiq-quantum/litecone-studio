# Tests

This directory contains all test files for the project.

## Test Files

### Integration Tests
- `test_api_executor_integration.py` - API and executor integration tests
- `test_workflow_jsonrpc.py` - Workflow JSON-RPC protocol tests
- `test_jsonrpc_deployment.py` - JSON-RPC deployment tests

### Feature Tests
- `test_circuit_breaker.py` - Circuit breaker functionality tests
- `test_conditional_logic.py` - Conditional logic execution tests
- `test_error_scenarios.py` - Error handling and edge case tests

### End-to-End Tests
- `e2e_test.py` - Comprehensive end-to-end workflow tests
- `simple_e2e_test.py` - Simple end-to-end test scenarios

### Database Tests
- `test_database_setup.py` - Database setup and configuration tests

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test file
```bash
pytest tests/test_circuit_breaker.py
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run with coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Categories

### Unit Tests
Test individual components in isolation:
- Condition evaluators
- Input mapping resolvers
- Circuit breaker logic

### Integration Tests
Test component interactions:
- API to executor communication
- Executor to bridge communication
- Database operations

### End-to-End Tests
Test complete workflows:
- Multi-step workflows
- Parallel execution
- Conditional branching
- Error handling

## Test Environment Setup

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Start test infrastructure
docker-compose up -d zookeeper kafka postgres redis

# Start mock agents
docker-compose -f docker-compose.test.yml up -d
```

### Environment Variables
```bash
export DATABASE_URL=postgresql://workflow_user:workflow_pass@localhost:5432/workflow_db
export KAFKA_BROKERS=localhost:9092
export REDIS_URL=redis://localhost:6379
```

## Writing New Tests

### Test Structure
```python
import pytest
from src.executor.centralized_executor import CentralizedExecutor

@pytest.mark.asyncio
async def test_feature_name():
    """Test description."""
    # Arrange
    executor = CentralizedExecutor(...)
    
    # Act
    result = await executor.execute_workflow(...)
    
    # Assert
    assert result.status == "COMPLETED"
```

### Best Practices
1. Use descriptive test names
2. Follow Arrange-Act-Assert pattern
3. Use fixtures for common setup
4. Mock external dependencies
5. Test both success and failure cases
6. Include edge cases
7. Add docstrings explaining what's being tested

## Test Data

Test workflows and data are located in:
- `examples/` - Example workflow definitions
- Test fixtures within test files

## Continuous Integration

Tests are run automatically on:
- Pull requests
- Commits to main branch
- Scheduled nightly builds

## Troubleshooting

### Tests failing locally
1. Ensure all services are running
2. Check environment variables
3. Clear test database: `docker exec postgres psql -U workflow_user -d workflow_db -c "TRUNCATE workflow_runs, step_executions CASCADE;"`
4. Restart services: `docker-compose restart`

### Mock agents not responding
```bash
docker-compose -f docker-compose.test.yml logs
docker-compose -f docker-compose.test.yml restart
```

## Documentation

For more testing information, see:
- [Testing Architecture](../docs/testing/TESTING_ARCHITECTURE.md)
- [Manual Testing Guide](../docs/testing/MANUAL_TESTING_GUIDE.md)
- [Circuit Breaker Testing](../docs/testing/CIRCUIT_BREAKER_TESTING_GUIDE.md)
