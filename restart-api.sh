#!/bin/bash

# Script to restart the API service with updated schema
# This rebuilds the Docker image and restarts the container

set -e

echo "🔄 Restarting Workflow Management API..."
echo ""

# Stop the API service
echo "📦 Stopping API service..."
docker compose --profile api down

# Rebuild the API image (no cache to ensure fresh build)
echo "🔨 Rebuilding API image (no cache)..."
docker compose build --no-cache api

# Start the API service
echo "🚀 Starting API service..."
docker compose --profile api up -d

# Wait for API to be healthy
echo "⏳ Waiting for API to be healthy..."
sleep 5

# Check API health
echo "🏥 Checking API health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is healthy and ready!"
        echo ""
        echo "📊 API Status:"
        docker compose ps api
        echo ""
        echo "📝 API Logs (last 20 lines):"
        docker compose logs --tail=20 api
        echo ""
        echo "✨ API successfully restarted with updated schema!"
        echo "🌐 API URL: http://localhost:8000"
        echo "📚 API Docs: http://localhost:8000/docs"
        exit 0
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

echo "❌ API failed to become healthy within 60 seconds"
echo "📝 API Logs:"
docker compose logs api
exit 1
