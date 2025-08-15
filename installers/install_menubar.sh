#!/bin/bash
#
# Impetus Menu Bar App Installer
# Installs the Impetus menu bar application for macOS
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║         Impetus Menu Bar App Installer                   ║"
    echo "║     Native macOS menu bar control for Impetus            ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────────"
}

check_requirements() {
    print_section "Checking Requirements"
    
    # Check macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo -e "${RED}Error: This script must be run on macOS${NC}"
        exit 1
    fi
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required${NC}"
        echo "Install from: https://www.python.org/downloads/"
        exit 1
    fi
    
    echo "✓ All requirements met"
}

setup_virtualenv() {
    print_section "Setting Up Python Environment"
    
    # Check if we're in project root
    if [[ ! -f "gerdsen_ai_server/src/main.py" ]]; then
        echo -e "${RED}Error: Please run this script from the project root directory${NC}"
        exit 1
    fi
    
    # Create or activate virtual environment
    if [[ ! -d ".venv" ]]; then
        echo "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    echo "Activating virtual environment..."
    source .venv/bin/activate
    
    echo "✓ Python environment ready"
}

install_dependencies() {
    print_section "Installing Menu Bar Dependencies"
    
    echo "Installing rumps (menu bar framework)..."
    pip install rumps
    
    echo "Installing PyObjC (macOS integration)..."
    pip install pyobjc-core pyobjc-framework-Cocoa
    
    echo "Installing psutil (for system stats)..."
    pip install psutil
    
    echo "✓ Dependencies installed"
}

create_launch_agent() {
    print_section "Creating Launch Agent (Optional)"
    
    PLIST_PATH="$HOME/Library/LaunchAgents/com.gerdsenai.impetus.menubar.plist"
    PROJECT_DIR="$(pwd)"
    
    echo "Creating launch agent for auto-start..."
    
    cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gerdsenai.impetus.menubar</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/.venv/bin/python</string>
        <string>$PROJECT_DIR/run_menubar.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/impetus-menubar.err</string>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/impetus-menubar.out</string>
</dict>
</plist>
EOF
    
    echo "✓ Launch agent created (will start on login)"
}

create_app_alias() {
    print_section "Creating Desktop Shortcut"
    
    # Create an alias on Desktop for easy access
    DESKTOP_SCRIPT="$HOME/Desktop/Impetus Menu Bar.command"
    PROJECT_DIR="$(pwd)"
    
    cat > "$DESKTOP_SCRIPT" << EOF
#!/bin/bash
cd "$PROJECT_DIR"
source .venv/bin/activate
python run_menubar.py
EOF
    
    chmod +x "$DESKTOP_SCRIPT"
    
    echo "✓ Desktop shortcut created"
}

test_installation() {
    print_section "Testing Installation"
    
    echo "Starting menu bar app for 5 seconds..."
    
    # Start in background
    python run_menubar.py &
    PID=$!
    
    # Wait a bit
    sleep 5
    
    # Check if it's running
    if ps -p $PID > /dev/null; then
        echo "✓ Menu bar app is running successfully!"
        
        # Kill the test instance
        kill $PID 2>/dev/null || true
    else
        echo -e "${YELLOW}Warning: Menu bar app may have issues${NC}"
    fi
}

print_success() {
    echo -e "\n${GREEN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           🎉 Menu Bar App Installed Successfully! 🎉       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "\n${BLUE}📱 How to Use:${NC}"
    echo "────────────────"
    echo "1. Start manually:"
    echo "   ${GREEN}python run_menubar.py${NC}"
    echo ""
    echo "2. Or use desktop shortcut:"
    echo "   Double-click '${GREEN}Impetus Menu Bar${NC}' on your Desktop"
    echo ""
    echo "3. Auto-start on login:"
    echo "   ${GREEN}launchctl load ~/Library/LaunchAgents/com.gerdsenai.impetus.menubar.plist${NC}"
    echo ""
    echo -e "${BLUE}📋 Features:${NC}"
    echo "────────────"
    echo "• Start/stop Impetus server from menu bar"
    echo "• Load and switch between MLX models"
    echo "• Monitor server performance"
    echo "• Quick access to dashboard and API docs"
    echo "• System tray notifications"
    echo ""
    echo -e "${BLUE}🛑 To Stop:${NC}"
    echo "────────────"
    echo "Click the brain icon (🧠) in menu bar → Quit Impetus"
    echo ""
    echo -e "${GREEN}✨ Your menu bar app is ready to use! ✨${NC}"
}

main() {
    print_header
    
    check_requirements
    setup_virtualenv
    install_dependencies
    
    # Ask about auto-start
    echo -e "\n${YELLOW}Would you like to auto-start the menu bar app on login? (y/n)${NC}"
    read -r response
    if [[ "$response" == "y" || "$response" == "Y" ]]; then
        create_launch_agent
    fi
    
    create_app_alias
    test_installation
    print_success
}

# Run main function
main "$@"