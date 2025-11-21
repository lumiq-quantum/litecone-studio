#!/bin/bash

# Simple Circuit Breaker Test
# Tests just the Python circuit breaker logic without full infrastructure

echo "=========================================="
echo "Simple Circuit Breaker Test"
echo "=========================================="
echo ""

# Check if Python test exists
if [ ! -f "test_circuit_breaker.py" ]; then
    echo "Error: test_circuit_breaker.py not found"
    echo "This file should have been created during implementation"
    exit 1
fi

# Check if redis module is installed
if ! python -c "import redis" 2>/dev/null; then
    echo "Installing redis module..."
    pip install redis==5.0.1
fi

# Run the test
echo "Running circuit breaker unit tests..."
echo ""

python test_circuit_breaker.py

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "=========================================="
    echo "✓ All tests passed!"
    echo "=========================================="
    echo ""
    echo "The circuit breaker logic is working correctly."
    echo ""
    echo "Next steps:"
    echo "  1. Start services: docker compose up -d redis kafka postgres bridge"
    echo "  2. Run full test: ./test_circuit_breaker_live.sh"
else
    echo "=========================================="
    echo "✗ Tests failed"
    echo "=========================================="
fi

exit $exit_code
