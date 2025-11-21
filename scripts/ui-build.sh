#!/bin/bash

# Build script for different environments

set -e

ENVIRONMENT=${1:-production}

echo "🏗️  Building for $ENVIRONMENT environment..."

# Set environment-specific variables
case $ENVIRONMENT in
  development)
    export VITE_API_URL=${VITE_API_URL:-http://localhost:8000/api/v1}
    export VITE_POLLING_INTERVAL=1000
    ;;
  staging)
    export VITE_API_URL=${VITE_API_URL:-https://staging-api.example.com/api/v1}
    export VITE_POLLING_INTERVAL=2000
    ;;
  production)
    export VITE_API_URL=${VITE_API_URL:-https://api.example.com/api/v1}
    export VITE_POLLING_INTERVAL=3000
    ;;
  *)
    echo "❌ Unknown environment: $ENVIRONMENT"
    echo "Usage: ./build.sh [development|staging|production]"
    exit 1
    ;;
esac

echo "📝 Environment variables:"
echo "  VITE_API_URL=$VITE_API_URL"
echo "  VITE_POLLING_INTERVAL=$VITE_POLLING_INTERVAL"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm ci
fi

# Run type check
echo "🔍 Running type check..."
npm run type-check

# Run linting
echo "🧹 Running linter..."
npm run lint

# Run tests
echo "🧪 Running tests..."
npm test

# Build the application
echo "🔨 Building application..."
npm run build

echo "✅ Build complete!"
echo "📦 Output directory: dist/"

# Show build size
if command -v du &> /dev/null; then
    BUILD_SIZE=$(du -sh dist/ | cut -f1)
    echo "📊 Build size: $BUILD_SIZE"
fi
