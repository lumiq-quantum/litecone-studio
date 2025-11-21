#!/bin/bash

# Quick restart of API service (without rebuilding)
# Use this for Python code changes that don't require dependency updates

set -e

echo "⚡ Quick restart of Workflow Management API..."
echo ""

# Restart the API container
echo "🔄 Restarting API container..."
docker compose restart api

# Wait for API to be healthy
echo "⏳ Waiting for API to be healthy..."
sleep 3

# Check API health
echo "🏥 Checking API health..."
for i in {1..20}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is healthy and ready!"
        echo ""
        echo "📊 API Status:"
        docker compose ps api
        echo ""
        echo "✨ API successfully restarted!"
        echo "🌐 API URL: http://localhost:8000"
        exit 0
    fi
    echo "   Waiting... ($i/20)"
    sleep 2
done

echo "❌ API failed to become healthy within 40 seconds"
echo "📝 API Logs:"
docker compose logs --tail=50 api
exit 1
