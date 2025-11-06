#!/bin/bash

# Cleanup Script for Centralized Executor
# Stops all services and optionally removes volumes

set -e

echo "=========================================="
echo "Centralized Executor - Cleanup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Detect docker compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    print_error "Docker Compose is not installed"
    exit 1
fi

# Parse arguments
REMOVE_VOLUMES=false
if [ "$1" == "--volumes" ] || [ "$1" == "-v" ]; then
    REMOVE_VOLUMES=true
    print_warning "Will remove volumes (database data will be deleted)"
fi

echo ""
print_info "Stopping services..."

# Stop bridge
print_info "Stopping bridge..."
$DOCKER_COMPOSE --profile bridge down 2>/dev/null || true
print_success "Bridge stopped"

# Stop test services
print_info "Stopping test services..."
$DOCKER_COMPOSE -f docker-compose.test.yml down 2>/dev/null || true
print_success "Test services stopped"

# Stop infrastructure
print_info "Stopping infrastructure services..."
if [ "$REMOVE_VOLUMES" = true ]; then
    $DOCKER_COMPOSE down -v
    print_success "Infrastructure stopped and volumes removed"
else
    $DOCKER_COMPOSE down
    print_success "Infrastructure stopped (volumes preserved)"
fi

# Remove orphaned containers
print_info "Removing orphaned containers..."
$DOCKER_COMPOSE down --remove-orphans 2>/dev/null || true
$DOCKER_COMPOSE -f docker-compose.test.yml down --remove-orphans 2>/dev/null || true

echo ""
echo "=========================================="
print_success "Cleanup complete!"
echo "=========================================="
echo ""

if [ "$REMOVE_VOLUMES" = false ]; then
    print_info "Database data preserved. To remove volumes, run:"
    echo "  ./cleanup.sh --volumes"
fi

echo ""
print_info "To start again, run:"
echo "  ./quick-start.sh"
echo ""
