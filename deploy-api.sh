#!/bin/bash

# Workflow Management API Deployment Script
# This script helps deploy the API in various environments

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_info "Prerequisites check passed ✓"
}

# Function to check environment file
check_env_file() {
    local env_file=$1
    
    if [ ! -f "$env_file" ]; then
        print_error "Environment file $env_file not found!"
        print_info "Creating from example..."
        
        if [ -f ".env.api.example" ]; then
            cp .env.api.example "$env_file"
            print_warning "Created $env_file from example. Please review and update the values!"
            return 1
        else
            print_error ".env.api.example not found!"
            exit 1
        fi
    fi
    
    return 0
}

# Function to validate environment variables
validate_env() {
    local env_file=$1
    print_info "Validating environment variables in $env_file..."
    
    # Source the env file
    set -a
    source "$env_file"
    set +a
    
    local errors=0
    
    # Check required variables
    if [ -z "$DATABASE_URL" ]; then
        print_error "DATABASE_URL is not set"
        errors=$((errors + 1))
    fi
    
    if [ -z "$KAFKA_BROKERS" ]; then
        print_error "KAFKA_BROKERS is not set"
        errors=$((errors + 1))
    fi
    
    # Check production security
    if [ "$ENVIRONMENT" = "production" ]; then
        if [ "$JWT_SECRET" = "dev-secret-key-change-in-production" ]; then
            print_error "JWT_SECRET is still using default value! Change it in production!"
            errors=$((errors + 1))
        fi
        
        if [ "$API_RELOAD" = "true" ]; then
            print_warning "API_RELOAD should be false in production"
        fi
        
        if [[ "$CORS_ORIGINS" == *"*"* ]]; then
            print_error "CORS_ORIGINS should not use wildcard (*) in production"
            errors=$((errors + 1))
        fi
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "Environment validation failed with $errors error(s)"
        return 1
    fi
    
    print_info "Environment validation passed ✓"
    return 0
}

# Function to run database migrations
run_migrations() {
    print_info "Running database migrations..."
    
    docker-compose exec -T api alembic upgrade head
    
    if [ $? -eq 0 ]; then
        print_info "Migrations completed successfully ✓"
    else
        print_error "Migration failed!"
        return 1
    fi
}

# Function to check health
check_health() {
    print_info "Checking API health..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
            print_info "API is healthy ✓"
            return 0
        fi
        
        print_info "Waiting for API to be ready... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "API health check failed after $max_attempts attempts"
    return 1
}

# Function to deploy development
deploy_dev() {
    print_info "Deploying in DEVELOPMENT mode..."
    
    check_env_file ".env.api"
    
    print_info "Starting services..."
    docker-compose --profile api up -d
    
    print_info "Waiting for services to start..."
    sleep 10
    
    run_migrations
    check_health
    
    print_info "Development deployment complete! ✓"
    print_info "API available at: http://localhost:8000"
    print_info "Swagger UI: http://localhost:8000/docs"
    print_info "ReDoc: http://localhost:8000/redoc"
}

# Function to deploy production
deploy_prod() {
    print_info "Deploying in PRODUCTION mode..."
    
    check_env_file ".env.api.production"
    
    if ! validate_env ".env.api.production"; then
        print_error "Environment validation failed. Please fix the issues before deploying."
        exit 1
    fi
    
    print_info "Building production images..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build api
    
    print_info "Starting services..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile api up -d
    
    print_info "Waiting for services to start..."
    sleep 15
    
    run_migrations
    check_health
    
    print_info "Production deployment complete! ✓"
    print_info "API available at: http://localhost:8000"
}

# Function to stop services
stop_services() {
    print_info "Stopping API services..."
    docker-compose --profile api down
    print_info "Services stopped ✓"
}

# Function to view logs
view_logs() {
    print_info "Viewing API logs (Ctrl+C to exit)..."
    docker-compose logs -f api
}

# Function to show status
show_status() {
    print_info "Service Status:"
    docker-compose ps api
    
    echo ""
    print_info "Health Check:"
    curl -s http://localhost:8000/health | python -m json.tool || print_error "API not responding"
    
    echo ""
    print_info "Readiness Check:"
    curl -s http://localhost:8000/health/ready | python -m json.tool || print_error "API not ready"
}

# Main menu
show_menu() {
    echo ""
    echo "=========================================="
    echo "  Workflow Management API Deployment"
    echo "=========================================="
    echo "1. Deploy Development"
    echo "2. Deploy Production"
    echo "3. Stop Services"
    echo "4. View Logs"
    echo "5. Show Status"
    echo "6. Run Migrations"
    echo "7. Check Health"
    echo "8. Exit"
    echo "=========================================="
}

# Main script
main() {
    check_prerequisites
    
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            show_menu
            read -p "Select an option: " choice
            
            case $choice in
                1)
                    deploy_dev
                    ;;
                2)
                    deploy_prod
                    ;;
                3)
                    stop_services
                    ;;
                4)
                    view_logs
                    ;;
                5)
                    show_status
                    ;;
                6)
                    run_migrations
                    ;;
                7)
                    check_health
                    ;;
                8)
                    print_info "Exiting..."
                    exit 0
                    ;;
                *)
                    print_error "Invalid option"
                    ;;
            esac
            
            echo ""
            read -p "Press Enter to continue..."
        done
    else
        # Command line mode
        case $1 in
            dev|development)
                deploy_dev
                ;;
            prod|production)
                deploy_prod
                ;;
            stop)
                stop_services
                ;;
            logs)
                view_logs
                ;;
            status)
                show_status
                ;;
            migrate)
                run_migrations
                ;;
            health)
                check_health
                ;;
            *)
                echo "Usage: $0 [dev|prod|stop|logs|status|migrate|health]"
                echo ""
                echo "Commands:"
                echo "  dev        - Deploy in development mode"
                echo "  prod       - Deploy in production mode"
                echo "  stop       - Stop all services"
                echo "  logs       - View API logs"
                echo "  status     - Show service status"
                echo "  migrate    - Run database migrations"
                echo "  health     - Check API health"
                echo ""
                echo "Run without arguments for interactive mode"
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@"
