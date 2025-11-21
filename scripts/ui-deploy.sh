#!/bin/bash

# Deployment script for Workflow UI

set -e

echo "🚀 Starting deployment..."

# Load environment variables
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found, using defaults"
fi

# Build mode (default: production)
BUILD_MODE=${1:-production}

echo "🏗️  Building for $BUILD_MODE..."

if [ "$BUILD_MODE" = "development" ]; then
    # Development build
    npm run build
else
    # Production build with Docker
    echo "🐳 Building Docker image..."
    docker build -t workflow-ui:latest .
    
    echo "🎯 Stopping existing container..."
    docker-compose down || true
    
    echo "🚀 Starting new container..."
    docker-compose up -d
    
    echo "⏳ Waiting for container to be healthy..."
    sleep 5
    
    # Check health
    if docker-compose ps | grep -q "healthy"; then
        echo "✅ Deployment successful!"
        echo "🌐 Application is running at http://localhost:3000"
    else
        echo "❌ Deployment failed - container is not healthy"
        docker-compose logs
        exit 1
    fi
fi

echo "✨ Deployment complete!"
