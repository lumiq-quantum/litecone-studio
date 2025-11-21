#!/bin/bash

# Script to fix multiple heads issue and rebuild API

set -e

echo "🔧 Fixing Multiple Heads Issue..."
echo ""

echo "📋 Migration chain will be:"
echo "   001 → 70b7d11bef31 → 002_conditional (head)"
echo ""

# Stop API
echo "1️⃣  Stopping API service..."
docker compose --profile api down

# Rebuild with fixed migration
echo ""
echo "2️⃣  Rebuilding API with corrected migration chain..."
docker compose build --no-cache api

# Start API
echo ""
echo "3️⃣  Starting API service..."
docker compose --profile api up -d

# Wait for readiness
echo ""
echo "4️⃣  Waiting for API to be ready..."
sleep 10

# Check health
echo ""
echo "5️⃣  Checking API health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ API failed to become healthy"
        docker compose logs --tail=50 api
        exit 1
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

# Check migration status
echo ""
echo "6️⃣  Checking migration status..."
docker compose exec -T api alembic current

echo ""
echo "✨ Migration chain fixed!"
echo ""
echo "📊 Container Status:"
docker compose ps api

echo ""
echo "🧪 Now test the conditional workflow:"
echo "curl -X POST http://localhost:8000/api/v1/workflows \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d @examples/conditional_workflow_example.json"
