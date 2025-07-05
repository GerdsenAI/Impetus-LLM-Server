#!/bin/bash

# IMPETUS Electron App Build Script
# Creates a production-ready macOS application

echo "🚀 Building IMPETUS for macOS..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Must run from impetus-electron directory"
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist out

# Option 1: Build without Python bundle (faster, requires Python on user's system)
build_without_python() {
    echo "📦 Building Electron app without Python bundle..."
    npm run build
    
    if [ $? -eq 0 ]; then
        echo "✅ Build complete!"
        echo "📁 App location: dist/mac/IMPETUS.app"
        echo ""
        echo "To install: cp -r dist/mac*/IMPETUS.app /Applications/"
    else
        echo "❌ Build failed"
        exit 1
    fi
}

# Option 2: Build with Python bundle (self-contained, larger)
build_with_python() {
    echo "🐍 Building with Python bundle (this may take several minutes)..."
    
    # First, let's skip the Python bundling for now and just build the app
    echo "⚠️  Skipping Python bundling for faster build..."
    echo "📦 Building Electron app..."
    
    npm run build
    
    if [ $? -eq 0 ]; then
        echo "✅ Build complete!"
        echo "📁 App location: dist/mac*/IMPETUS.app"
        echo ""
        echo "To install: cp -r dist/mac*/IMPETUS.app /Applications/"
        echo ""
        echo "Note: This build requires Python to be installed on the target system."
        echo "For a fully self-contained build, we would need to bundle Python."
    else
        echo "❌ Build failed"
        exit 1
    fi
}

# Create a simple icon if it doesn't exist
if [ ! -f "resources/icon.icns" ]; then
    echo "🎨 Creating placeholder icon..."
    # Create a simple icon using macOS tools
    mkdir -p resources
    
    # Create a simple PNG with sips (macOS built-in)
    echo "🚀" | convert -background transparent -fill black -font Arial -pointsize 512 label:@- resources/icon.png 2>/dev/null || {
        # If convert is not available, create an empty icon file
        touch resources/icon.icns
        echo "⚠️  No icon created (imagemagick not installed)"
    }
    
    # Convert PNG to ICNS if we created a PNG
    if [ -f "resources/icon.png" ]; then
        sips -s format icns resources/icon.png --out resources/icon.icns 2>/dev/null || {
            touch resources/icon.icns
        }
        rm resources/icon.png
    fi
fi

# Ask user which build type
echo ""
echo "Select build type:"
echo "1) Quick build (without Python bundle)"
echo "2) Full build (with Python bundle) - NOT IMPLEMENTED YET"
echo ""
read -p "Choice (1 or 2): " choice

case $choice in
    1)
        build_without_python
        ;;
    2)
        echo "⚠️  Full Python bundling not yet implemented"
        echo "   Using quick build instead..."
        build_without_python
        ;;
    *)
        echo "Invalid choice, using quick build"
        build_without_python
        ;;
esac