#!/bin/bash

# Script to run database migrations
# This applies all pending migrations to the database

set -e

echo "🗄️  Running Database Migrations..."
echo ""

# Check if API container is running
if ! docker compose ps api | grep -q "Up"; then
    echo "⚠️  API container is not running. Starting it..."
    docker compose --profile api up -d
    sleep 5
fi

# Run migrations
echo "📦 Applying migrations..."
docker compose exec api alembic upgrade head

# Check migration status
echo ""
echo "✅ Checking migration status..."
docker compose exec api alembic current

echo ""
echo "✨ Migrations completed successfully!"
echo ""
echo "📊 Current database schema version:"
docker compose exec api alembic current -v
