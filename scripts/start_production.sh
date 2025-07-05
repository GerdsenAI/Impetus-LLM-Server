#!/bin/bash
# Production startup script for Impetus LLM Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Impetus LLM Server (Production)${NC}"

# Check if we're in the right directory
if [ ! -f "gunicorn_config.py" ]; then
    echo -e "${RED}Error: Not in the Impetus-LLM-Server directory${NC}"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    echo -e "${GREEN}Loading environment from .env${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}Warning: No .env file found, using defaults${NC}"
fi

# Create necessary directories
echo -e "${GREEN}Creating directories...${NC}"
mkdir -p logs
mkdir -p ~/Models

# Check Python dependencies
echo -e "${GREEN}Checking dependencies...${NC}"
if ! python -c "import gunicorn" 2>/dev/null; then
    echo -e "${RED}Error: Gunicorn not installed. Run: pip install gunicorn${NC}"
    exit 1
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}:${PWD}/gerdsen_ai_server/src"

# Determine which server module to use
if [ "$USE_ENHANCED_SERVER" = "true" ]; then
    SERVER_MODULE="gerdsen_ai_server.src.production_main_enhanced:app"
    echo -e "${GREEN}Using enhanced production server with ML components${NC}"
else
    SERVER_MODULE="gerdsen_ai_server.src.production_main:app"
    echo -e "${GREEN}Using standard production server${NC}"
fi

# Start Gunicorn
echo -e "${GREEN}Starting Gunicorn...${NC}"
echo -e "Server: http://${SERVER_HOST:-0.0.0.0}:${SERVER_PORT:-8080}"

if [ "$FLASK_ENV" = "development" ]; then
    echo -e "${YELLOW}Running in development mode with auto-reload${NC}"
fi

# Run Gunicorn with configuration
exec gunicorn \
    --config gunicorn_config.py \
    "$SERVER_MODULE"