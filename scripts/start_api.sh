#!/bin/bash

# Start the Workflow Management API server

echo "🚀 Starting Workflow Management API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env.api exists
if [ ! -f ".env.api" ]; then
    echo "❌ .env.api file not found"
    exit 1
fi

# Load environment variables
export $(cat .env.api | grep -v '^#' | xargs)

echo "📝 Configuration:"
echo "  - API URL: http://${API_HOST}:${API_PORT}"
echo "  - CORS Origins: ${CORS_ORIGINS}"
echo "  - Database: ${DATABASE_URL}"

# Start the API server
echo ""
echo "🌐 Starting server..."
python -m uvicorn api.main:app --host ${API_HOST} --port ${API_PORT} --reload

