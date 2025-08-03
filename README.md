# Impetus LLM Server

**v1.0.0** - High-performance local LLM server optimized for Apple Silicon, providing OpenAI-compatible API endpoints with a beautiful dashboard interface.

## 🎯 Quick Start for Users

### Download the App
1. Download the latest release from [Releases](https://github.com/GerdsenAI/Impetus-LLM-Server/releases)
2. Open the `.dmg` file
3. Drag **Impetus.app** to your Applications folder
4. Double-click to run!

That's it! No Python, no terminal commands, no setup required.

## 🚀 Features

### For End Users
- **Zero Setup**: Download, install, run - just like any Mac app
- **Beautiful Dashboard**: Real-time monitoring and control at http://localhost:5173
- **Fast Performance**: 50-110 tokens/sec on Apple Silicon
- **OpenAI Compatible**: Works with VS Code extensions, Continue.dev, Cursor, and more
- **Automatic Updates**: Built-in updater keeps you on the latest version

### For Developers
- **API Compatible**: Drop-in replacement for OpenAI API
- **WebSocket Support**: Real-time streaming responses
- **Comprehensive Docs**: Interactive API documentation at http://localhost:8080/docs
- **Multiple Models**: Support for Mistral, Llama, Phi, and more
- **Production Ready**: Health checks, monitoring, and enterprise features

## 📋 System Requirements

- **macOS** 13.0 or later
- **Apple Silicon** (M1, M2, M3, or M4 series)
- **8GB RAM** minimum (16GB recommended)
- **10GB disk space** for models

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

### Creating Your Own Distribution

We provide several installer options:

- **Standalone App** (Recommended): `installers/macos_standalone_app.sh`
  - Creates a fully self-contained .app with embedded Python
  - Best for end-user distribution

- **Simple App**: `installers/macos_simple_app.sh`
  - Creates a lighter .app that requires Python on the system
  - Good for developers

- **Production Server**: `installers/production_installer.sh`
  - Sets up Gunicorn + nginx for server deployments

See [installers/README.md](installers/README.md) for all options.

### API Usage

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="your-api-key"  # Get from ~/.impetus/config
)

response = client.chat.completions.create(
    model="mistral-7b",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

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