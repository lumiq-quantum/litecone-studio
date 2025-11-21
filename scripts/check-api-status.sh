#!/bin/bash

# Quick script to check API status and provide next steps

echo "🔍 Checking API Status..."
echo ""

# Check container status
echo "📦 Container Status:"
docker compose ps api
echo ""

# Check if container is running
if docker compose ps api | grep -q "Up"; then
    echo "✅ Container is UP"
    
    # Check health
    echo ""
    echo "🏥 Health Check:"
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is HEALTHY"
        
        # Check migration status
        echo ""
        echo "🗄️  Migration Status:"
        docker compose exec -T api alembic current 2>/dev/null || echo "⚠️  Could not check migrations"
        
        echo ""
        echo "✨ API is ready! You can now:"
        echo "   1. Test conditional workflow:"
        echo "      curl -X POST http://localhost:8000/api/v1/workflows \\"
        echo "        -H 'Content-Type: application/json' \\"
        echo "        -d @examples/conditional_workflow_example.json"
        echo ""
        echo "   2. View API docs: http://localhost:8000/docs"
    else
        echo "⚠️  API is not responding to health checks"
        echo ""
        echo "📝 Recent logs:"
        docker compose logs --tail=20 api
    fi
    
elif docker compose ps api | grep -q "Restarting"; then
    echo "🔄 Container is RESTARTING"
    echo ""
    echo "This usually means there's an error. Checking logs..."
    echo ""
    echo "📝 Recent logs:"
    docker compose logs --tail=30 api
    echo ""
    echo "💡 Next steps:"
    echo "   1. Wait for restart to complete: watch docker compose ps api"
    echo "   2. Or check full logs: docker compose logs api"
    echo "   3. Or restart manually: docker compose restart api"
    
else
    echo "❌ Container is NOT running"
    echo ""
    echo "💡 Start the API:"
    echo "   docker compose --profile api up -d"
fi
