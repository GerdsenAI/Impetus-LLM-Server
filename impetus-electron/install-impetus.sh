#!/bin/bash
echo "📦 Installing Impetus..."

# Remove old version if exists
if [ -d "/Applications/Impetus.app" ]; then
    echo "🗑️  Removing old version..."
    rm -rf /Applications/Impetus.app
fi

# Copy new version
cp -r dist/mac-arm64/Impetus.app /Applications/
echo "✅ Impetus installed to Applications!"
echo "🎉 The app now includes a bundled Python environment - no external Python required!"
echo "🚀 You can now launch Impetus from your Applications folder"
