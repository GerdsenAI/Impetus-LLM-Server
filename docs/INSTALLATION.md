# Installation Guide

This guide provides step-by-step instructions for installing and configuring GerdsenAI MLX Manager Enhanced on macOS 15+.

## Prerequisites

### System Requirements
- **Operating System**: macOS 15.0 (Sequoia) or later
- **Hardware**: Apple Silicon Mac (M1, M2, M3, or M4 series)
- **RAM**: 8GB minimum, 16GB+ recommended for optimal performance
- **Storage**: 2GB free space for application and dependencies
- **Network**: Internet connection for initial setup and optional model downloads

### Required Software
- **Xcode Command Line Tools**: Required for compiling native extensions
- **Python 3.11+**: Usually pre-installed on macOS 15+
- **Homebrew**: Recommended for managing additional dependencies

## Installation Methods

### Method 1: Automated Installation (Recommended)

This is the easiest way to install GerdsenAI MLX Manager Enhanced.

#### Step 1: Download and Extract
```bash
# Download the application (replace with actual download URL)
curl -L -o gerdsen-ai-enhanced.zip https://github.com/your-repo/gerdsen-ai-enhanced/archive/main.zip

# Extract the archive
unzip gerdsen-ai-enhanced.zip
cd gerdsen-ai-enhanced-main
```

#### Step 2: Run Automated Installer
```bash
# Make the installer executable
chmod +x scripts/build_macos.sh

# Run the installer (this will handle all dependencies)
./scripts/build_macos.sh
```

#### Step 3: Launch Application
```bash
# Start the application
python3 gerdsen_ai_launcher.py

# Or start as a background service
python3 gerdsen_ai_launcher.py --service
```

### Method 2: Manual Installation

For users who prefer more control over the installation process.

#### Step 1: Install System Dependencies
```bash
# Install Xcode Command Line Tools (if not already installed)
xcode-select --install

# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11+ (if needed)
brew install python@3.11
```

#### Step 2: Clone Repository
```bash
# Clone the repository
git clone https://github.com/your-repo/gerdsen-ai-enhanced.git
cd gerdsen-ai-enhanced
```

#### Step 3: Set Up Python Environment
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install -r requirements_production.txt
```

#### Step 4: Install Apple Frameworks (Optional but Recommended)
```bash
# Install MLX for advanced AI acceleration
pip install mlx

# Install Core ML Tools for model optimization
pip install coremltools

# Install PyObjC frameworks for native macOS integration
pip install pyobjc-framework-Metal pyobjc-framework-CoreML pyobjc-framework-Foundation
```

#### Step 5: Configure Application
```bash
# Run setup script
python3 setup_macos.py

# Create configuration directory
mkdir -p config logs models

# Copy default configuration
cp config/default.json config/production.json
```

#### Step 6: Build Application Bundle (Optional)
```bash
# Install py2app for creating macOS application bundles
pip install py2app

# Build application bundle
python3 setup_macos.py py2app

# The application will be created in dist/GerdsenAI.app
```

### Method 3: Development Installation

For developers who want to contribute or modify the application.

#### Step 1: Development Dependencies
```bash
# Clone repository
git clone https://github.com/your-repo/gerdsen-ai-enhanced.git
cd gerdsen-ai-enhanced

# Create development environment
python3 -m venv dev-env
source dev-env/bin/activate

# Install development dependencies
pip install -r requirements_production.txt
pip install -r requirements_dev.txt  # If available

# Install in development mode
pip install -e .
```

#### Step 2: Set Up Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install
```

#### Step 3: Run Tests
```bash
# Run test suite
python3 -m pytest tests/

# Run functionality validation
python3 validate_functionality.py

# Run performance benchmarks
python3 tests/benchmark_performance.py
```

## Configuration

### Basic Configuration

#### Environment Variables
Add these to your shell profile (`~/.zshrc` or `~/.bash_profile`):

```bash
# GerdsenAI Configuration
export GERDSEN_AI_PORT=8080
export GERDSEN_AI_HOST=0.0.0.0
export GERDSEN_AI_API_KEY=gerdsen-ai-local-key
export GERDSEN_AI_LOG_LEVEL=INFO
export GERDSEN_AI_ENABLE_CORS=true
export GERDSEN_AI_MODEL_PATH=/Users/$USER/Documents/GerdsenAI/models
```

#### Configuration File
Create or edit `config/production.json`:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false,
    "workers": 4,
    "timeout": 300
  },
  "optimization": {
    "auto_optimize": true,
    "thermal_management": true,
    "performance_mode": "balanced",
    "max_memory_usage": 0.8,
    "enable_neural_engine": true
  },
  "api": {
    "enable_openai_compat": true,
    "rate_limiting": true,
    "max_requests_per_minute": 60,
    "cors_enabled": true,
    "allowed_origins": ["*"]
  },
  "models": {
    "auto_download": false,
    "cache_size_gb": 10,
    "optimization_level": "balanced",
    "quantization": "auto"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/gerdsen_ai.log",
    "max_size_mb": 100,
    "backup_count": 5
  }
}
```

### Advanced Configuration

#### Custom Model Paths
```bash
# Create model directories
mkdir -p ~/Documents/GerdsenAI/models/{coreml,mlx,custom}

# Set permissions
chmod 755 ~/Documents/GerdsenAI/models
```

#### Service Configuration
To run as a macOS service, create a launch agent:

```xml
<!-- ~/Library/LaunchAgents/com.gerdsen.ai.mlx.manager.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gerdsen.ai.mlx.manager</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/gerdsen-ai-enhanced/gerdsen_ai_launcher.py</string>
        <string>--service</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/path/to/gerdsen-ai-enhanced</string>
    <key>StandardOutPath</key>
    <string>/tmp/gerdsen-ai-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/gerdsen-ai-stderr.log</string>
</dict>
</plist>
```

Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.gerdsen.ai.mlx.manager.plist
launchctl start com.gerdsen.ai.mlx.manager
```

## VS Code Integration

### Step 1: Install Compatible Extension
Install one of these VS Code extensions:
- **Cline** (recommended)
- **Continue**
- **CodeGPT**
- **Any OpenAI-compatible extension**

### Step 2: Configure Extension
In VS Code settings, configure the extension to use the local API:

#### For Cline:
```json
{
  "cline.apiProvider": "openai",
  "cline.openai.baseUrl": "http://localhost:8080",
  "cline.openai.apiKey": "gerdsen-ai-local-key",
  "cline.openai.model": "gerdsen-ai-optimized"
}
```

#### For Continue:
```json
{
  "continue.apiBase": "http://localhost:8080",
  "continue.apiKey": "gerdsen-ai-local-key",
  "continue.model": "gerdsen-ai-optimized"
}
```

### Step 3: Test Integration
1. Start GerdsenAI MLX Manager
2. Open VS Code
3. Try using the AI assistant features
4. Check the GerdsenAI logs for API requests

## Verification

### Test Installation
```bash
# Check if application starts
python3 gerdsen_ai_launcher.py --test

# Validate functionality
python3 validate_functionality.py

# Test API endpoints
curl http://localhost:8080/v1/models

# Check hardware detection
python3 -c "from src.enhanced_apple_silicon_detector import *; detector = EnhancedAppleSiliconDetector(); print(detector.get_chip_info())"
```

### Performance Verification
```bash
# Run performance benchmark
python3 tests/benchmark_performance.py

# Check optimization status
curl http://localhost:8080/api/hardware/optimization

# Monitor real-time metrics
curl http://localhost:8080/api/hardware/metrics
```

## Troubleshooting

### Common Installation Issues

#### Issue: "Command not found: python3"
**Solution:**
```bash
# Install Python via Homebrew
brew install python@3.11

# Add to PATH
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Issue: "Permission denied" errors
**Solution:**
```bash
# Fix permissions
chmod +x scripts/*.sh
chmod +x gerdsen_ai_launcher.py

# If using virtual environment
source venv/bin/activate
```

#### Issue: "Module not found" errors
**Solution:**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements_production.txt

# Check Python path
python3 -c "import sys; print(sys.path)"
```

#### Issue: "Port already in use"
**Solution:**
```bash
# Find process using port 8080
lsof -i :8080

# Kill the process (replace PID)
kill -9 <PID>

# Or use a different port
export GERDSEN_AI_PORT=8081
```

#### Issue: Apple frameworks not working
**Solution:**
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install PyObjC frameworks
pip install pyobjc-framework-Metal pyobjc-framework-CoreML

# Check framework availability
python3 -c "import objc; print('PyObjC available')"
```

### Performance Issues

#### Issue: Slow performance
**Solutions:**
1. Check thermal state: `python3 -c "from src.production_gerdsen_ai import *; print(get_thermal_state())"`
2. Reduce model size or enable quantization
3. Close other resource-intensive applications
4. Enable efficiency cores for background tasks

#### Issue: High memory usage
**Solutions:**
1. Reduce model cache size in configuration
2. Enable automatic memory management
3. Use quantized models
4. Monitor memory pressure: `memory_pressure`

#### Issue: API timeouts
**Solutions:**
1. Increase timeout in configuration
2. Reduce batch sizes
3. Enable streaming responses
4. Check network connectivity

### Getting Additional Help

#### Log Files
- **Application logs**: `logs/gerdsen_ai.log`
- **System logs**: Console.app → System Reports
- **Service logs**: `/tmp/gerdsen-ai-*.log`

#### Diagnostic Commands
```bash
# System information
system_profiler SPHardwareDataType

# Python environment
python3 -m pip list

# Network connectivity
netstat -an | grep 8080

# Process information
ps aux | grep gerdsen
```

#### Support Resources
- **Documentation**: Check the `docs/` directory
- **FAQ**: See `docs/FAQ.md`
- **Issues**: Report on the project repository
- **Community**: Join the discussion forums

## Uninstallation

### Remove Application
```bash
# Stop service (if running)
launchctl unload ~/Library/LaunchAgents/com.gerdsen.ai.mlx.manager.plist

# Remove application files
rm -rf /path/to/gerdsen-ai-enhanced

# Remove configuration
rm -rf ~/Documents/GerdsenAI

# Remove launch agent
rm ~/Library/LaunchAgents/com.gerdsen.ai.mlx.manager.plist

# Remove virtual environment (if created)
rm -rf venv
```

### Clean Up Dependencies
```bash
# Remove Python packages (if in virtual environment)
pip uninstall -r requirements_production.txt

# Remove Homebrew packages (optional)
brew uninstall python@3.11  # Only if not needed by other apps
```

---

**Installation complete! 🎉**

Your GerdsenAI MLX Manager Enhanced is now ready to use. Start the application and enjoy optimized AI performance on your Apple Silicon Mac!

