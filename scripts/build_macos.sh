#!/bin/bash
# Build script for GerdsenAI MLX Manager on macOS
# This script creates a proper .app bundle for distribution

set -e  # Exit on any error

APP_NAME="GerdsenAI MLX Manager"
APP_VERSION="2.0.0"
BUILD_DIR="build"
DIST_DIR="dist"

echo "🚀 Building $APP_NAME v$APP_VERSION for macOS"
echo "=================================================="

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [[ $(echo "$PYTHON_VERSION >= $REQUIRED_VERSION" | bc -l) -eq 0 ]]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing requirements..."
if [ -f "requirements_macos.txt" ]; then
    pip install -r requirements_macos.txt
else
    echo "⚠️  requirements_macos.txt not found, installing basic requirements..."
    pip install flask flask-socketio flask-cors psutil rumps pystray Pillow requests numpy pandas
fi

# Install py2app if not already installed
echo "📱 Installing py2app..."
pip install py2app

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR"

# Create assets directory if it doesn't exist
mkdir -p assets

# Create a simple icon if it doesn't exist
if [ ! -f "assets/icon.icns" ]; then
    echo "🎨 Creating application icon..."
    
    # Create a simple PNG icon first
    python3 -c "
from PIL import Image, ImageDraw
import os

# Create a 512x512 icon with gradient
img = Image.new('RGB', (512, 512), color='#1a1a1a')
draw = ImageDraw.Draw(img)

# Draw a brain-like icon
center = (256, 256)
radius = 200

# Draw circles for brain lobes
draw.ellipse([center[0]-radius, center[1]-radius//2, center[0]+radius//3, center[1]+radius//2], fill='#007AFF')
draw.ellipse([center[0]-radius//3, center[1]-radius//2, center[0]+radius, center[1]+radius//2], fill='#0056CC')

# Add some neural network lines
for i in range(0, 360, 30):
    import math
    x1 = center[0] + (radius//2) * math.cos(math.radians(i))
    y1 = center[1] + (radius//2) * math.sin(math.radians(i))
    x2 = center[0] + (radius//3) * math.cos(math.radians(i+60))
    y2 = center[1] + (radius//3) * math.sin(math.radians(i+60))
    draw.line([x1, y1, x2, y2], fill='#FFFFFF', width=3)

img.save('assets/icon.png')
print('Created icon.png')
"

    # Convert PNG to ICNS using sips (macOS built-in tool)
    if command -v sips >/dev/null 2>&1; then
        echo "🔄 Converting PNG to ICNS..."
        mkdir -p icon.iconset
        
        # Create different sizes for the iconset
        sips -z 16 16 assets/icon.png --out icon.iconset/icon_16x16.png
        sips -z 32 32 assets/icon.png --out icon.iconset/icon_16x16@2x.png
        sips -z 32 32 assets/icon.png --out icon.iconset/icon_32x32.png
        sips -z 64 64 assets/icon.png --out icon.iconset/icon_32x32@2x.png
        sips -z 128 128 assets/icon.png --out icon.iconset/icon_128x128.png
        sips -z 256 256 assets/icon.png --out icon.iconset/icon_128x128@2x.png
        sips -z 256 256 assets/icon.png --out icon.iconset/icon_256x256.png
        sips -z 512 512 assets/icon.png --out icon.iconset/icon_256x256@2x.png
        sips -z 512 512 assets/icon.png --out icon.iconset/icon_512x512.png
        cp assets/icon.png icon.iconset/icon_512x512@2x.png
        
        # Create ICNS file
        iconutil -c icns icon.iconset
        mv icon.icns assets/
        rm -rf icon.iconset
        
        echo "✅ Created assets/icon.icns"
    else
        echo "⚠️  sips not available, using PNG icon"
        cp assets/icon.png assets/icon.icns
    fi
fi

# Build the application
echo "🔨 Building application bundle..."
python3 setup_macos.py py2app

# Check if build was successful
if [ -d "dist/$APP_NAME.app" ]; then
    echo "✅ Build successful!"
    echo "📁 Application bundle created: dist/$APP_NAME.app"
    
    # Make the app executable
    chmod +x "dist/$APP_NAME.app/Contents/MacOS/$APP_NAME"
    
    # Create a DMG for distribution (optional)
    if command -v hdiutil >/dev/null 2>&1; then
        echo "📦 Creating DMG for distribution..."
        DMG_NAME="$APP_NAME-$APP_VERSION.dmg"
        
        # Create temporary DMG directory
        mkdir -p dmg_temp
        cp -R "dist/$APP_NAME.app" dmg_temp/
        
        # Create Applications symlink
        ln -s /Applications dmg_temp/Applications
        
        # Create DMG
        hdiutil create -volname "$APP_NAME" -srcfolder dmg_temp -ov -format UDZO "$DMG_NAME"
        
        # Clean up
        rm -rf dmg_temp
        
        echo "✅ DMG created: $DMG_NAME"
    fi
    
    echo ""
    echo "🎉 Build completed successfully!"
    echo "=================================================="
    echo "📱 Application: dist/$APP_NAME.app"
    echo "📦 Installer: $DMG_NAME (if created)"
    echo ""
    echo "To install:"
    echo "1. Copy the .app to /Applications/"
    echo "2. Or run: cp -R 'dist/$APP_NAME.app' /Applications/"
    echo ""
    echo "To run:"
    echo "1. Launch from Applications folder"
    echo "2. Or run: open 'dist/$APP_NAME.app'"
    echo ""
    echo "The app will appear in the menu bar with a brain icon 🧠"
    
else
    echo "❌ Build failed!"
    echo "Check the error messages above for details."
    exit 1
fi

# Deactivate virtual environment
deactivate

echo "🏁 Build process completed!"

