# Impetus LLM Server

**v1.0.2** - High-performance local LLM server optimized for Apple Silicon with enhanced menu bar application, featuring OpenAI-compatible API endpoints and a beautiful dashboard interface.

## 🎯 Quick Start for Users

### Download the App
1. Download the latest release from [Releases](https://github.com/GerdsenAI/Impetus-LLM-Server/releases)
2. Open the `.dmg` file
3. Drag **Impetus.app** to your Applications folder
4. Double-click to run!

That's it! No Python, no terminal commands, no setup required.

## 🚀 Features

### 🆕 Enhanced Menu Bar Application
- **Professional Onboarding**: Interactive first-run tour for new users
- **Permission Management**: Proper macOS permissions with guided setup
- **Native Experience**: Brain emoji (🧠) status indicator in menu bar
- **Server Control**: Start/stop server with visual status updates
- **Model Management**: Load and switch between AI models from menu
- **Performance Modes**: Efficiency/Balanced/Performance settings
- **System Monitoring**: Real-time CPU, memory, and uptime stats
- **Help System**: Built-in help with guided tour restart

### For End Users
- **Zero Setup**: Download, install, run - just like any Mac app
- **Beautiful Dashboard**: Real-time monitoring and control at http://localhost:5173
- **Fast Performance**: 50-110 tokens/sec on Apple Silicon with MLX 0.28.0
- **OpenAI Compatible**: Works with VS Code extensions, Continue.dev, Cursor, and more
- **Menu Bar Control**: Native macOS menu bar app for seamless background operation

### For Developers
- **API Compatible**: Drop-in replacement for OpenAI API
- **WebSocket Support**: Real-time streaming responses
- **Comprehensive Docs**: Interactive API documentation at http://localhost:8080/docs
- **Multiple Models**: Support for Mistral, Llama, Phi, and more with latest MLX
- **Production Ready**: Health checks, monitoring, and enterprise features

## 🍎 Menu Bar Application

### Quick Start with Menu Bar App

For developers and power users who want background operation:

```bash
# Clone and setup
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server

# Install enhanced menu bar app
./installers/install_menubar.sh

# Launch enhanced version (recommended)
python run_menubar_enhanced.py

# Or launch basic version
python run_menubar.py
```

### Features

- 🧠 **Visual Status**: Brain emoji changes based on server state
  - 🧠 Server stopped (idle)
  - 🟡 Server starting/stopping
  - 🟢 Server running
  - 🔴 Server error

- 🎯 **First-Run Experience**: Professional onboarding tour
- 🔐 **Permission Management**: Automatic macOS permissions setup
- 🤖 **Model Management**: Load Mistral, Llama, Phi models from menu
- ⚡ **Performance Tuning**: Switch between efficiency/performance modes
- 📊 **System Monitoring**: Live CPU, memory, uptime tracking
- 🔗 **Quick Access**: Dashboard and API docs one click away

## 📋 System Requirements

- **macOS** 14.0 or later (Sonoma+)
- **Apple Silicon** (M1, M2, M3, or M4 series)
- **8GB RAM** minimum (16GB recommended)
- **10GB disk space** for models
- **Python 3.11+** (for menu bar app development)

## 🛠 For Developers

### Building from Source

If you want to build the app yourself or contribute to development:

```bash
# Clone the repository
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server

# Build the standalone app
cd installers
./macos_standalone_app.sh

# The app will be in build_standalone/Impetus.app
```

### Distribution Options

We provide multiple installer and deployment options:

- **Enhanced Menu Bar App**: `installers/install_menubar.sh`
  - Creates native macOS menu bar application
  - Includes onboarding tour and permissions management
  - Best for developer and power user experience

- **Standalone App** (Recommended): `installers/macos_standalone_app.sh`
  - Creates a fully self-contained .app with embedded Python
  - Best for end-user distribution

- **Simple App**: `installers/macos_simple_app.sh`
  - Creates a lighter .app that requires Python on the system
  - Good for developers

- **Production Server**: `installers/production_installer.sh`
  - Sets up Gunicorn + nginx for server deployments

See [installers/README.md](installers/README.md) for all options.

### Latest Dependencies

The project now uses the latest versions:

```bash
# MLX Framework (Apple Silicon ML)
mlx==0.28.0               # Latest Apple ML framework
mlx-lm==0.26.3            # Language model support
mlx-metal==0.28.0         # Metal GPU acceleration

# Menu Bar Application
rumps==0.4.0              # macOS menu bar framework
pyobjc-core==11.1         # Python-Objective-C bridge
pyobjc-framework-Cocoa==11.1  # Cocoa framework bindings

# Server Framework
flask==3.0.3              # Web framework
gunicorn==23.0.0          # Production WSGI server
psutil==7.0.0             # System monitoring
```

### API Usage

The server auto-generates an API key on the first `/v1/*` request and prints it to the console. Save this key for subsequent requests.

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="impetus-<key-from-server-console>"  # Check server console output
)

response = client.chat.completions.create(
    model="Qwen3-4B-Instruct-2507-MLX-4bit",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

> **Tip**: Set `IMPETUS_API_KEY=my-secret-key` as an environment variable for a persistent key that won't change on restart.

### Configuration

The app stores configuration in `~/Library/Application Support/Impetus/`:

```bash
# View configuration
cat ~/Library/Application\ Support/Impetus/config/server.env

# Models are stored in
~/Library/Application\ Support/Impetus/models/

# Logs for debugging
~/Library/Application\ Support/Impetus/logs/impetus.log
```

## 🌟 Model Library

Popular models that work great with Impetus:

- **Mistral 7B**: Best balance of speed and quality
- **Llama 3**: Latest from Meta with excellent performance  
- **Phi-3**: Microsoft's efficient small model
- **Qwen**: Excellent for code and technical tasks

Download models directly from the dashboard!

## 🔧 Troubleshooting

### App Won't Open
- Right-click and select "Open" to bypass Gatekeeper on first run
- Check Console.app for detailed error messages

### Server Not Starting
- Check if port 8080 is already in use
- View logs: `~/Library/Application Support/Impetus/logs/impetus.log`

### Performance Issues
- Ensure no other heavy applications are running
- Try a smaller model (Phi-3 mini)
- Check Activity Monitor for resource usage

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements_dev.txt

# Run tests
pytest gerdsen_ai_server/tests/

# Run with hot reload
cd gerdsen_ai_server
python src/main.py --reload
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [MLX](https://github.com/ml-explore/mlx) by Apple
- UI powered by React and Three.js
- OpenAI API compatibility for seamless integration

---

**Ready to supercharge your Mac with local AI?** [Download Impetus now!](https://github.com/GerdsenAI/Impetus-LLM-Server/releases)