#!/bin/bash

# Script to rebuild API with fixed migration and apply it

set -e

echo "🔧 Fixing Migration and Rebuilding API..."
echo ""

# Stop the API service
echo "1️⃣  Stopping API service..."
docker compose --profile api down

# Rebuild the API image (no cache to ensure fresh build)
echo ""
echo "2️⃣  Rebuilding API image with fixed migration..."
docker compose build --no-cache api

# Start the API service
echo ""
echo "3️⃣  Starting API service..."
docker compose --profile api up -d

# Wait for API to be ready
echo ""
echo "4️⃣  Waiting for API to be ready..."
sleep 10

# Check if API is healthy
echo ""
echo "5️⃣  Checking API health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ API failed to become healthy"
        echo ""
        echo "📝 Checking logs..."
        docker compose logs --tail=50 api
        exit 1
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

# Check migration status
echo ""
echo "6️⃣  Checking migration status..."
docker compose exec -T api alembic current || echo "⚠️  Migration not yet applied"

echo ""
echo "✨ API rebuilt and running!"
echo ""
echo "📊 Container Status:"
docker compose ps api

echo ""
echo "🧪 Test the conditional workflow:"
echo "curl -X POST http://localhost:8000/api/v1/workflows \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d @examples/conditional_workflow_example.json"
