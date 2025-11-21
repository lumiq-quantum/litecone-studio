#!/bin/bash

# Step-by-step test script for debugging
# Run each step manually to identify issues

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "ℹ $1"; }

# Detect docker compose
if docker compose version &> /dev/null; then
    DC="docker compose"
else
    DC="docker-compose"
fi

echo "Using: $DC"
echo ""

# Test 1: Check if infrastructure is running
echo "=== Test 1: Check Infrastructure ==="
print_info "Checking Kafka..."
if docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; then
    print_success "Kafka is running"
else
    print_error "Kafka is not running"
    print_info "Starting infrastructure..."
    $DC up -d zookeeper kafka postgres
    sleep 10
fi

print_info "Checking PostgreSQL..."
if docker exec postgres pg_isready -U workflow_user &> /dev/null; then
    print_success "PostgreSQL is running"
else
    print_error "PostgreSQL is not running"
fi
echo ""

# Test 2: Try to start test services
echo "=== Test 2: Start Test Services ==="
print_info "Starting mock agents..."
$DC -f docker-compose.test.yml up -d 2>&1 | head -20

echo ""
print_info "Waiting for services to start..."
sleep 5

# Test 3: Check if agents are responding
echo ""
echo "=== Test 3: Check Agents ==="
print_info "Testing ResearchAgent..."
if curl -s http://localhost:8081/health &> /dev/null; then
    print_success "ResearchAgent is responding"
    curl -s http://localhost:8081/health | jq . || echo ""
else
    print_error "ResearchAgent is not responding"
    print_info "Checking logs..."
    $DC -f docker-compose.test.yml logs research-agent | tail -20
fi

echo ""
print_info "Testing WriterAgent..."
if curl -s http://localhost:8082/health &> /dev/null; then
    print_success "WriterAgent is responding"
    curl -s http://localhost:8082/health | jq . || echo ""
else
    print_error "WriterAgent is not responding"
    print_info "Checking logs..."
    $DC -f docker-compose.test.yml logs writer-agent | tail -20
fi

echo ""
print_info "Testing Agent Registry..."
if curl -s http://localhost:8080/health &> /dev/null; then
    print_success "Agent Registry is responding"
    curl -s http://localhost:8080/health | jq . || echo ""
else
    print_error "Agent Registry is not responding"
    print_info "Checking logs..."
    $DC -f docker-compose.test.yml logs agent-registry | tail -20
fi

# Test 4: Check running containers
echo ""
echo "=== Test 4: Running Containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "research-agent|writer-agent|agent-registry|kafka|postgres" || echo "No matching containers"

echo ""
echo "=== Summary ==="
print_info "If all tests passed, you can run: ./quick-start.sh"
print_info "If tests failed, check the logs above for errors"
