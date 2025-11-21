#!/bin/bash

# Workflow Orchestrator - Quick Start Script

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Workflow Orchestrator - Quick Start ===${NC}\n"

# Function to display menu
show_menu() {
    echo "Select deployment mode:"
    echo "1) Full Stack (API + Consumer + UI)"
    echo "2) API + UI (Development)"
    echo "3) Core Infrastructure Only"
    echo "4) Full Stack + Test Agents"
    echo "5) Production Mode"
    echo "6) Rebuild Without Cache"
    echo "7) Stop All Services"
    echo "8) View Logs"
    echo "9) Exit"
    echo ""
}

# Function to start full stack
start_full_stack() {
    echo -e "${GREEN}Starting Full Stack...${NC}"
    docker compose --profile api --profile consumer --profile ui up -d
    show_access_points
}

# Function to start API + UI
start_api_ui() {
    echo -e "${GREEN}Starting API + UI...${NC}"
    docker compose --profile api --profile ui up -d
    show_access_points
}

# Function to start core only
start_core() {
    echo -e "${GREEN}Starting Core Infrastructure...${NC}"
    docker compose up -d
    echo -e "${GREEN}Core services started (Kafka, Postgres, Zookeeper)${NC}"
}

# Function to start with test agents
start_with_tests() {
    echo -e "${GREEN}Starting Full Stack with Test Agents...${NC}"
    docker compose --profile api --profile consumer --profile test up -d
    show_access_points
    echo -e "${YELLOW}Test Agents:${NC}"
    echo "  - Mock Agent Registry: http://localhost:8080"
    echo "  - Research Agent: http://localhost:8081"
    echo "  - Writer Agent: http://localhost:8082"
}

# Function to start production
start_production() {
    echo -e "${GREEN}Starting Production Mode...${NC}"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile api --profile consumer --profile ui up -d
    show_access_points
}

# Function to rebuild without cache
rebuild_no_cache() {
    echo -e "${YELLOW}Select service to rebuild:${NC}"
    echo "1) API"
    echo "2) UI"
    echo "3) Everything"
    read -p "Enter choice: " rebuild_choice
    
    case $rebuild_choice in
        1)
            echo -e "${GREEN}Rebuilding API...${NC}"
            docker compose stop api
            docker compose rm -f api
            docker compose build --no-cache api
            docker compose --profile api up -d
            ;;
        2)
            echo -e "${GREEN}Rebuilding UI...${NC}"
            docker compose stop workflow-ui
            docker compose rm -f workflow-ui
            docker compose build --no-cache workflow-ui
            docker compose --profile ui up -d
            ;;
        3)
            echo -e "${GREEN}Rebuilding Everything...${NC}"
            docker compose down -v
            docker compose build --no-cache
            docker compose --profile api --profile consumer --profile ui up -d
            ;;
        *)
            echo -e "${YELLOW}Invalid choice${NC}"
            ;;
    esac
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}Stopping all services...${NC}"
    docker compose down
    echo -e "${GREEN}All services stopped${NC}"
}

# Function to view logs
view_logs() {
    echo -e "${YELLOW}Select service logs to view:${NC}"
    echo "1) All services"
    echo "2) API"
    echo "3) UI"
    echo "4) Consumer"
    echo "5) Kafka"
    read -p "Enter choice: " log_choice
    
    case $log_choice in
        1) docker compose logs -f ;;
        2) docker compose logs -f api ;;
        3) docker compose logs -f workflow-ui ;;
        4) docker compose logs -f execution-consumer ;;
        5) docker compose logs -f kafka ;;
        *) echo -e "${YELLOW}Invalid choice${NC}" ;;
    esac
}

# Function to show access points
show_access_points() {
    echo -e "\n${GREEN}Services started successfully!${NC}"
    echo -e "${BLUE}Access Points:${NC}"
    echo "  - API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - UI: http://localhost:3000"
    echo "  - Postgres: localhost:5432"
    echo "  - Kafka: localhost:9092"
    echo ""
}

# Main loop
while true; do
    show_menu
    read -p "Enter choice: " choice
    echo ""
    
    case $choice in
        1) start_full_stack ;;
        2) start_api_ui ;;
        3) start_core ;;
        4) start_with_tests ;;
        5) start_production ;;
        6) rebuild_no_cache ;;
        7) stop_services ;;
        8) view_logs ;;
        9) echo "Goodbye!"; exit 0 ;;
        *) echo -e "${YELLOW}Invalid choice. Please try again.${NC}\n" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    echo ""
done
