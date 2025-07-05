# IMPETUS v1.0.0 - Release

## Intelligent Model Platform Enabling Taskbar Unified Server
### By GerdsenAI - "Intelligence Without Boundaries"

### 🎉 First Release - MVP Complete!

IMPETUS exemplifies GerdsenAI's commitment to local-first privacy and cross-platform AI solutions. This native macOS menubar application enables you to run ANY local AI model with complete control over your data, seamlessly integrating with VS Code extensions like Cline, Continue, and others.

## 📦 Download

**For Apple Silicon Macs (M1, M2, M3, M4):**
- [`IMPETUS-1.0.0-arm64.dmg`](./IMPETUS-1.0.0-arm64.dmg) (96MB)

## 🚀 Installation

1. **Download** the DMG file above
2. **Double-click** to open the installer
3. **Drag** IMPETUS to your Applications folder
4. **Launch** IMPETUS from Applications or Launchpad

## ✨ Features

- **Universal Model Support**: GGUF, SafeTensors, MLX, CoreML, PyTorch, ONNX
- **Native macOS Menubar App**: Quick access from your menu bar
- **OpenAI Compatible API**: Works with Cline, Continue, and other VS Code extensions
- **Dynamic Model Discovery**: Automatically scans ~/Models for your AI models
- **Zero Configuration**: Works out of the box
- **Privacy First**: Everything runs locally, no cloud dependencies

## 🏁 Quick Start

1. **Launch IMPETUS** from Applications
2. **Click the menubar icon** and select "Start Server"
3. **Add Models**:
   - Click "Open Models Directory" in the menu
   - Place your `.gguf` files in `~/Models/GGUF/chat/`
   - Click "Scan for Models" to detect them
4. **Configure VS Code**:
   ```json
   {
     "cline.apiProvider": "openai",
     "cline.openaiBaseUrl": "http://localhost:8080",
     "cline.openaiApiKey": "any-key-works"
   }
   ```

## 📁 Model Directory Structure

Models are automatically organized in `~/Models/`:
```
~/Models/
├── GGUF/         # Quantized models (recommended)
│   ├── chat/     # Conversational models
│   ├── completion/
│   └── embedding/
├── SafeTensors/  # Hugging Face models
├── MLX/          # Apple Silicon optimized
├── CoreML/       # iOS/macOS native
├── PyTorch/      # PyTorch models
└── ONNX/         # Cross-platform
```

## 🤖 Recommended Models

For coding with Cline:
- **Qwen2.5-Coder** (32B) - Excellent for code generation
- **Code Llama** (13B/34B) - Specialized for coding
- **Mistral 7B Instruct** - Fast general purpose
- **Phi-3 Mini** - Small but capable

## 🛠 Technical Details

- **Requires**: macOS 15.0+ (Sequoia or later), Apple Silicon
- **API**: OpenAI-compatible at `http://localhost:8080`
- **Formats**: GGUF, SafeTensors, MLX, CoreML, PyTorch, ONNX
- **Memory**: 8GB minimum, 16GB+ recommended

## 🐛 Known Issues

- First launch may take a moment to initialize
- Large models (>30GB) may take time to load
- Ensure you have enough free RAM for your models

## 📝 Changelog

### v1.0.0 (July 5, 2025)
- Initial release
- Complete MVP implementation
- Support for 6 model formats
- Native macOS menubar application
- Dynamic model discovery
- OpenAI-compatible API
- VS Code extension compatibility

## 🔗 Links

- [GitHub Repository](https://github.com/your-repo/Impetus-LLM-Server)
- [Documentation](../../README.md)
- [Report Issues](https://github.com/your-repo/Impetus-LLM-Server/issues)

---

**GerdsenAI** - Intelligence Without Boundaries

IMPETUS is part of GerdsenAI's suite of distributed AI solutions, demonstrating our commitment to:
- 🔒 **Local-First Privacy**: Your models, your data, your control
- 🌐 **Cross-Platform Excellence**: Native performance on Apple Silicon
- ⚡ **Performance Optimization**: Lightning-fast local inference
- 🔧 **Seamless Integration**: Works with your existing development workflow

Learn more at [gerdsenai.com](https://gerdsenai.com)