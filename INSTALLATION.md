# Impetus Installation Guide

## 🚀 Quick Install (Recommended)

### For End Users

1. **Download the installer**
   - [Impetus-1.0.0-arm64.dmg](impetus-electron/dist/Impetus-1.0.0-arm64.dmg) - For Apple Silicon Macs (M1/M2/M3/M4)
   - [Impetus-1.0.0.dmg](impetus-electron/dist/Impetus-1.0.0.dmg) - For Intel Macs

2. **Install the app**
   - Double-click the downloaded DMG file
   - Drag Impetus to your Applications folder
   - Eject the DMG

3. **First launch**
   - Open Impetus from your Applications folder
   - If macOS shows a security warning:
     - Right-click Impetus and select "Open"
     - Or go to System Settings > Privacy & Security > "Open Anyway"

4. **Start using**
   - Click the rocket icon in your menu bar
   - Select "Start Server"
   - Configure VS Code/Cline with `http://localhost:8080`

That's it! No Python installation or setup required.

## 🎯 VS Code Configuration

### For Cline
1. Open VS Code Settings (⌘,)
2. Search for "Cline API"
3. Set Base URL: `http://localhost:8080`
4. Set API Key: `sk-dummy` (or leave blank)
5. Save and start using Cline!

### For Continue.dev
1. Open Continue settings
2. Add custom model:
```json
{
  "models": [{
    "title": "Impetus Local",
    "provider": "openai",
    "model": "gpt-4",
    "apiBase": "http://localhost:8080/v1"
  }]
}
```

## 📦 What's Included

- **Complete Python Environment**: Python 3.13.5 with all dependencies
- **GGUF Model Support**: Hardware-accelerated inference with Metal
- **Model Management UI**: Web interface for managing models
- **Real-time Monitoring**: Performance metrics and system status
- **OpenAI API Compatibility**: Works with any OpenAI-compatible extension

## 🛠️ Building from Source

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+ (for development only)
- macOS 12.0 or later

### Build Steps
```bash
# Clone the repository
git clone https://github.com/yourusername/Impetus-LLM-Server.git
cd Impetus-LLM-Server

# Install dependencies
cd impetus-electron
npm install

# Build self-contained app
npm run dist-with-python

# Install to Applications
./install-impetus.sh
```

## 🔧 Troubleshooting

### App won't open
- Right-click and select "Open" to bypass Gatekeeper
- Or run in Terminal: `xattr -cr /Applications/Impetus.app`

### Server won't start
- Check if port 8080 is available
- View logs in the Impetus window
- Restart the app if needed

### Models not loading
- Place GGUF models in `~/Models/GGUF/chat/`
- Ensure model files have `.gguf` extension
- Check file permissions

## 📋 System Requirements

- **macOS**: 12.0 or later
- **Processor**: Apple Silicon (M1/M2/M3/M4) or Intel
- **Memory**: 8GB minimum, 16GB+ recommended
- **Storage**: 1GB for app + space for models

## 🎨 Features

### Menu Bar Integration
- Quick access from menu bar
- Server status indicator
- One-click start/stop
- Model switching menu

### Model Management
- Drag & drop model upload
- HuggingFace model search
- Real-time download progress
- Model format validation

### Performance Monitoring
- CPU/GPU usage graphs
- Memory utilization
- Inference speed metrics
- Thermal status

## 🔒 Privacy & Security

- **100% Local**: No cloud services or telemetry
- **Private**: Your data never leaves your machine
- **Secure**: API key authentication (optional)
- **Open Source**: Full source code available

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Support

- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/Impetus-LLM-Server/issues)
- Documentation: [Full docs](https://github.com/yourusername/Impetus-LLM-Server/wiki)

---

Built with ❤️ for the developer community. Enjoy local AI coding assistance!