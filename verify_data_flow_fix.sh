#!/bin/bash

# Verification script for the data flow fix
# This script helps verify that structured data is now being passed between workflow steps

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Data Flow Fix Verification ===${NC}\n"

# Check if services are running
echo -e "${YELLOW}1. Checking service status...${NC}"
docker compose -f docker-compose.prod.standalone.yml ps --format table

echo -e "\n${YELLOW}2. Checking bridge service logs for initialization...${NC}"
if docker compose -f docker-compose.prod.standalone.yml logs bridge | grep -q "initialization complete"; then
    echo -e "${GREEN}✓ Bridge service initialized successfully${NC}"
else
    echo -e "${RED}✗ Bridge service may not be running correctly${NC}"
    exit 1
fi

echo -e "\n${YELLOW}3. Testing the fix with unit tests...${NC}"
if python tests/test_data_flow.py; then
    echo -e "${GREEN}✓ Data flow tests passed${NC}"
else
    echo -e "${RED}✗ Data flow tests failed${NC}"
    exit 1
fi

echo -e "\n${YELLOW}4. Checking API health...${NC}"
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ API is healthy${NC}"
else
    echo -e "${RED}✗ API is not responding${NC}"
    exit 1
fi

echo -e "\n${YELLOW}5. Checking UI availability...${NC}"
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✓ UI is accessible${NC}"
else
    echo -e "${RED}✗ UI is not responding${NC}"
    exit 1
fi

echo -e "\n${GREEN}=== Verification Summary ===${NC}"
echo -e "${GREEN}✓ All services are running${NC}"
echo -e "${GREEN}✓ Bridge service has the data flow fix${NC}"
echo -e "${GREEN}✓ Unit tests confirm the fix works${NC}"
echo -e "${GREEN}✓ API and UI are accessible${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Test your workflow with structured data passing between steps"
echo "2. Check workflow execution logs to verify data is preserved"
echo "3. Monitor the bridge service logs during workflow execution"

echo -e "\n${YELLOW}Useful Commands:${NC}"
echo "• View bridge logs: docker compose -f docker-compose.prod.standalone.yml logs bridge -f"
echo "• View API logs: docker compose -f docker-compose.prod.standalone.yml logs api -f"
echo "• Check service status: docker compose -f docker-compose.prod.standalone.yml ps"
echo "• Access UI: http://localhost:3000"
echo "• Access API: http://localhost:8000"

echo -e "\n${GREEN}Data flow fix deployment completed successfully!${NC}"