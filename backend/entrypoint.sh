#!/bin/bash
set -e

echo "🚀 Starting Cashback Optimization Engine Backend..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! pg_isready -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} > /dev/null 2>&1; do
    sleep 1
done
echo "✅ Database is ready!"

# Start the FastAPI application
# (Table creation and card import happen in FastAPI startup event)
echo "🌐 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
