#!/bin/sh
set -e

echo "Running migrations..."
alembic upgrade head

echo "Starting server..."
if [ "$ENV" = "production" ]; then
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
else
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
