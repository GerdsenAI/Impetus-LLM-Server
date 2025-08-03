#!/bin/bash
#
# Impetus LLM Server - Simple macOS App Creator
# 
# This creates a basic .app that uses the system Python
# Much simpler than trying to embed everything
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="Impetus.app"
BUILD_DIR="./build"
APP_DIR="$BUILD_DIR/$APP_NAME"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

print_header() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║       Impetus LLM Server - Simple App Creator           ║"
    echo "║              Creates a basic macOS .app                  ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Create app structure
echo "Creating app bundle..."
rm -rf "$BUILD_DIR"
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Copy all project files to Resources
echo "Copying project files..."
cp -r gerdsen_ai_server "$RESOURCES_DIR/"
cp -r impetus-dashboard "$RESOURCES_DIR/"
cp -r docs "$RESOURCES_DIR/"
cp README.md LICENSE "$RESOURCES_DIR/" 2>/dev/null || true

# Create the main executable
cat > "$MACOS_DIR/Impetus" << 'EOF'
#!/bin/bash
# Impetus LLM Server - App Launcher

RESOURCES_DIR="$(dirname "$0")/../Resources"
USER_DIR="$HOME/Library/Application Support/Impetus"
VENV_DIR="$USER_DIR/venv"
CONFIG_FILE="$USER_DIR/config.json"
LOG_FILE="$USER_DIR/impetus.log"

# Create user directories
mkdir -p "$USER_DIR"
mkdir -p "$USER_DIR/models"
mkdir -p "$USER_DIR/cache"

# Function to show dialog
show_dialog() {
    osascript -e "display dialog \"$1\" with title \"Impetus\" buttons {\"OK\"} default button \"OK\""
}

# Function to show notification
show_notification() {
    osascript -e "display notification \"$1\" with title \"Impetus\""
}

# Check Python
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "Python 3 is required to run Impetus.

Please install Python 3.11 or later from:
https://www.python.org/downloads/

Or via Homebrew:
brew install python@3.11" with title "Python Required" buttons {"Open Python Website", "Cancel"} default button "Open Python Website"'
    
    if [[ $? -eq 0 ]]; then
        open "https://www.python.org/downloads/"
    fi
    exit 1
fi

# First time setup
if [[ ! -f "$CONFIG_FILE" ]]; then
    show_notification "Setting up Impetus for first use..."
    
    # Create virtual environment
    echo "Creating Python environment..." > "$LOG_FILE"
    python3 -m venv "$VENV_DIR" >> "$LOG_FILE" 2>&1
    
    # Install dependencies
    echo "Installing dependencies..." >> "$LOG_FILE"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip >> "$LOG_FILE" 2>&1
    
    cd "$RESOURCES_DIR/gerdsen_ai_server"
    pip install -r requirements.txt >> "$LOG_FILE" 2>&1
    cd - > /dev/null
    
    # Build frontend
    echo "Building dashboard..." >> "$LOG_FILE"
    cd "$RESOURCES_DIR/impetus-dashboard"
    if command -v npm &> /dev/null; then
        npm install >> "$LOG_FILE" 2>&1
        npm run build >> "$LOG_FILE" 2>&1
    else
        echo "npm not found, dashboard may not work properly" >> "$LOG_FILE"
    fi
    cd - > /dev/null
    
    # Create config
    cat > "$CONFIG_FILE" << EOL
{
    "installed": true,
    "version": "1.0.0",
    "api_key": "$(openssl rand -hex 16)"
}
EOL
    
    show_dialog "Impetus has been set up successfully!

The server will now start and the dashboard will open in your browser.

API Key has been generated and saved."
fi

# Start server
show_notification "Starting Impetus Server..."

# Activate virtual environment and start server
source "$VENV_DIR/bin/activate"
cd "$RESOURCES_DIR/gerdsen_ai_server"

# Start in background
python src/main.py >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Open dashboard
open "http://localhost:5173"

# Create a simple menu bar controller
osascript << 'APPLESCRIPT'
on run
    display dialog "Impetus is running!" & return & return & ¬
        "• Dashboard: http://localhost:5173" & return & ¬
        "• API: http://localhost:8080" & return & return & ¬
        "Click Stop to shut down the server." ¬
        with title "Impetus LLM Server" ¬
        buttons {"Stop Server", "Hide"} ¬
        default button "Hide"
    
    if button returned of result is "Stop Server" then
        do shell script "pkill -f 'python.*main.py'"
        display notification "Impetus Server stopped" with title "Impetus"
    end if
end run
APPLESCRIPT

# Kill server if dialog was used to stop
pkill -f "python.*main.py" 2>/dev/null || true
EOF

chmod +x "$MACOS_DIR/Impetus"

# Create Info.plist
cat > "$CONTENTS_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>Impetus</string>
    <key>CFBundleIdentifier</key>
    <string>com.gerdsenai.impetus</string>
    <key>CFBundleName</key>
    <string>Impetus</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>Impetus</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create a basic icon (optional)
if command -v sips &> /dev/null; then
    # Create a simple icon if we have sips
    cat > "$BUILD_DIR/icon.svg" << 'EOF'
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
  <rect width="128" height="128" rx="28" fill="#4F46E5"/>
  <text x="64" y="88" text-anchor="middle" fill="white" font-size="72" font-weight="bold">I</text>
</svg>
EOF
fi

# Create DMG
DMG_NAME="Impetus-1.0.0.dmg"
echo "Creating DMG installer..."

# Create DMG directory
DMG_DIR="$BUILD_DIR/dmg"
mkdir -p "$DMG_DIR"
cp -R "$APP_DIR" "$DMG_DIR/"
ln -s /Applications "$DMG_DIR/Applications"

# Create README
cat > "$DMG_DIR/README.txt" << EOF
Impetus LLM Server
==================

Installation:
1. Drag Impetus.app to the Applications folder
2. Double-click Impetus.app to run
3. On first run, it will install Python dependencies

Requirements:
- macOS 13.0+ on Apple Silicon
- Python 3.11+ (install from python.org or Homebrew)
- 8GB+ RAM recommended

The first launch will take a few minutes to set up.
EOF

# Build DMG
hdiutil create -srcfolder "$DMG_DIR" -volname "Impetus" -format UDZO "$DMG_NAME"

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ App Successfully Created!                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo
echo "Created files:"
echo "  • App: $APP_DIR"
echo "  • DMG: $DMG_NAME"
echo
echo "The app will:"
echo "  1. Check for Python on launch"
echo "  2. Set up virtual environment on first run"
echo "  3. Install all dependencies automatically"
echo "  4. Start the server and open dashboard"
echo
echo "To test: open $APP_DIR"
echo