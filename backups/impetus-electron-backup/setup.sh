#!/bin/bash

# IMPETUS Electron App Setup Script
# Intelligent Model Platform Enabling Taskbar Unified Server

echo "🚀 Setting up IMPETUS Electron App..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not available"
    exit 1
fi

echo "✅ npm $(npm -v) detected"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Check if Python virtual environment exists
if [ -f "../venv/bin/python" ]; then
    echo "✅ Python virtual environment detected"
else
    echo "⚠️  Python virtual environment not found at ../venv/"
    echo "   Make sure to set up the IMPETUS server first"
fi

echo ""
echo "🎉 IMPETUS Electron App setup complete!"
echo ""
echo "Available commands:"
echo "  npm start              - Start the app"
echo "  npm run dev            - Start with hot reload"
echo "  npm run build          - Build for production"
echo "  npm run bundle-python  - Bundle Python environment"
echo "  npm run test-bundle    - Test bundled Python environment"
echo "  npm run dist-with-python - Create distributable with Python bundle"
echo ""
echo "To start the app:"
echo "  cd impetus-electron"
echo "  npm start"
echo ""
echo "For development, make sure the IMPETUS server virtual environment is set up:"
echo "  cd .."
echo "  python -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements_production.txt"
echo ""
echo "For distribution, create a Python bundle:"
echo "  cd impetus-electron"
echo "  npm run bundle-python"
echo "  npm run dist-with-python"