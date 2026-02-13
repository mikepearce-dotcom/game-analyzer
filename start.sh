#!/bin/bash
# Railway startup script for Sentient Tracker

# Exit on any error
set -e

# Check required environment variables
if [ -z "$MONGO_URL" ]; then
  echo "ERROR: MONGO_URL not set"
  exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
  echo "ERROR: OPENAI_API_KEY not set"
  exit 1
fi

if [ -z "$DB_NAME" ]; then
  export DB_NAME="sentient_tracker"
  echo "DB_NAME not set, using default: sentient_tracker"
fi

if [ -z "$CORS_ORIGINS" ]; then
  export CORS_ORIGINS="*"
  echo "CORS_ORIGINS not set, allowing all origins (use carefully in production)"
fi

echo "✓ All required environment variables are set"
echo "✓ Starting Sentient Tracker backend..."

# Start the application
cd /app/backend
exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
