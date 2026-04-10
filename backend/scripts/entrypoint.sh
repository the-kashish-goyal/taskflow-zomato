#!/bin/bash
set -e

echo "Running database migrations..."
cd /app
alembic upgrade head

echo "Seeding database..."
python scripts/seed.py

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
