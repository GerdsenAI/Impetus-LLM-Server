#!/bin/bash
# Production startup script for Impetus LLM Server

# Set production environment
export IMPETUS_ENVIRONMENT=production

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    source ../.venv/bin/activate
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default values if not provided
export IMPETUS_HOST=${IMPETUS_HOST:-0.0.0.0}
export IMPETUS_PORT=${IMPETUS_PORT:-8080}
export IMPETUS_WORKERS=${IMPETUS_WORKERS:-auto}
export IMPETUS_LOG_LEVEL=${IMPETUS_LOG_LEVEL:-info}

# Calculate workers if set to auto
if [ "$IMPETUS_WORKERS" = "auto" ]; then
    # Get number of CPU cores
    CORES=$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)
    # Use half the cores, max 4 for ML workloads
    WORKERS=$((CORES / 2))
    if [ $WORKERS -gt 4 ]; then
        WORKERS=4
    fi
    if [ $WORKERS -lt 1 ]; then
        WORKERS=1
    fi
else
    WORKERS=$IMPETUS_WORKERS
fi

echo "Starting Impetus LLM Server in production mode..."
echo "Host: $IMPETUS_HOST"
echo "Port: $IMPETUS_PORT"
echo "Workers: $WORKERS"
echo "Log Level: $IMPETUS_LOG_LEVEL"

# Start Gunicorn with eventlet worker class for WebSocket support
exec gunicorn \
    --config gunicorn_config.py \
    --workers $WORKERS \
    --worker-class eventlet \
    --bind $IMPETUS_HOST:$IMPETUS_PORT \
    --log-level $IMPETUS_LOG_LEVEL \
    wsgi:application