#!/bin/bash
#
# Impetus LLM Server - macOS GUI Package Installer Creator
# 
# This script creates a macOS .pkg installer with GUI interface
# for easy installation on macOS systems
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/GerdsenAI/Impetus-LLM-Server.git"
PRODUCT_NAME="Impetus LLM Server"
PRODUCT_VERSION="1.0.0"
BUNDLE_ID="com.gerdsenai.impetus"
INSTALL_DIR="/Applications/Impetus LLM Server"
PACKAGE_NAME="Impetus-LLM-Server-${PRODUCT_VERSION}.pkg"
BUILD_DIR="./build"
PAYLOAD_DIR="$BUILD_DIR/payload"
SCRIPTS_DIR="$BUILD_DIR/scripts"
RESOURCES_DIR="$BUILD_DIR/resources"

# Functions
print_header() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║      Impetus LLM Server - macOS GUI Installer Builder    ║"
    echo "║         Creates .pkg installer for macOS systems        ║"
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
    
    # Check Xcode command line tools
    if ! command -v pkgbuild &> /dev/null; then
        echo -e "${RED}Error: Xcode command line tools are required${NC}"
        echo "Install with: xcode-select --install"
        exit 1
    fi
    
    # Check if running from project root
    if [[ ! -f "gerdsen_ai_server/src/main.py" ]]; then
        echo -e "${RED}Error: Please run this script from the project root directory${NC}"
        exit 1
    fi
    
    echo "✓ Build requirements met"
}

create_build_structure() {
    print_section "Creating Build Structure"
    
    # Clean and create build directories
    rm -rf "$BUILD_DIR"
    mkdir -p "$PAYLOAD_DIR"
    mkdir -p "$SCRIPTS_DIR"
    mkdir -p "$RESOURCES_DIR"
    
    echo "✓ Build directories created"
}

prepare_payload() {
    print_section "Preparing Installation Payload"
    
    # Create application bundle structure
    APP_BUNDLE="$PAYLOAD_DIR/$INSTALL_DIR"
    mkdir -p "$APP_BUNDLE/Contents/MacOS"
    mkdir -p "$APP_BUNDLE/Contents/Resources"
    mkdir -p "$APP_BUNDLE/Contents/SharedSupport"
    
    # Copy application files
    echo "Copying application files..."
    cp -r gerdsen_ai_server "$APP_BUNDLE/Contents/SharedSupport/"
    cp -r impetus-dashboard "$APP_BUNDLE/Contents/SharedSupport/"
    cp -r service "$APP_BUNDLE/Contents/SharedSupport/"
    cp -r docs "$APP_BUNDLE/Contents/SharedSupport/"
    cp README.md QUICKSTART.md LICENSE RELEASE_NOTES.md "$APP_BUNDLE/Contents/SharedSupport/"
    cp install.sh "$APP_BUNDLE/Contents/SharedSupport/"
    
    # Create Info.plist
    cat > "$APP_BUNDLE/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>$PRODUCT_NAME</string>
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
    <string>impetus</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
</dict>
</plist>
EOF
    
    # Create launcher script
    cat > "$APP_BUNDLE/Contents/MacOS/impetus" << 'EOF'
#!/bin/bash
# Impetus LLM Server Launcher

APP_DIR="$(dirname "$0")/../SharedSupport"
cd "$APP_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    osascript -e 'display alert "Python 3 Required" message "Please install Python 3.11+ to run Impetus LLM Server.\n\nInstall with: brew install python@3.11" buttons {"OK"} default button "OK"'
    exit 1
fi

# Run the installation if needed
if [[ ! -d "$HOME/.impetus" ]]; then
    osascript -e 'display notification "Setting up Impetus for first time..." with title "Impetus LLM Server"'
    ./install.sh
fi

# Start the server
osascript -e 'display notification "Starting Impetus LLM Server..." with title "Impetus LLM Server"'
cd gerdsen_ai_server
python3 src/main.py &

# Open dashboard in browser
sleep 5
open http://localhost:5173
EOF
    
    chmod +x "$APP_BUNDLE/Contents/MacOS/impetus"
    
    # Create icon (basic text-based icon for now)
    cat > "$APP_BUNDLE/Contents/Resources/icon.svg" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="1024" height="1024" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4F46E5;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#7C3AED;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" rx="200" fill="url(#grad1)"/>
  <text x="512" y="600" text-anchor="middle" fill="white" font-family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif" font-size="200" font-weight="700">I</text>
  <text x="512" y="800" text-anchor="middle" fill="white" font-family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif" font-size="80" font-weight="400">IMPETUS</text>
</svg>
EOF
    
    echo "✓ Application payload prepared"
}

create_preinstall_script() {
    print_section "Creating Pre-install Script"
    
    cat > "$SCRIPTS_DIR/preinstall" << 'EOF'
#!/bin/bash
# Impetus LLM Server - Pre-install Script

# Check system requirements
if [[ $(uname -m) != "arm64" ]]; then
    echo "Error: Impetus requires Apple Silicon (M1/M2/M3/M4)"
    exit 1
fi

# Check macOS version
MIN_VERSION="13.0"
CURRENT_VERSION=$(sw_vers -productVersion)
if [[ $(echo "$CURRENT_VERSION < $MIN_VERSION" | bc) -eq 1 ]]; then
    echo "Error: macOS $MIN_VERSION or later is required (found $CURRENT_VERSION)"
    exit 1
fi

# Check available disk space
AVAILABLE_SPACE=$(df -g /Applications | awk 'NR==2 {print $4}')
if [[ $AVAILABLE_SPACE -lt 5 ]]; then
    echo "Error: At least 5GB of free space is required in /Applications"
    exit 1
fi

# Stop any running Impetus instances
pkill -f "impetus"
pkill -f "python.*main.py"

echo "Pre-install checks passed"
exit 0
EOF
    
    chmod +x "$SCRIPTS_DIR/preinstall"
    echo "✓ Pre-install script created"
}

create_postinstall_script() {
    print_section "Creating Post-install Script"
    
    cat > "$SCRIPTS_DIR/postinstall" << 'EOF'
#!/bin/bash
# Impetus LLM Server - Post-install Script

INSTALL_DIR="/Applications/Impetus LLM Server"
USER=$(stat -f "%Su" /dev/console)
USER_HOME=$(eval echo "~$USER")

# Create user directories
sudo -u "$USER" mkdir -p "$USER_HOME/.impetus/models"
sudo -u "$USER" mkdir -p "$USER_HOME/.impetus/cache"
sudo -u "$USER" mkdir -p "$USER_HOME/.impetus/logs"

# Create desktop shortcut
DESKTOP_DIR="$USER_HOME/Desktop"
if [[ -d "$DESKTOP_DIR" ]]; then
    cat > "$DESKTOP_DIR/Impetus LLM Server.command" << 'LAUNCHER_EOF'
#!/bin/bash
cd "/Applications/Impetus LLM Server/Contents/SharedSupport"
./install.sh
LAUNCHER_EOF
    chmod +x "$DESKTOP_DIR/Impetus LLM Server.command"
    chown "$USER:staff" "$DESKTOP_DIR/Impetus LLM Server.command"
fi

# Create Applications folder alias
if [[ ! -e "/Applications/Impetus.app" ]]; then
    ln -s "$INSTALL_DIR" "/Applications/Impetus.app"
fi

# Set permissions
chown -R "$USER:admin" "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"

# Display completion message
sudo -u "$USER" osascript << 'APPLESCRIPT_EOF'
display dialog "Impetus LLM Server has been installed successfully!

To get started:
1. Double-click the Impetus LLM Server shortcut on your Desktop
2. Or open it from the Applications folder

The first launch will set up Python dependencies and download a default model.

Visit http://localhost:5173 after starting to access the dashboard." with title "Installation Complete" buttons {"Open Documentation", "OK"} default button "OK"

if button returned of result is "Open Documentation" then
    open location "https://github.com/GerdsenAI/Impetus-LLM-Server#readme"
end if
APPLESCRIPT_EOF

echo "Post-install setup completed"
exit 0
EOF
    
    chmod +x "$SCRIPTS_DIR/postinstall"
    echo "✓ Post-install script created"
}

create_welcome_rtf() {
    print_section "Creating Welcome Document"
    
    cat > "$RESOURCES_DIR/Welcome.rtf" << 'EOF'
{\rtf1\ansi\deff0 {\fonttbl {\f0 Times New Roman;}}
\f0\fs24
{\b\fs28 Welcome to Impetus LLM Server}
\par\par
Thank you for choosing Impetus LLM Server - the high-performance local LLM server optimized for Apple Silicon!
\par\par
{\b What you're installing:}
\par
\u8226 Enterprise-ready LLM server with production features
\par
\u8226 OpenAI-compatible API endpoints
\par
\u8226 Real-time performance monitoring dashboard
\par
\u8226 Optimized for M1, M2, M3, and M4 chips
\par
\u8226 50-110 tokens/sec inference speed
\par\par
{\b System Requirements:}
\par
\u8226 macOS 13.0+ on Apple Silicon
\par
\u8226 Python 3.11+ (will be installed if missing)
\par
\u8226 8GB+ RAM (16GB recommended)
\par
\u8226 10GB+ free disk space
\par\par
{\b After Installation:}
\par
1. Launch Impetus from your Applications folder or Desktop shortcut
\par
2. The first run will set up dependencies and download a model
\par
3. Visit http://localhost:5173 for the dashboard
\par
4. API will be available at http://localhost:8080
\par\par
For support and documentation, visit:
\par
https://github.com/GerdsenAI/Impetus-LLM-Server
}
EOF
    
    echo "✓ Welcome document created"
}

create_license_rtf() {
    print_section "Creating License Document"
    
    cat > "$RESOURCES_DIR/License.rtf" << 'EOF'
{\rtf1\ansi\deff0 {\fonttbl {\f0 Courier New;}}
\f0\fs20
MIT License
\par\par
Copyright (c) 2024 GerdsenAI
\par\par
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
\par\par
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
\par\par
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
}
EOF
    
    echo "✓ License document created"
}

create_distribution_xml() {
    print_section "Creating Distribution Configuration"
    
    cat > "$BUILD_DIR/distribution.xml" << EOF
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="2">
    <title>$PRODUCT_NAME</title>
    <organization>$BUNDLE_ID</organization>
    
    <welcome file="Welcome.rtf"/>
    <license file="License.rtf"/>
    
    <options customize="never" require-scripts="false" hostArchitectures="arm64"/>
    <volume-check>
        <allowed-os-versions>
            <os-version min="13.0"/>
        </allowed-os-versions>
    </volume-check>
    
    <choices-outline>
        <line choice="default">
            <line choice="$BUNDLE_ID"/>
        </line>
    </choices-outline>
    
    <choice id="default"/>
    <choice id="$BUNDLE_ID" visible="false">
        <pkg-ref id="$BUNDLE_ID"/>
    </choice>
    
    <pkg-ref id="$BUNDLE_ID" version="$PRODUCT_VERSION" onConclusion="none">impetus-core.pkg</pkg-ref>
</installer-gui-script>
EOF
    
    echo "✓ Distribution configuration created"
}

build_package() {
    print_section "Building Package"
    
    # Build the component package
    echo "Creating component package..."
    pkgbuild \
        --root "$PAYLOAD_DIR" \
        --scripts "$SCRIPTS_DIR" \
        --identifier "$BUNDLE_ID" \
        --version "$PRODUCT_VERSION" \
        --install-location "/" \
        "$BUILD_DIR/impetus-core.pkg"
    
    # Build the product archive
    echo "Creating product archive..."
    productbuild \
        --distribution "$BUILD_DIR/distribution.xml" \
        --resources "$RESOURCES_DIR" \
        --package-path "$BUILD_DIR" \
        "$PACKAGE_NAME"
    
    # Get package size
    PACKAGE_SIZE=$(ls -lh "$PACKAGE_NAME" | awk '{print $5}')
    echo "✓ Package created: $PACKAGE_NAME ($PACKAGE_SIZE)"
}

sign_package() {
    print_section "Code Signing (Optional)"
    
    # Check if Developer ID certificate is available
    CERT_NAME=$(security find-identity -v -p codesigning | grep "Developer ID Installer" | head -1 | sed 's/.*"\(.*\)".*/\1/')
    
    if [[ -n "$CERT_NAME" ]]; then
        echo "Signing with certificate: $CERT_NAME"
        productsign --sign "$CERT_NAME" "$PACKAGE_NAME" "${PACKAGE_NAME%.pkg}-signed.pkg"
        mv "${PACKAGE_NAME%.pkg}-signed.pkg" "$PACKAGE_NAME"
        echo "✓ Package signed"
    else
        echo "⚠️  No Developer ID certificate found - package will be unsigned"
        echo "   Users will need to right-click and 'Open' to bypass Gatekeeper"
    fi
}

create_dmg() {
    print_section "Creating Disk Image"
    
    DMG_NAME="Impetus-LLM-Server-${PRODUCT_VERSION}.dmg"
    DMG_DIR="$BUILD_DIR/dmg"
    
    # Create DMG directory structure
    mkdir -p "$DMG_DIR"
    cp "$PACKAGE_NAME" "$DMG_DIR/"
    
    # Create README for DMG
    cat > "$DMG_DIR/README.txt" << EOF
Impetus LLM Server v${PRODUCT_VERSION}

Installation Instructions:
1. Double-click the .pkg file to start installation
2. Follow the installation wizard
3. Launch Impetus from Applications folder or Desktop shortcut

For more information, visit:
https://github.com/GerdsenAI/Impetus-LLM-Server

Requirements:
- macOS 13.0+ on Apple Silicon (M1/M2/M3/M4)
- Python 3.11+ (auto-installed if missing)
- 8GB+ RAM, 10GB+ disk space
EOF
    
    # Create DMG
    hdiutil create -srcfolder "$DMG_DIR" -volname "$PRODUCT_NAME" -fs HFS+ -fsargs "-c c=64,a=16,e=16" -format UDZO -imagekey zlib-level=9 "$DMG_NAME"
    
    DMG_SIZE=$(ls -lh "$DMG_NAME" | awk '{print $5}')
    echo "✓ Disk image created: $DMG_NAME ($DMG_SIZE)"
}

cleanup() {
    print_section "Cleaning Up"
    
    # Remove build directory
    rm -rf "$BUILD_DIR"
    
    echo "✓ Build artifacts cleaned up"
}

print_success() {
    print_section "Build Complete!"
    
    cat << EOF

${GREEN}╔════════════════════════════════════════════════════════════╗
║                 🎉 Package Build Successful! 🎉             ║
╚════════════════════════════════════════════════════════════╝${NC}

${BLUE}📦 Created Files:${NC}
─────────────────
• Package: $PACKAGE_NAME
• Disk Image: Impetus-LLM-Server-${PRODUCT_VERSION}.dmg

${BLUE}📋 Distribution Instructions:${NC}
─────────────────────────────
1. Share the .dmg file with users
2. Users double-click the .dmg to mount it
3. Users double-click the .pkg file to install
4. Installation wizard guides them through setup

${BLUE}🔒 Security Notes:${NC}
─────────────────
EOF

    # Check if package is signed
    if pkgutil --check-signature "$PACKAGE_NAME" &>/dev/null; then
        echo "• Package is code-signed and will install without warnings"
    else
        echo "• Package is unsigned - users must right-click and 'Open'"
        echo "• For distribution, consider getting a Developer ID certificate"
    fi

    cat << EOF

${BLUE}🚀 Next Steps:${NC}
─────────────
• Test installation on a clean macOS system
• Distribute via your preferred method
• Consider notarization for wider distribution

${GREEN}✨ macOS installer package ready for distribution! ✨${NC}

EOF
}

# Main build flow
main() {
    print_header
    
    # Parse command line options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-sign)
                SKIP_SIGNING=true
                shift
                ;;
            --no-dmg)
                SKIP_DMG=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --no-sign    Skip code signing step"
                echo "  --no-dmg     Skip DMG creation"
                echo "  --help       Show this help"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    check_requirements
    create_build_structure
    prepare_payload
    create_preinstall_script
    create_postinstall_script
    create_welcome_rtf
    create_license_rtf
    create_distribution_xml
    build_package
    
    if [[ "$SKIP_SIGNING" != true ]]; then
        sign_package
    fi
    
    if [[ "$SKIP_DMG" != true ]]; then
        create_dmg
    fi
    
    cleanup
    print_success
}

# Run main function
main "$@"