#!/bin/bash
#
# Impetus LLM Server - Simple DMG Creator
# Creates a functional DMG installer with basic layout
#

set -e

# Configuration
PRODUCT_NAME="Impetus"
PRODUCT_VERSION="1.0.2"
APP_NAME="Impetus.app"
DMG_NAME="Impetus-${PRODUCT_VERSION}-arm64.dmg"

# Directories
BUILD_DIR="./build_dmg"
APP_DIR="$BUILD_DIR/$APP_NAME"

# Clean and create build directory
echo "🧹 Cleaning build directory..."
rm -rf "$BUILD_DIR" "$DMG_NAME"
mkdir -p "$BUILD_DIR"

# First, let's just create a minimal app bundle for testing
echo "📦 Creating minimal app bundle..."
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Copy basic Info.plist
cp "installers/assets/Info.plist" "$APP_DIR/Contents/"

# Copy icon
cp "installers/assets/AppIcon.icns" "$APP_DIR/Contents/Resources/"

# Create a simple launcher
cat > "$APP_DIR/Contents/MacOS/Impetus" << 'EOF'
#!/bin/bash
echo "Impetus LLM Server"
osascript -e 'display dialog "Impetus LLM Server\n\nThis is a test installation.\nThe full version would launch the AI server here." with title "Impetus" buttons {"OK"} default button "OK" with icon note'
EOF

chmod +x "$APP_DIR/Contents/MacOS/Impetus"

# Copy application code
echo "📁 Copying application code..."
cp -r gerdsen_ai_server "$APP_DIR/Contents/Resources/"
cp run_menubar.py "$APP_DIR/Contents/Resources/" 2>/dev/null || echo "Note: run_menubar.py not found"

echo "💿 Creating DMG..."

# Create the DMG directly from the build directory
hdiutil create -srcfolder "$BUILD_DIR" -volname "Impetus" \
    -fs HFS+ -format UDZO -imagekey zlib-level=9 \
    "$DMG_NAME"

echo "✅ DMG created: $DMG_NAME"

# Get file size
dmg_size=$(ls -lh "$DMG_NAME" | awk '{print $5}')
echo "📏 DMG size: $dmg_size"

# Clean up
rm -rf "$BUILD_DIR"

echo "🎉 Simple DMG creation completed!"
echo "📋 To test: Double-click $DMG_NAME and drag Impetus.app to Applications"