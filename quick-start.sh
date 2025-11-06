#!/bin/bash

# Quick Start Script for Centralized Executor Testing
# This script automates the setup and execution of a test workflow

set -e  # Exit on error

echo "=========================================="
echo "Centralized Executor - Quick Start"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Function to check if a service is ready
wait_for_service() {
    local service=$1
    local check_command=$2
    local max_attempts=30
    local attempt=0
    
    print_info "Waiting for $service to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if eval "$check_command" &> /dev/null; then
            print_success "$service is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_error "$service failed to start"
    return 1
}

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi
print_success "Docker is installed"

# Check for docker compose (V2) or docker-compose (V1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    print_success "Docker Compose V2 is installed"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    print_success "Docker Compose V1 is installed"
else
    print_error "Docker Compose is not installed"
    exit 1
fi
echo ""

# Step 2: Create .env file if it doesn't exist
echo "Step 2: Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_success "Created .env file from .env.example"
else
    print_info ".env file already exists"
fi
echo ""

# Step 3: Start infrastructure services
echo "Step 3: Starting infrastructure services (Kafka, PostgreSQL)..."
$DOCKER_COMPOSE up -d zookeeper kafka postgres
print_success "Infrastructure services started"
echo ""

# Wait for services to be ready
wait_for_service "Kafka" "docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list"
wait_for_service "PostgreSQL" "docker exec postgres pg_isready -U workflow_user"
echo ""

# Step 4: Start test services (mock agents)
echo "Step 4: Starting test services (mock agents)..."
$DOCKER_COMPOSE -f docker-compose.test.yml up -d
print_success "Test services started"
echo ""

# Wait for agents to be ready
sleep 5
wait_for_service "ResearchAgent" "curl -s http://localhost:8081/health"
wait_for_service "WriterAgent" "curl -s http://localhost:8082/health"
wait_for_service "Agent Registry" "curl -s http://localhost:8080/health"
echo ""

# Step 5: Start the HTTP-Kafka Bridge
echo "Step 5: Starting HTTP-Kafka Bridge..."
$DOCKER_COMPOSE --profile bridge up -d
print_success "Bridge started"
sleep 3
echo ""

# Step 6: Run a test workflow
echo "Step 6: Running test workflow..."
echo ""

# Generate unique run ID
RUN_ID="quickstart-test-$(date +%s)"
print_info "Run ID: $RUN_ID"

# Load workflow and input
WORKFLOW_PLAN=$(cat examples/sample_workflow.json)
WORKFLOW_INPUT=$(cat examples/sample_workflow_input.json)

print_info "Workflow: research-and-write (2 steps)"
print_info "Input: $(cat examples/sample_workflow_input.json | tr -d '\n')"
echo ""

print_info "Executing workflow..."
echo "=========================================="

# Run the executor
$DOCKER_COMPOSE run --rm \
  -e RUN_ID="$RUN_ID" \
  -e WORKFLOW_PLAN="$WORKFLOW_PLAN" \
  -e WORKFLOW_INPUT="$WORKFLOW_INPUT" \
  -e KAFKA_BROKERS=kafka:29092 \
  -e DATABASE_URL=postgresql://workflow_user:workflow_pass@postgres:5432/workflow_db \
  -e AGENT_REGISTRY_URL=http://agent-registry:8080 \
  -e LOG_LEVEL=INFO \
  -e LOG_FORMAT=text \
  executor

echo "=========================================="
echo ""

# Step 7: Verify results
echo "Step 7: Verifying results in database..."
echo ""

# Query workflow status
print_info "Workflow Status:"
docker exec postgres psql -U workflow_user -d workflow_db -c \
  "SELECT run_id, workflow_id, status, created_at, completed_at FROM workflow_runs WHERE run_id = '$RUN_ID';" \
  2>/dev/null || print_warning "Could not query database"

echo ""
print_info "Step Executions:"
docker exec postgres psql -U workflow_user -d workflow_db -c \
  "SELECT step_id, agent_name, status, started_at, completed_at FROM step_executions WHERE run_id = '$RUN_ID' ORDER BY started_at;" \
  2>/dev/null || print_warning "Could not query database"

echo ""
echo "=========================================="
echo "Quick Start Complete!"
echo "=========================================="
echo ""
print_success "Workflow executed successfully!"
echo ""
print_info "Next steps:"
echo "  1. View logs: $DOCKER_COMPOSE logs bridge"
echo "  2. Run another workflow: export RUN_ID=\"test-\$(date +%s)\" && ./quick-start.sh"
echo "  3. See MANUAL_TESTING_GUIDE.md for more testing scenarios"
echo "  4. Stop services: ./cleanup.sh"
echo ""
print_info "Your RUN_ID: $RUN_ID"
echo ""
