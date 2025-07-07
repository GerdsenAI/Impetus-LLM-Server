# Impetus Installation Guide

## 🚀 Quick Install (Recommended)

### For End Users

1. **Download the latest release**
   - Visit the [Releases](https://github.com/GerdsenAI/Impetus-LLM-Server/releases) page
   - Download the appropriate version for your system

2. **Install dependencies**
   - Ensure Python 3.9+ is installed on your system
   - Install required packages: `pip install -r requirements.txt`

3. **Launch the tray app**
   - Run `python impetus_tray.py`
   - A tray icon will appear in your system tray/menu bar

4. **Start using**
   - Click the tray icon to access the menu
   - Select "Start Server" to launch the LLM server
   - Select "Open Web UI" to configure settings in your browser
   - Configure VS Code/Cline with `http://localhost:8080`

That's it! The tray app provides a lightweight interface to control the server.

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

- **GGUF Model Support**: Hardware-accelerated inference with Metal
- **Model Management UI**: Web interface for managing models
- **Real-time Monitoring**: Performance metrics and system status
- **OpenAI API Compatibility**: Works with any OpenAI-compatible extension

## 💻 Developer Installation

### Prerequisites


- macOS 12+ (Monterey or newer) recommended
- Python 3.9+ with pip
- Git (for cloning the repository)


### Steps


1. **Clone the repository**
   
```bash
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server
```


2. **Install dependencies**
   
```bash
pip install -r requirements.txt
```


3. **Run in development mode**
   
```bash
python impetus_tray.py
```


4. **Build a standalone executable (optional)**
   
```bash
# Using PyInstaller (install with: pip install pyinstaller)
pyinstaller --onefile --windowed --icon=assets/icon.ico --name Impetus impetus_tray.py
```

   This creates a standalone executable in the `dist` folder.

## 🔧 Troubleshooting

- Run in Terminal: `xattr -cr /Applications/Impetus.app`


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

- GitHub Issues: [Report bugs or request features](https://github.com/GerdsenAI/Impetus-LLM-Server/issues)
- [Full Documentation](https://github.com/GerdsenAI/Impetus-LLM-Server/wiki)

---

Built with ❤️ for the developer community. Enjoy local AI coding assistance!