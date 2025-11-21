#!/bin/bash

# Script to wait for API container to be ready and then run migrations

set -e

echo "⏳ Waiting for API container to be ready..."
echo ""

# Wait for container to be running (not restarting)
for i in {1..30}; do
    STATUS=$(docker compose ps api --format json 2>/dev/null | grep -o '"State":"[^"]*"' | cut -d'"' -f4 || echo "not_found")
    
    if [ "$STATUS" = "running" ]; then
        echo "✅ API container is running!"
        break
    elif [ "$STATUS" = "restarting" ]; then
        echo "   Container is restarting... ($i/30)"
        sleep 2
    else
        echo "   Waiting for container... ($i/30)"
        sleep 2
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ Container did not become ready in time"
        echo ""
        echo "📝 Container status:"
        docker compose ps api
        echo ""
        echo "📝 Recent logs:"
        docker compose logs --tail=50 api
        exit 1
    fi
done

# Give it a few more seconds to fully initialize
echo "⏳ Waiting for API to fully initialize..."
sleep 5

# Check if API is healthy
echo "🏥 Checking API health..."
for i in {1..20}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is healthy!"
        break
    fi
    echo "   Waiting for health check... ($i/20)"
    sleep 2
done

# Run migrations
echo ""
echo "🗄️  Running database migrations..."
docker compose exec -T api alembic upgrade head

# Check migration status
echo ""
echo "✅ Checking migration status..."
docker compose exec -T api alembic current

echo ""
echo "✨ Done! API is ready and migrations are applied."
echo ""
echo "🧪 Test the conditional workflow:"
echo "curl -X POST http://localhost:8000/api/v1/workflows \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d @examples/conditional_workflow_example.json"
