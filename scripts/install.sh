#!/bin/bash
# GerdsenAI MLX Model Manager Installation Script

set -e

echo "🚀 Installing GerdsenAI MLX Model Manager"
echo "========================================"

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This application is designed for macOS with Apple Silicon"
    exit 1
fi

# Check for Apple Silicon
if [[ $(uname -m) != "arm64" ]]; then
    echo "⚠️  Warning: This application is optimized for Apple Silicon (M1/M2/M3)"
    echo "   It may not perform optimally on Intel Macs"
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [[ $(echo "$python_version >= $required_version" | bc -l) -eq 0 ]]; then
    echo "❌ Python 3.8+ is required. Found: $python_version"
    echo "   Please install Python 3.8 or later"
    exit 1
fi

echo "✅ Python $python_version detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install MLX framework
echo "🔧 Installing MLX framework..."
pip install mlx mlx-lm

# Install other requirements
echo "📋 Installing requirements..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p ~/.gerdsen_ai_cache/memory_maps
mkdir -p ~/Library/Logs/GerdsenAI

# Set permissions
chmod +x src/integrated_gerdsen_ai.py
chmod +x installer/drag_drop_installer.py

# Create app bundle (optional)
read -p "🍎 Create macOS app bundle? (y/n): " create_bundle
if [[ $create_bundle == "y" || $create_bundle == "Y" ]]; then
    echo "🔨 Creating app bundle..."
    python installer/drag_drop_installer.py
    echo "✅ App bundle created in installer/output/"
fi

# Create desktop shortcut
read -p "🖥️  Create desktop shortcut? (y/n): " create_shortcut
if [[ $create_shortcut == "y" || $create_shortcut == "Y" ]]; then
    cat > ~/Desktop/GerdsenAI.command << EOF
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python src/integrated_gerdsen_ai.py
EOF
    chmod +x ~/Desktop/GerdsenAI.command
    echo "✅ Desktop shortcut created"
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "🚀 To start GerdsenAI MLX Model Manager:"
echo "   source venv/bin/activate"
echo "   python src/integrated_gerdsen_ai.py"
echo ""
echo "📚 Documentation: docs/README.md"
echo "🔧 Configuration: ~/.gerdsen_ai_config.json"
echo "📊 Logs: ~/Library/Logs/GerdsenAI/"
echo ""
echo "Enjoy your enhanced AI model management experience! 🎯"

