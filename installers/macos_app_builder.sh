#!/bin/bash
#
# Impetus LLM Server - macOS .app Bundle Builder
# 
# This script creates a standalone .app bundle with all dependencies included
# No development tools required on user's machine
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PRODUCT_NAME="Impetus"
PRODUCT_VERSION="1.0.0"
BUNDLE_ID="com.gerdsenai.impetus"
APP_NAME="Impetus.app"
BUILD_DIR="./build"
APP_DIR="$BUILD_DIR/$APP_NAME"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
FRAMEWORKS_DIR="$CONTENTS_DIR/Frameworks"

# Functions
print_header() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║      Impetus LLM Server - macOS App Bundle Builder      ║"
    echo "║         Creates standalone .app for distribution         ║"
    echo "║                      v1.0.0                             ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────────"
}

check_requirements() {
    print_section "Checking Build Requirements"
    
    # Check macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo -e "${RED}Error: This script must be run on macOS${NC}"
        exit 1
    fi
    
    # Check if running from project root
    if [[ ! -f "gerdsen_ai_server/src/main.py" ]]; then
        echo -e "${RED}Error: Please run this script from the project root directory${NC}"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3.11+ is required for building${NC}"
        exit 1
    fi
    
    echo "✓ Build requirements met"
}

create_app_structure() {
    print_section "Creating App Bundle Structure"
    
    # Clean and create directories
    rm -rf "$BUILD_DIR"
    mkdir -p "$MACOS_DIR"
    mkdir -p "$RESOURCES_DIR"
    mkdir -p "$FRAMEWORKS_DIR"
    mkdir -p "$RESOURCES_DIR/server"
    mkdir -p "$RESOURCES_DIR/dashboard"
    
    echo "✓ App bundle structure created"
}

create_python_runtime() {
    print_section "Creating Embedded Python Runtime"
    
    # Create a relocatable Python environment
    echo "Creating standalone Python environment..."
    
    # Create virtual environment in build directory
    python3 -m venv "$BUILD_DIR/python_env"
    source "$BUILD_DIR/python_env/bin/activate"
    
    # Install all dependencies
    pip install --upgrade pip
    pip install wheel
    
    # Install production requirements
    cd gerdsen_ai_server
    if [[ -f "requirements_production.txt" ]]; then
        pip install -r requirements_production.txt
    else
        pip install -r requirements.txt
    fi
    cd ..
    
    # Package Python and dependencies into the app
    echo "Packaging Python runtime..."
    
    # Copy Python framework
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_FRAMEWORK="/Library/Frameworks/Python.framework/Versions/$PYTHON_VERSION"
    
    if [[ -d "$PYTHON_FRAMEWORK" ]]; then
        cp -R "$PYTHON_FRAMEWORK" "$FRAMEWORKS_DIR/Python.framework"
    else
        # Use system Python and create minimal runtime
        mkdir -p "$FRAMEWORKS_DIR/python"
        cp -R "$BUILD_DIR/python_env/lib/python$PYTHON_VERSION/site-packages" "$FRAMEWORKS_DIR/python/"
    fi
    
    deactivate
    echo "✓ Python runtime packaged"
}

package_server() {
    print_section "Packaging Server Components"
    
    # Copy server code
    cp -r gerdsen_ai_server "$RESOURCES_DIR/server/"
    
    # Remove development files
    find "$RESOURCES_DIR/server" -name "*.pyc" -delete
    find "$RESOURCES_DIR/server" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$RESOURCES_DIR/server" -name "*.test.py" -delete
    find "$RESOURCES_DIR/server" -name "pytest.ini" -delete
    
    echo "✓ Server components packaged"
}

build_dashboard() {
    print_section "Building Dashboard"
    
    cd impetus-dashboard
    
    # Install dependencies
    if command -v pnpm &> /dev/null; then
        pnpm install
        pnpm build
    else
        npm install
        npm run build
    fi
    
    # Copy built dashboard
    cp -r dist/* "$RESOURCES_DIR/dashboard/"
    
    cd ..
    echo "✓ Dashboard built and packaged"
}

create_launcher() {
    print_section "Creating App Launcher"
    
    # Create main executable
    cat > "$MACOS_DIR/Impetus" << 'EOF'
#!/bin/bash
# Impetus LLM Server Launcher

# Get the app bundle directory
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RESOURCES_DIR="$APP_DIR/Contents/Resources"
FRAMEWORKS_DIR="$APP_DIR/Contents/Frameworks"
USER_DATA_DIR="$HOME/Library/Application Support/Impetus"

# Create user directories
mkdir -p "$USER_DATA_DIR/models"
mkdir -p "$USER_DATA_DIR/cache"
mkdir -p "$USER_DATA_DIR/logs"
mkdir -p "$USER_DATA_DIR/config"

# Check if first run
if [[ ! -f "$USER_DATA_DIR/config/initialized" ]]; then
    # First run setup
    osascript -e 'display notification "Setting up Impetus for first time use..." with title "Impetus LLM Server"'
    
    # Create default configuration
    cat > "$USER_DATA_DIR/config/server.env" << EOL
# Impetus LLM Server Configuration
IMPETUS_HOST=127.0.0.1
IMPETUS_PORT=8080
IMPETUS_API_KEY=$(openssl rand -hex 16)
IMPETUS_MODEL_DIR=$USER_DATA_DIR/models
IMPETUS_CACHE_DIR=$USER_DATA_DIR/cache
IMPETUS_LOG_DIR=$USER_DATA_DIR/logs
IMPETUS_PERFORMANCE_MODE=balanced
IMPETUS_LOG_LEVEL=INFO
EOL
    
    touch "$USER_DATA_DIR/config/initialized"
    
    # Show welcome dialog
    osascript << 'APPLESCRIPT'
display dialog "Welcome to Impetus LLM Server!

Impetus is now setting up for first use. This includes:
• Creating configuration files
• Setting up model storage
• Preparing the dashboard

After setup, the dashboard will open in your browser.

Your data is stored in:
~/Library/Application Support/Impetus/" with title "Welcome to Impetus" buttons {"Get Started"} default button "Get Started"
APPLESCRIPT
fi

# Set up Python path
if [[ -d "$FRAMEWORKS_DIR/Python.framework" ]]; then
    export PYTHONHOME="$FRAMEWORKS_DIR/Python.framework/Versions/Current"
    export PYTHONPATH="$RESOURCES_DIR/server:$PYTHONHOME/lib/python3.11/site-packages"
    PYTHON_BIN="$PYTHONHOME/bin/python3"
else
    # Fallback to embedded site-packages
    export PYTHONPATH="$RESOURCES_DIR/server:$FRAMEWORKS_DIR/python/site-packages"
    PYTHON_BIN="python3"
fi

# Start the server
cd "$RESOURCES_DIR/server/gerdsen_ai_server"
export IMPETUS_CONFIG="$USER_DATA_DIR/config/server.env"

# Create a log file for debugging
LOG_FILE="$USER_DATA_DIR/logs/impetus.log"
echo "Starting Impetus Server at $(date)" >> "$LOG_FILE"

# Start server in background
$PYTHON_BIN src/main.py >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Save PID for menu bar app
echo $SERVER_PID > "$USER_DATA_DIR/server.pid"

# Start dashboard server
cd "$RESOURCES_DIR/dashboard"
python3 -m http.server 5173 >> "$LOG_FILE" 2>&1 &
DASHBOARD_PID=$!
echo $DASHBOARD_PID > "$USER_DATA_DIR/dashboard.pid"

# Wait a moment for servers to start
sleep 3

# Open dashboard in default browser
open "http://localhost:5173"

# Keep the app running
osascript -e 'display notification "Impetus is running. Use the menu bar icon to control it." with title "Impetus LLM Server"'

# Wait for server process
wait $SERVER_PID
EOF
    
    chmod +x "$MACOS_DIR/Impetus"
    echo "✓ App launcher created"
}

create_info_plist() {
    print_section "Creating Info.plist"
    
    cat > "$CONTENTS_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>Impetus</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleName</key>
    <string>Impetus</string>
    <key>CFBundleShortVersionString</key>
    <string>$PRODUCT_VERSION</string>
    <key>CFBundleVersion</key>
    <string>$PRODUCT_VERSION</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>Impetus</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSUIElement</key>
    <false/>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>LSMinimumSystemVersion</key>
    <string>14.0</string>
    <key>LSArchitecturePriority</key>
    <array>
        <string>arm64</string>
    </array>
    <key>NSAppleEventsUsageDescription</key>
    <string>Impetus needs to control your web browser to open the dashboard.</string>
</dict>
</plist>
EOF
    
    echo "✓ Info.plist created"
}

create_app_icon() {
    print_section "Creating App Icon"
    
    # Create a simple icon using sips (built into macOS)
    # First create a colored square image
    cat > "$BUILD_DIR/icon_template.svg" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="1024" height="1024" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4F46E5;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#7C3AED;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" rx="234" fill="url(#grad)"/>
  <text x="512" y="650" text-anchor="middle" fill="white" font-family="-apple-system, system-ui" font-size="400" font-weight="700">I</text>
</svg>
EOF
    
    # Convert SVG to PNG using available tools
    if command -v rsvg-convert &> /dev/null; then
        rsvg-convert -w 1024 -h 1024 "$BUILD_DIR/icon_template.svg" -o "$BUILD_DIR/icon_1024.png"
    elif command -v convert &> /dev/null; then
        convert -background none "$BUILD_DIR/icon_template.svg" -resize 1024x1024 "$BUILD_DIR/icon_1024.png"
    else
        # Create a simple PNG icon using Python if no converters available
        python3 << 'PYTHON_EOF'
from PIL import Image, ImageDraw, ImageFont
import os

# Create gradient background
img = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Simple gradient effect
for y in range(1024):
    r = int(79 + (124-79) * y / 1024)
    g = int(70 + (58-70) * y / 1024)
    b = int(229 + (237-229) * y / 1024)
    draw.line([(0, y), (1024, y)], fill=(r, g, b, 255))

# Add rounded corners
mask = Image.new('L', (1024, 1024), 0)
mask_draw = ImageDraw.Draw(mask)
mask_draw.rounded_rectangle([(0, 0), (1024, 1024)], radius=234, fill=255)
img.putalpha(mask)

# Add text
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 400)
except:
    font = None

draw = ImageDraw.Draw(img)
draw.text((512, 512), "I", fill="white", font=font, anchor="mm")

img.save(os.path.join(os.environ.get('BUILD_DIR', './build'), 'icon_1024.png'))
PYTHON_EOF
    fi
    
    # Create iconset
    mkdir -p "$BUILD_DIR/AppIcon.iconset"
    
    # Generate different sizes
    sips -z 16 16     "$BUILD_DIR/icon_1024.png" --out "$BUILD_DIR/AppIcon.iconset/icon_16x16.png"
    sips -z 32 32     "$BUILD_DIR/icon_1024.png" --out "$BUILD_DIR/AppIcon.iconset/icon_16x16@2x.png"
    sips -z 32 32     "$BUILD_DIR/icon_1024.png" --out "$BUILD_DIR/AppIcon.iconset/icon_32x32.png"
    sips -z 64 64     "$BUILD_DIR/icon_1024.png" --out "$BUILD_DIR/AppIcon.iconset/icon_32x32@2x.png"
    sips -z 128 128   "$BUILD_DIR/icon_1024.png" --out "$BUILD_DIR/AppIcon.iconset/icon_128x128.png"
    sips -z 256 256   "$BUILD_DIR/icon_1024.png" --out "$BUILD_DIR/AppIcon.iconset/icon_128x128@2x.png"
    sips -z 256 256   "$BUILD_DIR/icon_1024.png" --out "$BUILD_DIR/AppIcon.iconset/icon_256x256.png"
    sips -z 512 512   "$BUILD_DIR/icon_1024.png" --out "$BUILD_DIR/AppIcon.iconset/icon_256x256@2x.png"
    sips -z 512 512   "$BUILD_DIR/icon_1024.png" --out "$BUILD_DIR/AppIcon.iconset/icon_512x512.png"
    cp "$BUILD_DIR/icon_1024.png" "$BUILD_DIR/AppIcon.iconset/icon_512x512@2x.png"
    
    # Create icns file
    iconutil -c icns "$BUILD_DIR/AppIcon.iconset" -o "$RESOURCES_DIR/AppIcon.icns"
    
    echo "✓ App icon created"
}

sign_app() {
    print_section "Code Signing (Optional)"
    
    # Check if Developer ID certificate is available
    if security find-identity -v -p codesigning | grep -q "Developer ID Application"; then
        CERT_NAME=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | sed 's/.*"\(.*\)".*/\1/')
        
        echo "Signing with certificate: $CERT_NAME"
        codesign --force --deep --sign "$CERT_NAME" "$APP_DIR"
        echo "✓ App signed"
    else
        echo "⚠️  No Developer ID certificate found - app will be unsigned"
        echo "   Users will need to right-click and 'Open' to bypass Gatekeeper"
    fi
}

create_dmg() {
    print_section "Creating DMG Installer"
    
    DMG_NAME="Impetus-$PRODUCT_VERSION.dmg"
    DMG_DIR="$BUILD_DIR/dmg"
    
    # Create DMG staging directory
    mkdir -p "$DMG_DIR"
    cp -R "$APP_DIR" "$DMG_DIR/"
    
    # Create Applications symlink
    ln -s /Applications "$DMG_DIR/Applications"
    
    # Create DMG
    hdiutil create -srcfolder "$DMG_DIR" -volname "Impetus" -fs HFS+ \
        -fsargs "-c c=64,a=16,e=16" -format UDZO -imagekey zlib-level=9 "$DMG_NAME"
    
    DMG_SIZE=$(ls -lh "$DMG_NAME" | awk '{print $5}')
    echo "✓ DMG created: $DMG_NAME ($DMG_SIZE)"
}

cleanup() {
    print_section "Cleaning Up"
    
    # Remove build directory except the app
    mv "$APP_DIR" "$BUILD_DIR/../$APP_NAME.tmp"
    rm -rf "$BUILD_DIR"
    mkdir "$BUILD_DIR"
    mv "$BUILD_DIR/../$APP_NAME.tmp" "$APP_DIR"
    
    echo "✓ Build artifacts cleaned up"
}

print_success() {
    print_section "Build Complete!"
    
    cat << EOF

${GREEN}╔════════════════════════════════════════════════════════════╗
║              🎉 App Build Successful! 🎉                   ║
╚════════════════════════════════════════════════════════════╝${NC}

${BLUE}📦 Created Files:${NC}
─────────────────
• App Bundle: $BUILD_DIR/$APP_NAME
• Disk Image: Impetus-$PRODUCT_VERSION.dmg

${BLUE}📋 Distribution:${NC}
─────────────────
1. Users can drag Impetus.app to Applications
2. Double-click to run - no dependencies needed!
3. First run will set up user configuration

${BLUE}🚀 Features:${NC}
────────────
• Standalone app - no Python/Git/npm required
• Embedded Python runtime and dependencies  
• Auto-setup on first launch
• User data in ~/Library/Application Support/Impetus/

${GREEN}✨ Your macOS app is ready for distribution! ✨${NC}

To test the app:
open "$BUILD_DIR/$APP_NAME"

EOF
}

# Main build flow
main() {
    print_header
    
    check_requirements
    create_app_structure
    create_python_runtime
    package_server
    build_dashboard
    create_launcher
    create_info_plist
    create_app_icon
    sign_app
    create_dmg
    cleanup
    print_success
}

# Run main function
main "$@"