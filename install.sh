#!/bin/bash
#
# Impetus LLM Server - Installation Script
# 
# This script installs Impetus LLM Server on macOS (Apple Silicon)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/GerdsenAI/Impetus-LLM-Server.git"
INSTALL_DIR="$HOME/impetus-llm-server"
VENV_DIR="$INSTALL_DIR/venv"
DEFAULT_MODEL="mlx-community/Mistral-7B-Instruct-v0.3-4bit"

# Functions
print_header() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════╗"
    echo "║     Impetus LLM Server Installer         ║"
    echo "║   High-Performance LLM for Apple Silicon ║"
    echo "╚══════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_requirements() {
    echo -e "${YELLOW}Checking requirements...${NC}"
    
    # Check macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo -e "${RED}Error: This installer is for macOS only${NC}"
        exit 1
    fi
    
    # Check Apple Silicon
    if [[ $(uname -m) != "arm64" ]]; then
        echo -e "${RED}Error: This installer requires Apple Silicon (M1/M2/M3/M4)${NC}"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required${NC}"
        echo "Install with: brew install python@3.11"
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.11"
    if [[ $(echo "$PYTHON_VERSION < $REQUIRED_VERSION" | bc) -eq 1 ]]; then
        echo -e "${RED}Error: Python $REQUIRED_VERSION+ is required (found $PYTHON_VERSION)${NC}"
        echo "Install with: brew install python@3.11"
        exit 1
    fi
    
    # Check memory
    MEMORY_GB=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    if [[ $MEMORY_GB -lt 8 ]]; then
        echo -e "${YELLOW}Warning: System has ${MEMORY_GB}GB RAM. 8GB+ recommended for larger models${NC}"
        sleep 2
    fi
    
    # Check disk space
    DISK_FREE_GB=$(df -H / | awk 'NR==2 {print int($4)}')
    if [[ $DISK_FREE_GB -lt 10 ]]; then
        echo -e "${YELLOW}Warning: Only ${DISK_FREE_GB}GB free disk space. 10GB+ recommended${NC}"
        echo "Continue anyway? (y/n)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check for conflicting processes on port 8080
    if lsof -i :8080 &> /dev/null; then
        echo -e "${YELLOW}Warning: Port 8080 is already in use${NC}"
        echo "Impetus can be configured to use a different port in .env"
    fi
    
    # Check for git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}Error: Git is required${NC}"
        echo "Install with: xcode-select --install"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All requirements met${NC}"
}

install_impetus() {
    echo -e "${YELLOW}Installing Impetus LLM Server...${NC}"
    
    # Clone repository
    if [ -d "$INSTALL_DIR" ]; then
        echo "Installation directory already exists. Updating..."
        cd "$INSTALL_DIR"
        git pull
    else
        echo "Cloning repository..."
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
    
    # Create virtual environment
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install package
    echo "Installing Impetus..."
    pip install -e .
    
    # Install frontend dependencies
    echo "Installing frontend dependencies..."
    cd impetus-dashboard
    if command -v pnpm &> /dev/null; then
        pnpm install
    else
        echo -e "${YELLOW}pnpm not found, using npm...${NC}"
        npm install
    fi
    cd ..
    
    echo -e "${GREEN}✓ Installation complete${NC}"
}

create_config() {
    echo -e "${YELLOW}Creating configuration...${NC}"
    
    ENV_FILE="$INSTALL_DIR/gerdsen_ai_server/.env"
    
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << EOL
# Impetus LLM Server Configuration
IMPETUS_HOST=0.0.0.0
IMPETUS_PORT=8080
IMPETUS_API_KEY=$(openssl rand -hex 16)
IMPETUS_DEFAULT_MODEL=$DEFAULT_MODEL
IMPETUS_PERFORMANCE_MODE=balanced
IMPETUS_LOG_LEVEL=INFO
EOL
        echo -e "${GREEN}✓ Configuration created${NC}"
    else
        echo "Configuration already exists, skipping..."
    fi
}

create_launch_script() {
    echo -e "${YELLOW}Creating launch script...${NC}"
    
    LAUNCH_SCRIPT="$HOME/.local/bin/impetus"
    mkdir -p "$HOME/.local/bin"
    
    cat > "$LAUNCH_SCRIPT" << EOL
#!/bin/bash
source "$VENV_DIR/bin/activate"
cd "$INSTALL_DIR/gerdsen_ai_server"
python src/main.py "\$@"
EOL
    
    chmod +x "$LAUNCH_SCRIPT"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
        echo -e "${YELLOW}Added ~/.local/bin to PATH. Run 'source ~/.zshrc' to update.${NC}"
    fi
    
    echo -e "${GREEN}✓ Launch script created${NC}"
}

create_directories() {
    echo -e "${YELLOW}Creating Impetus directories...${NC}"
    
    # Create required directories
    mkdir -p "$HOME/.impetus/models"
    mkdir -p "$HOME/.impetus/cache"
    mkdir -p "$HOME/.impetus/logs"
    
    echo -e "${GREEN}✓ Created ~/.impetus directories${NC}"
}

download_model() {
    echo -e "${YELLOW}Would you like to download a model now? (y/n)${NC}"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Starting server temporarily to download model..."
        
        # Start server in background
        source "$VENV_DIR/bin/activate"
        cd "$INSTALL_DIR/gerdsen_ai_server"
        python src/main.py &
        SERVER_PID=$!
        
        # Wait for server to start
        echo "Waiting for server to start..."
        sleep 5
        
        # Download model
        echo "Downloading $DEFAULT_MODEL..."
        curl -X POST http://localhost:8080/api/models/download \
            -H "Content-Type: application/json" \
            -d "{\"model_id\": \"$DEFAULT_MODEL\", \"auto_load\": true}" \
            --silent
        
        echo -e "\n${YELLOW}Model download started. Check progress at http://localhost:5173${NC}"
        echo "Press any key to stop the server..."
        read -n 1
        
        # Stop server
        kill $SERVER_PID
        wait $SERVER_PID 2>/dev/null
    fi
}

print_success() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════╗"
    echo "║        Installation Complete! 🎉         ║"
    echo "╚══════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    echo "To start Impetus:"
    echo -e "  ${GREEN}impetus${NC}"
    echo
    echo "Or if you haven't reloaded your shell:"
    echo -e "  ${GREEN}source ~/.zshrc${NC}"
    echo -e "  ${GREEN}impetus${NC}"
    echo
    echo "Dashboard will be available at:"
    echo -e "  ${GREEN}http://localhost:5173${NC}"
    echo
    echo "API endpoint:"
    echo -e "  ${GREEN}http://localhost:8080${NC}"
    echo
    echo "Configuration file:"
    echo -e "  ${GREEN}$INSTALL_DIR/gerdsen_ai_server/.env${NC}"
    echo
}

# Main installation flow
main() {
    print_header
    check_requirements
    install_impetus
    create_directories
    create_config
    create_launch_script
    download_model
    print_success
}

# Run main function
main