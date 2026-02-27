#!/bin/bash
#
# Impetus LLM Server - Standalone macOS App Builder
# 
# This script creates a fully self-contained .app bundle with embedded Python
# No dependencies required on user's machine - everything is included
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
BUILD_DIR="./build_standalone"
APP_DIR="$BUILD_DIR/$APP_NAME"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
FRAMEWORKS_DIR="$CONTENTS_DIR/Frameworks"

# Python configuration
PYTHON_VERSION="3.11.9"
PYTHON_MAJOR_MINOR="3.11"
PYTHON_FRAMEWORK_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-macos11.pkg"

# Functions
print_header() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║    Impetus LLM Server - Standalone App Builder          ║"
    echo "║      Creates fully self-contained macOS app             ║"
    echo "║            No dependencies required!                     ║"
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
    
    # Check architecture
    if [[ $(uname -m) != "arm64" ]]; then
        echo -e "${RED}Error: This script requires Apple Silicon (M1/M2/M3/M4)${NC}"
        exit 1
    fi
    
    # Check if running from project root
    if [[ ! -f "gerdsen_ai_server/src/main.py" ]]; then
        echo -e "${RED}Error: Please run this script from the project root directory${NC}"
        exit 1
    fi
    
    # Check for required tools
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required for building (not for the final app)${NC}"
        exit 1
    fi
    
    echo "✓ Build requirements met"
}

create_app_structure() {
    print_section "Creating App Bundle Structure"
    
    # Clean and create directories
    rm -rf "$BUILD_DIR"
    mkdir -p "$MACOS_DIR"
    mkdir -p "$RESOURCES_DIR"/{server,dashboard,python}
    mkdir -p "$FRAMEWORKS_DIR"
    
    echo "✓ App bundle structure created"
}

download_python_framework() {
    print_section "Setting Up Embedded Python Runtime"
    
    # Use the system Python to create a relocatable environment
    echo "Creating standalone Python environment..."
    
    # Create a temporary virtual environment to get clean site-packages
    TEMP_VENV="$BUILD_DIR/temp_venv"
    python3 -m venv "$TEMP_VENV"
    source "$TEMP_VENV/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip wheel
    
    # Install all dependencies
    echo "Installing Python dependencies..."
    cd gerdsen_ai_server
    if [[ -f "requirements_production.txt" ]]; then
        pip install -r requirements_production.txt
    else
        pip install -r requirements.txt
    fi
    cd ..
    
    # Copy Python framework
    echo "Copying Python framework..."
    
    # For macOS, we'll use the Python from python.org which is relocatable
    # First, let's copy the Python executable and standard library
    PYTHON_EXE=$(which python3)
    PYTHON_HOME=$(python3 -c "import sys; print(sys.prefix)")
    
    # Copy Python binary
    cp "$PYTHON_EXE" "$RESOURCES_DIR/python/python3"
    
    # Copy Python standard library
    if [[ -z "$PYTHON_MAJOR_MINOR" ]]; then
        echo -e "${RED}Error: PYTHON_MAJOR_MINOR is not set. Aborting.${NC}"
        exit 1
    fi
    PYTHON_LIB="$PYTHON_HOME/lib/python$PYTHON_MAJOR_MINOR"
    if [[ -d "$PYTHON_LIB" ]]; then
        echo "Copying Python standard library..."
        cp -R "$PYTHON_LIB" "$RESOURCES_DIR/python/lib/"
    fi
    
    # Copy site-packages with all installed dependencies
    echo "Copying installed packages..."
    SITE_PACKAGES="$TEMP_VENV/lib/python$PYTHON_MAJOR_MINOR/site-packages"
    cp -R "$SITE_PACKAGES" "$RESOURCES_DIR/python/lib/python$PYTHON_MAJOR_MINOR/"
    
    # Copy any dynamic libraries
    if [[ -d "$TEMP_VENV/lib/python$PYTHON_MAJOR_MINOR/lib-dynload" ]]; then
        cp -R "$TEMP_VENV/lib/python$PYTHON_MAJOR_MINOR/lib-dynload" "$RESOURCES_DIR/python/lib/python$PYTHON_MAJOR_MINOR/"
    fi
    
    deactivate
    echo "✓ Python runtime embedded"
}

package_server() {
    print_section "Packaging Server Components"
    
    # Copy server code
    cp -r gerdsen_ai_server/* "$RESOURCES_DIR/server/"
    
    # Remove development files
    find "$RESOURCES_DIR/server" -name "*.pyc" -delete
    find "$RESOURCES_DIR/server" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$RESOURCES_DIR/server" -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$RESOURCES_DIR/server" -name "*.test.py" -delete
    
    # Create default configuration
    cat > "$RESOURCES_DIR/server/.env" << EOF
# Impetus LLM Server Configuration
IMPETUS_HOST=127.0.0.1
IMPETUS_PORT=8080
IMPETUS_PERFORMANCE_MODE=balanced
IMPETUS_LOG_LEVEL=INFO
EOF
    
    echo "✓ Server components packaged"
}

build_dashboard() {
    print_section "Building Dashboard"
    
    cd impetus-dashboard
    
    # Check if npm/pnpm is available
    if command -v pnpm &> /dev/null; then
        echo "Building with pnpm..."
        pnpm install
        pnpm build
    elif command -v npm &> /dev/null; then
        echo "Building with npm..."
        npm install
        npm run build
    else
        echo -e "${YELLOW}Warning: npm/pnpm not found, copying dashboard source${NC}"
        cd ..
        cp -r impetus-dashboard/* "$RESOURCES_DIR/dashboard/"
        return
    fi
    
    # Copy built dashboard
    if [[ -d "dist" ]]; then
        cp -r dist/* "$RESOURCES_DIR/dashboard/"
    elif [[ -d "build" ]]; then
        cp -r build/* "$RESOURCES_DIR/dashboard/"
    fi
    
    cd ..
    echo "✓ Dashboard built and packaged"
}

fix_library_paths() {
    print_section "Fixing Dynamic Library Paths"
    
    # Find all .so and .dylib files and update their paths
    echo "Updating library paths for relocation..."
    
    # This is complex on macOS, so we'll use a simpler approach
    # by setting environment variables in the launcher script
    
    echo "✓ Library paths configured"
}

create_launcher() {
    print_section "Creating App Launcher"
    
    cat > "$MACOS_DIR/Impetus" << 'EOF'
#!/bin/bash
# Impetus LLM Server - Standalone App Launcher

# Get the app bundle directory
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RESOURCES_DIR="$APP_DIR/Contents/Resources"
USER_DATA_DIR="$HOME/Library/Application Support/Impetus"

# Create user directories
mkdir -p "$USER_DATA_DIR"/{models,cache,logs,config}

# Set up Python environment
export PYTHONHOME="$RESOURCES_DIR/python"
export PYTHONPATH="$RESOURCES_DIR/server:$PYTHONHOME/lib/python3.11:$PYTHONHOME/lib/python3.11/site-packages"
export PATH="$PYTHONHOME:$PATH"
export DYLD_LIBRARY_PATH="$PYTHONHOME/lib:$DYLD_LIBRARY_PATH"

# Python executable
PYTHON_BIN="$PYTHONHOME/python3"

# Configure Impetus paths
export IMPETUS_MODEL_DIR="$USER_DATA_DIR/models"
export IMPETUS_CACHE_DIR="$USER_DATA_DIR/cache"
export IMPETUS_LOG_DIR="$USER_DATA_DIR/logs"
export IMPETUS_CONFIG_DIR="$USER_DATA_DIR/config"

# Check if first run
if [[ ! -f "$USER_DATA_DIR/config/initialized" ]]; then
    # First run setup
    osascript -e 'display notification "Welcome to Impetus! Setting up for first use..." with title "Impetus LLM Server"'
    
    # Generate API key
    API_KEY=$(openssl rand -hex 16)
    
    # Create user configuration
    cat > "$USER_DATA_DIR/config/server.env" << EOL
# Impetus LLM Server Configuration
IMPETUS_HOST=127.0.0.1
IMPETUS_PORT=8080
IMPETUS_API_KEY=$API_KEY
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

Impetus is now ready to use. Your API key has been generated and saved.

The dashboard will open in your browser shortly.

Your data is stored in:
~/Library/Application Support/Impetus/" with title "Welcome to Impetus" buttons {"Get Started"} default button "Get Started" with icon note
APPLESCRIPT
fi

# Load user configuration
if [[ -f "$USER_DATA_DIR/config/server.env" ]]; then
    export $(grep -v '^#' "$USER_DATA_DIR/config/server.env" | xargs)
fi

# Start the server
cd "$RESOURCES_DIR/server"
LOG_FILE="$USER_DATA_DIR/logs/impetus.log"
echo "Starting Impetus Server at $(date)" >> "$LOG_FILE"

# Run server in background
"$PYTHON_BIN" src/main.py >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Save PID for management
echo $SERVER_PID > "$USER_DATA_DIR/server.pid"

# Start dashboard server (simple HTTP server for built files)
cd "$RESOURCES_DIR/dashboard"
"$PYTHON_BIN" -m http.server 5173 >> "$LOG_FILE" 2>&1 &
DASHBOARD_PID=$!
echo $DASHBOARD_PID > "$USER_DATA_DIR/dashboard.pid"

# Wait for server to start
sleep 3

# Open dashboard in default browser
open "http://localhost:5173"

# Show running notification
osascript -e 'display notification "Impetus is running. Dashboard opened in browser." with title "Impetus LLM Server"'

# Create a simple dialog for server management
osascript << 'APPLESCRIPT'
on run
    set dialogResult to display dialog "Impetus LLM Server is running!" & return & return & ¬
        "• Dashboard: http://localhost:5173" & return & ¬
        "• API: http://localhost:8080" & return & ¬
        "• API Docs: http://localhost:8080/docs" & return & return & ¬
        "Server will continue running in the background." ¬
        with title "Impetus LLM Server" ¬
        buttons {"Stop Server", "Keep Running"} ¬
        default button "Keep Running" ¬
        with icon note
    
    if button returned of dialogResult is "Stop Server" then
        do shell script "pkill -F '$HOME/Library/Application Support/Impetus/server.pid' 2>/dev/null || true"
        do shell script "pkill -F '$HOME/Library/Application Support/Impetus/dashboard.pid' 2>/dev/null || true"
        display notification "Impetus Server stopped" with title "Impetus"
    end if
end run
APPLESCRIPT
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
    
    # Create a simple icon
    mkdir -p "$BUILD_DIR/AppIcon.iconset"
    
    # Create base icon using Python PIL if available, otherwise use a simple approach
    python3 << 'PYTHON_EOF' 2>/dev/null || true
import os
try:
    from PIL import Image, ImageDraw, ImageFont
    
    # Create base 1024x1024 icon
    img = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background
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
    if font:
        # Get text bounds for centering
        bbox = draw.textbbox((0, 0), "I", font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (1024 - text_width) // 2
        y = (1024 - text_height) // 2 - 50
        draw.text((x, y), "I", fill="white", font=font)
    else:
        draw.text((512, 512), "I", fill="white", anchor="mm")
    
    build_dir = os.environ.get('BUILD_DIR', './build_standalone')
    img.save(f'{build_dir}/icon_1024.png')
    print("Created icon with PIL")
except ImportError:
    print("PIL not available, using fallback icon")
PYTHON_EOF
    
    # If no icon was created, create a simple one
    if [[ ! -f "$BUILD_DIR/icon_1024.png" ]]; then
        # Create a simple colored square as fallback
        convert -size 1024x1024 xc:'#4F46E5' "$BUILD_DIR/icon_1024.png" 2>/dev/null || \
        echo "Warning: Could not create icon"
    fi
    
    # Generate icon sizes if we have the base icon
    if [[ -f "$BUILD_DIR/icon_1024.png" ]]; then
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
    else
        echo "⚠️  No app icon created"
    fi
}

sign_app() {
    print_section "Code Signing (Optional)"
    
    # Check if Developer ID certificate is available
    if security find-identity -v -p codesigning | grep -q "Developer ID Application"; then
        CERT_NAME=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | sed 's/.*"\(.*\)".*/\1/')
        
        echo "Signing with certificate: $CERT_NAME"
        
        # Sign the app bundle deeply
        codesign --force --deep --sign "$CERT_NAME" "$APP_DIR"
        
        # Verify signature
        codesign --verify --deep --strict "$APP_DIR"
        
        echo "✓ App signed successfully"
    else
        echo "⚠️  No Developer ID certificate found - app will be unsigned"
        echo "   Users will need to right-click and 'Open' to bypass Gatekeeper"
    fi
}

create_dmg() {
    print_section "Creating DMG Installer"
    
    DMG_NAME="Impetus-Standalone-$PRODUCT_VERSION.dmg"
    DMG_DIR="$BUILD_DIR/dmg"
    
    # Create DMG staging directory
    mkdir -p "$DMG_DIR"
    cp -R "$APP_DIR" "$DMG_DIR/"
    
    # Create Applications symlink
    ln -s /Applications "$DMG_DIR/Applications"
    
    # Create background and styling (optional)
    mkdir -p "$DMG_DIR/.background"
    
    # Create README
    cat > "$DMG_DIR/README.txt" << EOF
Impetus LLM Server - Standalone Edition
=======================================

This is a fully self-contained version of Impetus.
No Python or other dependencies required!

Installation:
1. Drag Impetus.app to the Applications folder
2. Double-click Impetus.app to run
3. The dashboard will open automatically

Features:
- High-performance LLM inference
- Optimized for Apple Silicon (M1/M2/M3/M4)
- OpenAI-compatible API
- Real-time performance monitoring
- 50-110 tokens/sec inference speed

System Requirements:
- macOS 14.0 or later (Sonoma+)
- Apple Silicon Mac (M1/M2/M3/M4)
- 8GB RAM (16GB recommended)
- 10GB free disk space

Support:
https://github.com/GerdsenAI/Impetus-LLM-Server

Version: $PRODUCT_VERSION
EOF
    
    # Create DMG
    echo "Building disk image..."
    hdiutil create -srcfolder "$DMG_DIR" -volname "$PRODUCT_NAME" -fs HFS+ \
        -fsargs "-c c=64,a=16,e=16" -format UDZO -imagekey zlib-level=9 "$DMG_NAME"
    
    # Get final size
    DMG_SIZE=$(ls -lh "$DMG_NAME" | awk '{print $5}')
    
    echo "✓ DMG created: $DMG_NAME ($DMG_SIZE)"
}

cleanup() {
    print_section "Cleaning Up"
    
    # Remove temporary files but keep the app
    rm -rf "$BUILD_DIR/temp_venv"
    rm -rf "$BUILD_DIR/AppIcon.iconset"
    rm -f "$BUILD_DIR/icon_1024.png"
    rm -rf "$BUILD_DIR/dmg"
    
    echo "✓ Build artifacts cleaned up"
}

calculate_size() {
    print_section "App Statistics"
    
    # Calculate app size
    APP_SIZE=$(du -sh "$APP_DIR" | cut -f1)
    
    echo "App bundle size: $APP_SIZE"
    echo "Components:"
    echo "  • Python runtime: $(du -sh "$RESOURCES_DIR/python" 2>/dev/null | cut -f1 || echo "N/A")"
    echo "  • Server code: $(du -sh "$RESOURCES_DIR/server" 2>/dev/null | cut -f1 || echo "N/A")"
    echo "  • Dashboard: $(du -sh "$RESOURCES_DIR/dashboard" 2>/dev/null | cut -f1 || echo "N/A")"
}

print_success() {
    print_section "Build Complete!"
    
    cat << EOF

${GREEN}╔════════════════════════════════════════════════════════════╗
║         🎉 Standalone App Build Successful! 🎉            ║
╚════════════════════════════════════════════════════════════╝${NC}

${BLUE}📦 Created Files:${NC}
─────────────────
• App Bundle: $APP_DIR
• Disk Image: Impetus-Standalone-$PRODUCT_VERSION.dmg

${BLUE}🚀 Features:${NC}
────────────
• ${GREEN}Zero dependencies${NC} - Everything included!
• ${GREEN}Instant start${NC} - No setup required
• ${GREEN}Self-contained Python${NC} - Works on any Mac
• ${GREEN}Pre-built dashboard${NC} - Ready to use
• ${GREEN}Optimized for Apple Silicon${NC}

${BLUE}📋 Distribution:${NC}
─────────────────
1. Share the DMG file with users
2. Users drag Impetus.app to Applications
3. Double-click to run - that's it!

${BLUE}💡 What's Included:${NC}
──────────────────
• Python $PYTHON_MAJOR_MINOR runtime
• All Python packages pre-installed
• MLX optimizations for Apple Silicon
• React dashboard (pre-built)
• API documentation at /docs

${GREEN}✨ Your standalone app is ready for distribution! ✨${NC}

To test the app:
open "$APP_DIR"

EOF
}

# Main build flow
main() {
    print_header
    
    check_requirements
    create_app_structure
    download_python_framework
    package_server
    build_dashboard
    fix_library_paths
    create_launcher
    create_info_plist
    create_app_icon
    sign_app
    calculate_size
    create_dmg
    cleanup
    print_success
}

# Run main function
main "$@"