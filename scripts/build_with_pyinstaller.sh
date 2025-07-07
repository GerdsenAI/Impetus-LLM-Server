#!/bin/bash
# Build script for Impetus Tray App using PyInstaller
# This script creates a standalone application for the headless tray app

set -e  # Exit on any error

APP_NAME="Impetus"
APP_VERSION="2.0.0"
BUILD_DIR="build"
DIST_DIR="dist"

echo "🚀 Building $APP_NAME v$APP_VERSION for macOS using PyInstaller"
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
    pip install flask flask-socketio flask-cors psutil pystray Pillow requests numpy pandas
fi

# Install PyInstaller if not already installed
echo "📱 Installing PyInstaller..."
pip install pyinstaller

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf "$BUILD_DIR/$APP_NAME" "$DIST_DIR/$APP_NAME"

# Create assets directory if it doesn't exist
mkdir -p assets

# Create a simple icon if it doesn't exist
if [ ! -f "assets/icon.png" ]; then
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
fi

# Build the application with PyInstaller
echo "🔨 Building application bundle with PyInstaller..."
pyinstaller --name="$APP_NAME" \
            --windowed \
            --icon=assets/icon.png \
            --add-data="assets:assets" \
            --add-data="src:src" \
            --add-data="ui:ui" \
            --hidden-import=pystray \
            --hidden-import=PIL \
            --hidden-import=PIL._imaging \
            --hidden-import=PIL.Image \
            --hidden-import=PIL.ImageDraw \
            --hidden-import=PIL.ImageFont \
            --hidden-import=PIL.ImageTk \
            --hidden-import=flask \
            --hidden-import=flask_socketio \
            --hidden-import=flask_cors \
            --collect-all=PIL \
            impetus_tray.py

# Check if build was successful
if [ -d "dist/$APP_NAME.app" ]; then
    echo "✅ Build successful!"
    echo "📁 Application bundle created: dist/$APP_NAME.app"
    
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
    echo "The app will appear in the menu bar with the Impetus icon"
    
else
    echo "❌ Build failed!"
    echo "Check the error messages above for details."
    exit 1
fi

# Deactivate virtual environment
deactivate

echo "🏁 Build process completed!"
