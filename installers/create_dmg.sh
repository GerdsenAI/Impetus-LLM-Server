#!/bin/bash
#
# Impetus LLM Server - Professional DMG Installer Creator
# Creates a beautiful drag-and-drop DMG installer for macOS
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PRODUCT_NAME="Impetus"
PRODUCT_VERSION="1.0.2"
BUNDLE_ID="com.gerdsenai.impetus"
APP_NAME="Impetus.app"
DMG_NAME="Impetus-${PRODUCT_VERSION}-arm64.dmg"
TEMP_DMG_NAME="Impetus-temp.dmg"

# Directories
BUILD_DIR="./build_dmg"
APP_DIR="$BUILD_DIR/$APP_NAME"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
FRAMEWORKS_DIR="$CONTENTS_DIR/Frameworks"

# Assets
ASSETS_DIR="./installers/assets"
SCRIPTS_DIR="./installers/scripts"
ICON_FILE="$ASSETS_DIR/AppIcon.icns"
BACKGROUND_IMAGE="$ASSETS_DIR/dmg-background.png"
INFO_PLIST="$ASSETS_DIR/Info.plist"
LAUNCHER_SCRIPT="$SCRIPTS_DIR/launcher.sh"
FIRST_RUN_SCRIPT="$SCRIPTS_DIR/first_run.py"

# DMG configuration
DMG_WINDOW_WIDTH=600
DMG_WINDOW_HEIGHT=400
DMG_ICON_SIZE=80
DMG_TEXT_SIZE=12

# Icon positions (x, y)
APP_ICON_X=150
APP_ICON_Y=200
APPLICATIONS_ICON_X=450
APPLICATIONS_ICON_Y=200

# Functions
print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║          Impetus LLM Server - DMG Creator               ║"
    echo "║             Professional macOS Installer                ║"
    echo "║                                                          ║"
    echo "║  Creates beautiful drag-and-drop installer DMG          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────────"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_requirements() {
    print_section "Checking Build Requirements"
    
    # Check macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This script must be run on macOS"
        exit 1
    fi
    
    # Check architecture
    if [[ $(uname -m) != "arm64" ]]; then
        print_error "This script requires Apple Silicon (M1/M2/M3/M4)"
        exit 1
    fi
    
    # Check if running from project root
    if [[ ! -f "gerdsen_ai_server/src/main.py" ]]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Check for required tools
    local required_tools=("hdiutil" "python3" "osascript")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            print_error "Required tool '$tool' not found"
            exit 1
        fi
    done
    
    # Check for assets
    if [[ ! -f "$ICON_FILE" ]]; then
        print_warning "App icon not found, creating it..."
        if ! python3 installers/create_icon.py; then
            print_error "Failed to create app icon"
            exit 1
        fi
    fi
    
    if [[ ! -f "$BACKGROUND_IMAGE" ]]; then
        print_warning "DMG background not found, creating it..."
        if ! python3 installers/create_dmg_background.py; then
            print_error "Failed to create DMG background"
            exit 1
        fi
    fi
    
    print_success "Build requirements met"
}

clean_build_directory() {
    print_section "Cleaning Build Directory"
    
    if [[ -d "$BUILD_DIR" ]]; then
        rm -rf "$BUILD_DIR"
        print_success "Cleaned existing build directory"
    fi
    
    mkdir -p "$BUILD_DIR"
    print_success "Created fresh build directory"
}

create_app_bundle() {
    print_section "Creating App Bundle Structure"
    
    # Create bundle directories
    mkdir -p "$MACOS_DIR"
    mkdir -p "$RESOURCES_DIR"
    mkdir -p "$FRAMEWORKS_DIR"
    
    print_success "Created bundle directory structure"
    
    # Copy Info.plist
    cp "$INFO_PLIST" "$CONTENTS_DIR/"
    print_success "Copied Info.plist"
    
    # Copy app icon
    cp "$ICON_FILE" "$RESOURCES_DIR/"
    print_success "Copied app icon"
    
    # Copy launcher script as main executable
    cp "$LAUNCHER_SCRIPT" "$MACOS_DIR/Impetus"
    chmod +x "$MACOS_DIR/Impetus"
    print_success "Installed launcher script"
    
    # Copy first run setup script
    cp "$FIRST_RUN_SCRIPT" "$RESOURCES_DIR/"
    chmod +x "$RESOURCES_DIR/first_run.py"
    print_success "Copied first-run setup script"
}

bundle_python_runtime() {
    print_section "Bundling Python Runtime"
    
    # Check if we have a virtual environment
    if [[ -d ".venv" ]]; then
        print_success "Found virtual environment, bundling dependencies..."
        
        # Create proper Python runtime directory structure
        PYTHON_RUNTIME_DIR="$FRAMEWORKS_DIR/Python.framework/Versions/Current"
        mkdir -p "$PYTHON_RUNTIME_DIR/bin"
        mkdir -p "$PYTHON_RUNTIME_DIR/lib"
        
        # Create simple symlink to system Python (PYTHONPATH will handle isolation)
        ln -sf "$(command -v python3)" "$PYTHON_RUNTIME_DIR/bin/python3"
        print_success "Linked to system Python (using PYTHONPATH for isolation)"
        
        # Find and copy the correct site-packages directory
        VENV_SITE_PACKAGES=$(find .venv -name "site-packages" -type d | head -1)
        if [[ -n "$VENV_SITE_PACKAGES" ]]; then
            # Create the proper Python version directory structure
            PYTHON_VERSION=$(python3 -c "import sys; print(f'python{sys.version_info.major}.{sys.version_info.minor}')")
            SITE_PACKAGES_DIR="$PYTHON_RUNTIME_DIR/lib/$PYTHON_VERSION/site-packages"
            mkdir -p "$SITE_PACKAGES_DIR"
            
            # Copy all site-packages content
            cp -r "$VENV_SITE_PACKAGES"/* "$SITE_PACKAGES_DIR/"
            print_success "Bundled Python libraries from $VENV_SITE_PACKAGES"
            
            # Verify Flask is bundled
            if [[ -d "$SITE_PACKAGES_DIR/flask" ]]; then
                print_success "Verified Flask is bundled"
            else
                print_warning "Flask not found in bundled packages"
            fi
        else
            print_warning "No site-packages directory found in virtual environment"
        fi
        
        # Install dependencies from requirements.txt if site-packages copy failed
        if [[ ! -d "$PYTHON_RUNTIME_DIR/lib/$PYTHON_VERSION/site-packages/flask" ]] && [[ -f "gerdsen_ai_server/requirements.txt" ]]; then
            print_warning "Installing dependencies directly into bundle..."
            PYTHONPATH="$PYTHON_RUNTIME_DIR/lib/$PYTHON_VERSION/site-packages" \
            "$PYTHON_RUNTIME_DIR/bin/python3" -m pip install --target "$PYTHON_RUNTIME_DIR/lib/$PYTHON_VERSION/site-packages" \
                -r gerdsen_ai_server/requirements.txt --no-deps --quiet
            print_success "Installed dependencies into bundle"
        fi
    else
        print_error "No virtual environment found. Please activate virtual environment and install dependencies first."
        print_error "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r gerdsen_ai_server/requirements.txt"
        exit 1
    fi
}

bundle_application_code() {
    print_section "Bundling Application Code"
    
    # Copy the entire application
    cp -r gerdsen_ai_server "$RESOURCES_DIR/"
    print_success "Copied application code"
    
    # Copy menu bar script
    cp run_menubar.py "$RESOURCES_DIR/"
    print_success "Copied menu bar application"
    
    # Copy requirements file
    if [[ -f "gerdsen_ai_server/requirements.txt" ]]; then
        cp gerdsen_ai_server/requirements.txt "$RESOURCES_DIR/"
        print_success "Copied requirements file"
    fi
    
    # Create models directory
    mkdir -p "$RESOURCES_DIR/models"
    echo "# AI models will be downloaded here" > "$RESOURCES_DIR/models/README.txt"
    print_success "Created models directory"
    
    # Copy documentation
    if [[ -f "README.md" ]]; then
        cp README.md "$RESOURCES_DIR/"
        print_success "Copied documentation"
    fi
    
    # Remove unnecessary files
    find "$RESOURCES_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$RESOURCES_DIR" -name "*.pyc" -type f -delete 2>/dev/null || true
    find "$RESOURCES_DIR" -name ".DS_Store" -type f -delete 2>/dev/null || true
    print_success "Cleaned up temporary files"
}

create_temp_dmg() {
    print_section "Creating Temporary DMG"
    
    # Calculate DMG size (app bundle size + 200MB buffer for customization)
    local app_size=$(du -sm "$APP_DIR" | cut -f1)
    local dmg_size=$((app_size + 200))
    
    print_success "App size: ${app_size}MB, DMG size: ${dmg_size}MB"
    
    # Create temporary DMG with more space  
    hdiutil create -volname "Impetus" -fs HFS+ \
           -type UDIF -size "${dmg_size}m" \
           -ov "$BUILD_DIR/$TEMP_DMG_NAME"
    
    print_success "Created temporary DMG"
}

customize_dmg() {
    print_section "Customizing DMG Appearance"
    
    # Mount the temporary DMG
    local mount_output=$(hdiutil attach -readwrite -noverify -nobrowse \
                        "$BUILD_DIR/$TEMP_DMG_NAME" 2>&1)
    local mount_point=$(echo "$mount_output" | grep -E '/Volumes/' | \
                       sed 1q | awk '{print $3}')
    
    if [[ -z "$mount_point" ]]; then
        print_error "Failed to mount temporary DMG"
        echo "Mount output: $mount_output"
        exit 1
    fi
    
    print_success "Mounted DMG at: $mount_point"
    
    # Copy the app bundle to the mounted DMG
    cp -R "$APP_DIR" "$mount_point/"
    print_success "Copied app bundle to DMG"
    
    # Create Applications symlink
    ln -sf /Applications "$mount_point/Applications"
    print_success "Created Applications symlink"
    
    # Copy background image
    mkdir -p "$mount_point/.background"
    cp "$BACKGROUND_IMAGE" "$mount_point/.background/background.png"
    print_success "Copied background image"
    
    # Set custom icon for the volume
    cp "$ICON_FILE" "$mount_point/.VolumeIcon.icns"
    SetFile -c icnC "$mount_point/.VolumeIcon.icns"
    SetFile -a C "$mount_point"
    print_success "Set volume icon"
    
    # Configure Finder view options using AppleScript
    osascript <<EOF
        tell application "Finder"
            tell disk "Impetus"
                open
                set current view of container window to icon view
                set toolbar visible of container window to false
                set statusbar visible of container window to false
                set the bounds of container window to {100, 100, $((100 + DMG_WINDOW_WIDTH)), $((100 + DMG_WINDOW_HEIGHT))}
                set viewOptions to the icon view options of container window
                set arrangement of viewOptions to not arranged
                set icon size of viewOptions to $DMG_ICON_SIZE
                set text size of viewOptions to $DMG_TEXT_SIZE
                set background picture of viewOptions to file ".background:background.png"
                set position of item "Impetus.app" of container window to {$APP_ICON_X, $APP_ICON_Y}
                set position of item "Applications" of container window to {$APPLICATIONS_ICON_X, $APPLICATIONS_ICON_Y}
                close
                open
                update without registering applications
                delay 2
            end tell
        end tell
EOF
    
    print_success "Configured DMG window layout"
    
    # Ensure the background image is hidden
    SetFile -a V "$mount_point/.background/background.png"
    
    # Unmount the DMG
    hdiutil detach "$mount_point"
    print_success "Unmounted DMG"
}

create_final_dmg() {
    print_section "Creating Final DMG"
    
    # Convert to compressed read-only format
    hdiutil convert "$BUILD_DIR/$TEMP_DMG_NAME" -format UDZO \
           -imagekey zlib-level=9 -o "$BUILD_DIR/$DMG_NAME"
    
    # Remove temporary DMG
    rm "$BUILD_DIR/$TEMP_DMG_NAME"
    
    # Move final DMG to project root
    mv "$BUILD_DIR/$DMG_NAME" "./"
    
    print_success "Created final DMG: $DMG_NAME"
}

verify_dmg() {
    print_section "Verifying DMG"
    
    # Verify DMG integrity
    if hdiutil verify "$DMG_NAME"; then
        print_success "DMG verification passed"
    else
        print_error "DMG verification failed"
        exit 1
    fi
    
    # Get DMG info
    local dmg_size=$(ls -lh "$DMG_NAME" | awk '{print $5}')
    print_success "DMG size: $dmg_size"
    
    # Test mounting
    local test_mount=$(hdiutil attach -readonly -nobrowse "$DMG_NAME" | \
                      grep -E '^/dev/' | sed 1q | awk '{print $3}')
    
    if [[ -n "$test_mount" ]]; then
        print_success "DMG mounts successfully"
        
        # Check if app exists
        if [[ -d "$test_mount/Impetus.app" ]]; then
            print_success "App bundle found in DMG"
        else
            print_error "App bundle not found in DMG"
        fi
        
        # Check Applications symlink
        if [[ -L "$test_mount/Applications" ]]; then
            print_success "Applications symlink found"
        else
            print_error "Applications symlink not found"
        fi
        
        # Unmount test
        hdiutil detach "$test_mount" &>/dev/null
        print_success "Test mount/unmount successful"
    else
        print_error "Failed to test mount DMG"
        exit 1
    fi
}

cleanup_build() {
    print_section "Cleaning Up"
    
    # Remove build directory
    rm -rf "$BUILD_DIR"
    print_success "Removed build directory"
}

show_completion_message() {
    print_section "Build Complete!"
    
    echo -e "${GREEN}"
    echo "🎉 DMG Installer Created Successfully!"
    echo ""
    echo "📦 File: $DMG_NAME"
    echo "📏 Size: $(ls -lh "$DMG_NAME" | awk '{print $5}')"
    echo "🏷️  Version: $PRODUCT_VERSION"
    echo ""
    echo "📋 Installation Instructions:"
    echo "  1. Double-click $DMG_NAME to mount"
    echo "  2. Drag Impetus.app to Applications folder"
    echo "  3. Launch Impetus from Applications"
    echo "  4. Look for 🧠 icon in menu bar"
    echo ""
    echo "🚀 The installer is ready for distribution!"
    echo -e "${NC}"
}

# Main execution
main() {
    print_header
    
    check_requirements
    clean_build_directory
    create_app_bundle
    bundle_python_runtime
    bundle_application_code
    create_temp_dmg
    customize_dmg
    create_final_dmg
    verify_dmg
    cleanup_build
    show_completion_message
    
    echo -e "${CYAN}🧠 Impetus DMG creation completed successfully!${NC}"
}

# Handle script interruption
trap 'echo -e "\n${RED}❌ Build interrupted by user${NC}"; exit 130' SIGINT SIGTERM

# Run main function
main "$@"