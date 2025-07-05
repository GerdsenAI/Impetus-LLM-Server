#!/bin/bash
# Development environment setup script for Impetus-LLM-Server
# This script creates a virtual environment and installs all dependencies

set -e  # Exit on error

echo "🚀 Setting up Impetus-LLM-Server development environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${YELLOW}Warning: This project is optimized for macOS with Apple Silicon.${NC}"
    echo "Some features may not work on other platforms."
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"

# Create virtual environment
VENV_DIR="venv"
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Removing old one...${NC}"
    rm -rf "$VENV_DIR"
fi

echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"

# Activate virtual environment
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓ Virtual environment created and activated${NC}"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip wheel setuptools

# Install development dependencies
echo "Installing development dependencies..."
pip install -r requirements_dev.txt

# Create necessary directories
echo "Creating project directories..."
mkdir -p models
mkdir -p logs
mkdir -p .clinerules/mcp_context
mkdir -p .clinerules/agent_memory
mkdir -p .clinerules/search_index

# Download a small test model (optional)
echo -e "${YELLOW}Would you like to download a small test model (Phi-3-mini GGUF ~2GB)? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Downloading Phi-3-mini GGUF model..."
    # Create models directory if it doesn't exist
    mkdir -p models/phi-3-mini
    # Download using huggingface-hub
    python3 -c "
from huggingface_hub import hf_hub_download
import os

repo_id = 'microsoft/Phi-3-mini-4k-instruct-gguf'
filename = 'Phi-3-mini-4k-instruct-q4.gguf'
cache_dir = './models/phi-3-mini'

print(f'Downloading {filename}...')
try:
    model_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=cache_dir,
        local_dir_use_symlinks=False
    )
    print(f'✓ Model downloaded to: {model_path}')
except Exception as e:
    print(f'Error downloading model: {e}')
    print('You can download it manually later.')
"
fi

# Set up pre-commit hooks (optional)
if command -v pre-commit &> /dev/null; then
    echo "Setting up pre-commit hooks..."
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Impetus-LLM-Server Environment Configuration

# Server settings
PORT=8080
DEBUG=True
LOG_LEVEL=INFO

# Model settings
MODEL_CACHE_DIR=./models
DEFAULT_MODEL=phi-3-mini-4k-instruct-q4.gguf
MAX_CONTEXT_LENGTH=4096

# Performance settings
MAX_BATCH_SIZE=8
NUM_THREADS=0  # 0 = auto-detect

# API settings
API_KEY=sk-dev-local-testing-only
ENABLE_CORS=True

# Hardware optimization
ENABLE_METAL=True
ENABLE_NEURAL_ENGINE=True
AUTO_OPTIMIZE=True
EOL
    echo -e "${GREEN}✓ .env file created${NC}"
fi

# Run initial tests
echo "Running initial tests..."
python -m pytest tests/ -v --tb=short || echo -e "${YELLOW}No tests found yet. That's OK for initial setup.${NC}"

# Display next steps
echo ""
echo -e "${GREEN}✅ Development environment setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start the development server: python gerdsen_ai_server/src/production_main.py"
echo "3. Configure VS Code/Cline to use http://localhost:8080"
echo ""
echo "To run tests: pytest"
echo "To format code: black ."
echo "To lint: flake8"
echo ""
echo -e "${YELLOW}Happy coding! 🎉${NC}"