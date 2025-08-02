#!/bin/bash
#
# Install Impetus as a system service
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    echo -e "${RED}Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

# Get username
USERNAME=$(whoami)
INSTALL_DIR="$HOME/impetus-llm-server"

install_macos() {
    echo -e "${YELLOW}Installing Impetus service for macOS...${NC}"
    
    # Create logs directory
    mkdir -p "$HOME/Library/Logs/impetus"
    
    # Copy and customize plist
    PLIST_FILE="/Library/LaunchDaemons/com.gerdsenai.impetus.plist"
    TEMP_PLIST="/tmp/impetus.plist"
    
    # Replace USERNAME placeholder
    sed "s|USERNAME|$USERNAME|g" impetus.plist > "$TEMP_PLIST"
    
    # Install plist
    echo "Installing launch daemon (requires sudo)..."
    sudo cp "$TEMP_PLIST" "$PLIST_FILE"
    sudo chown root:wheel "$PLIST_FILE"
    sudo chmod 644 "$PLIST_FILE"
    
    # Load service
    echo "Loading service..."
    sudo launchctl load "$PLIST_FILE"
    
    rm "$TEMP_PLIST"
    
    echo -e "${GREEN}✓ Service installed${NC}"
    echo
    echo "Commands:"
    echo "  Start:   sudo launchctl start com.gerdsenai.impetus"
    echo "  Stop:    sudo launchctl stop com.gerdsenai.impetus"
    echo "  Status:  sudo launchctl list | grep impetus"
    echo "  Logs:    tail -f ~/Library/Logs/impetus/server.log"
}

install_linux() {
    echo -e "${YELLOW}Installing Impetus service for Linux...${NC}"
    
    # Create logs directory
    sudo mkdir -p /var/log/impetus
    sudo chown "$USERNAME:$USERNAME" /var/log/impetus
    
    # Copy and customize service file
    SERVICE_FILE="/etc/systemd/system/impetus@$USERNAME.service"
    
    # Install service
    echo "Installing systemd service (requires sudo)..."
    sudo cp impetus.service "$SERVICE_FILE"
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service
    sudo systemctl enable "impetus@$USERNAME"
    
    echo -e "${GREEN}✓ Service installed${NC}"
    echo
    echo "Commands:"
    echo "  Start:   sudo systemctl start impetus@$USERNAME"
    echo "  Stop:    sudo systemctl stop impetus@$USERNAME"
    echo "  Status:  sudo systemctl status impetus@$USERNAME"
    echo "  Logs:    sudo journalctl -u impetus@$USERNAME -f"
}

# Main
echo -e "${GREEN}Impetus Service Installer${NC}"
echo

if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}Error: Impetus not found at $INSTALL_DIR${NC}"
    echo "Please run the main installer first: ./install.sh"
    exit 1
fi

cd "$(dirname "$0")"

if [ "$OS" == "macos" ]; then
    install_macos
elif [ "$OS" == "linux" ]; then
    install_linux
fi

echo
echo -e "${GREEN}Service installation complete!${NC}"