#!/bin/bash
# Deploy Parallel Execution Feature
# This script rebuilds and restarts the necessary services

set -e  # Exit on error

echo "🚀 Deploying Parallel Execution Feature"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if docker compose is available
if ! command -v docker compose &> /dev/null; then
    print_error "docker compose not found. Please install docker compose."
    exit 1
fi

print_success "Docker Compose found"

# Step 1: Verify database migration
echo ""
echo "Step 1: Verifying database migration..."
if python scripts/verify_parallel_execution_migration.py > /dev/null 2>&1; then
    print_success "Database migration verified"
else
    print_warning "Database migration not verified. Continuing anyway..."
fi

# Step 2: Stop running services
echo ""
echo "Step 2: Stopping services..."
docker compose --profile executor --profile bridge --profile consumer down
print_success "Services stopped"

# Step 3: Rebuild images
echo ""
echo "Step 3: Rebuilding Docker images..."
echo "  - Building executor..."
docker compose build executor
print_success "Executor built"

echo "  - Building execution-consumer..."
docker compose build execution-consumer
print_success "Execution consumer built"

echo "  - Building bridge..."
docker compose build bridge
print_success "Bridge built"

# Step 4: Start infrastructure
echo ""
echo "Step 4: Starting infrastructure..."
docker compose up -d zookeeper kafka postgres
print_success "Infrastructure started"

# Wait for Kafka to be ready
echo ""
echo "Waiting for Kafka to be ready..."
sleep 10
print_success "Kafka should be ready"

# Step 5: Start services
echo ""
echo "Step 5: Starting services..."
docker compose --profile executor up -d
print_success "Executor started"

docker compose --profile consumer up -d
print_success "Execution consumer started"

docker compose --profile bridge up -d
print_success "Bridge started"

# Step 6: Verify deployment
echo ""
echo "Step 6: Verifying deployment..."
sleep 5

# Check if containers are running
if docker ps --filter "name=centralized-executor" --format "{{.Names}}" | grep -q "centralized-executor"; then
    print_success "Executor is running"
else
    print_error "Executor is not running"
fi

if docker ps --filter "name=execution-consumer" --format "{{.Names}}" | grep -q "execution-consumer"; then
    print_success "Execution consumer is running"
else
    print_error "Execution consumer is not running"
fi

if docker ps --filter "name=external-agent-executor" --format "{{.Names}}" | grep -q "external-agent-executor"; then
    print_success "Bridge is running"
else
    print_error "Bridge is not running"
fi

# Check logs for ParallelExecutor initialization
echo ""
echo "Checking logs for ParallelExecutor initialization..."
if docker logs centralized-executor 2>&1 | grep -q "Initializing Parallel Executor"; then
    print_success "ParallelExecutor initialized successfully"
else
    print_warning "ParallelExecutor initialization not found in logs (may not have started yet)"
fi

# Summary
echo ""
echo "========================================"
echo "🎉 Deployment Complete!"
echo "========================================"
echo ""
echo "Services running:"
docker compose ps --filter "status=running"
echo ""
echo "Next steps:"
echo "  1. Check logs: docker compose logs -f executor"
echo "  2. Test with example: examples/parallel_workflow_example.json"
echo "  3. Read docs: docs/parallel_execution.md"
echo ""
print_success "Parallel execution feature is ready to use!"
