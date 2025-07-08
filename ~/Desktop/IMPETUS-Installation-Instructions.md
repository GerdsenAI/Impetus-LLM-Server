# IMPETUS LLM Server Installation Instructions

## 🎉 Welcome to IMPETUS!
**Intelligent Model Platform Enabling Taskbar Unified Server**

Your professional macOS installer is ready: `Impetus-LLM-Server-Installer.dmg` (96MB)

## 📦 Installation Steps

### 1. Mount the Installer
- Double-click `Impetus-LLM-Server-Installer.dmg` on your desktop
- The installer window will open

### 2. Install the Application
- Drag `Impetus.app` to the `Applications` folder shortcut
- Wait for the copy process to complete
- Eject the installer disk image

### 3. Launch IMPETUS
- Open Applications folder or use Spotlight (⌘+Space)
- Search for "Impetus" and double-click to launch
- The app will appear in your menu bar (top-right corner)

### 4. Start the Server
- Click the IMPETUS icon in your menu bar
- Select "Start Server" from the dropdown menu
- Server will start at `http://localhost:8080`

## 🚀 Quick Setup for VS Code + Cline

### Configure Cline Extension
1. Install Cline extension in VS Code
2. Open Cline settings
3. Set these values:
   - **API Provider**: OpenAI
   - **Base URL**: `http://localhost:8080`
   - **API Key**: `sk-dev-gerdsen-ai-local-development-key`
   - **Model**: `gpt-4` (or any available model)

### Add Models
1. Click IMPETUS menu bar icon
2. Select "Open Models Directory"
3. Place model files in appropriate folders:
   - GGUF models → `~/Models/GGUF/chat/`
   - SafeTensors → `~/Models/SafeTensors/chat/`
   - MLX models → `~/Models/MLX/chat/`
4. Select "Scan for Models" to detect new models
5. Choose active model from the Models menu

## ✅ Features Included

- **Universal Model Support**: GGUF, SafeTensors, MLX, CoreML, PyTorch, ONNX
- **Native macOS Experience**: Menu bar integration with Apple HIG design
- **VS Code Integration**: Full OpenAI API compatibility for Cline/Continue
- **Apple Silicon Optimization**: Dynamic performance scaling for M1/M2/M3/M4
- **Privacy-First**: All processing happens locally, no cloud dependencies
- **Self-Contained**: No additional Python installation required

## 🔧 System Requirements

- **OS**: macOS 12.0 or later
- **Hardware**: Apple Silicon Mac (M1, M2, M3, M4) recommended
- **Memory**: 8GB RAM minimum, 16GB+ recommended for larger models
- **Storage**: 500MB for app + space for models (2-50GB per model)

## 🆘 Troubleshooting

### If the server won't start:
1. Check if port 8080 is available
2. Look for error messages in the menu bar app
3. Try restarting the app

### If models won't load:
1. Ensure models are in correct directories
2. Check file permissions
3. Use "Scan for Models" to refresh

### If Cline can't connect:
1. Verify server is running (green indicator in menu bar)
2. Test API: Open `http://localhost:8080/v1/models` in browser
3. Check Cline configuration matches settings above

## 🎯 Success!

Once configured, you can:
- ✅ Use Cline with local AI models
- ✅ Switch models on the fly
- ✅ Enjoy private, local AI coding assistance
- ✅ Get optimal performance on your Apple Silicon Mac

## 📞 Support

For issues or questions:
- Project: [Impetus-LLM-Server](https://github.com/GerdsenAI/Impetus-LLM-Server)
- Documentation: Check `README.md` in the project repository

---

**Built with ❤️ for Apple Silicon developers**  
*© 2025 GerdsenAI. All rights reserved.*
