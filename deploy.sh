#!/bin/bash
set -e

echo "🚀 Deploying LiteCone Studio..."

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f docker-compose.prod.yml --env-file .env.images pull

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml --env-file .env.images down

# Start services
echo "▶️  Starting services..."
docker-compose -f docker-compose.prod.yml --env-file .env.images up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo "📊 Service status:"
docker-compose -f docker-compose.prod.yml --env-file .env.images ps

echo "✅ Deployment complete!"
echo ""
echo "🌐 Access the application:"
echo "   UI:  http://localhost:3000"
echo "   API: http://localhost:8000"
echo ""
echo "📝 View logs: docker-compose -f docker-compose.prod.yml --env-file .env.images logs -f"
