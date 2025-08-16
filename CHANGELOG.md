# Changelog

All notable changes to Impetus LLM Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2025-08-16

### 🔧 Fixed
- **CRITICAL**: Fixed DMG app bundling where installed application would not launch from Applications folder
- **CRITICAL**: Fixed Python dependency isolation in bundled .app - Flask and other dependencies now load correctly
- **DMG Builder**: Updated `installers/create_dmg.sh` to properly bundle virtual environment site-packages (110MB)
- **Launcher Script**: Fixed `installers/scripts/launcher.sh` to set correct PYTHONPATH for dependency isolation
- **Production Config**: Made production configuration import fail gracefully instead of crashing
- **Security**: Applied production security validation successfully with bundled runtime

### 🔄 Changed
- DMG size increased from 72MB to 110MB due to proper Python dependency bundling
- Launcher now logs PYTHONPATH for debugging purposes
- Production configuration now shows success/warning messages instead of silent failures

### 📚 Documentation
- Updated CLAUDE.md with comprehensive fix documentation
- Updated installers/README.md with proper build instructions and recent fixes
- Added troubleshooting section for bundling issues

## [0.1.0] - 2025-01-XX

### 🎉 Initial Release - Production Ready!

This is the first public release of Impetus LLM Server, a high-performance local LLM server optimized for Apple Silicon.

### ✨ Features

#### Core Infrastructure
- **Flask-based REST API** with OpenAI-compatible endpoints
- **WebSocket support** for real-time updates and streaming
- **Modular architecture** with clean separation of concerns
- **Comprehensive error handling** and recovery mechanisms
- **Production-ready configuration** with rate limiting and security hardening

#### Apple Silicon Optimization
- **MLX framework integration** for optimal performance on M1/M2/M3/M4 chips
- **Dynamic hardware detection** with chip-specific optimizations
- **Metal GPU monitoring** for real-time performance tracking
- **Unified memory architecture** support for efficient model loading
- **Thermal monitoring** with automatic performance adjustment

#### Model Management
- **Model discovery service** with 9 curated, optimized models
- **One-click download** from HuggingFace Hub with progress tracking
- **Auto-loading** after download completion
- **Smart memory management** with automatic model unloading
- **Multi-model support** with concurrent model management

#### Performance Features
- **KV cache implementation** for multi-turn conversations (2-3x speedup)
- **Model warmup system** eliminating cold start latency (<200ms first token)
- **Memory-mapped loading** for 5-6x faster model loading
- **Comprehensive benchmarking** system with historical tracking
- **Performance modes** (efficiency/balanced/performance)

#### Developer Experience
- **Quick start guide** for 5-minute setup
- **CLI tool** with validation, setup, and management commands
- **OpenAI-compatible API** for VS Code extensions (Cline, Continue, Cursor)
- **React + TypeScript dashboard** with real-time monitoring
- **Error boundaries** and connection status indicators
- **User-friendly errors** with actionable suggestions
- **Comprehensive test suite** with unit, integration, and performance tests
- **Service files** for systemd and launchd
- **Troubleshooting guide** with solutions for common issues

### 📊 Performance Targets Achieved

- **Model Loading**: <5 seconds for 7B models (with mmap)
- **First Token Latency**: <200ms when warmed up
- **Inference Speed**: 
  - M1: 40-60 tokens/sec (7B 4-bit)
  - M2: 60-80 tokens/sec (7B 4-bit)
  - M3: 80-100 tokens/sec (7B 4-bit)
  - M4: 100-120 tokens/sec (7B 4-bit)
- **Memory Efficiency**: 20-30% reduction with mmap
- **API Overhead**: <50ms per request

### 🛠 Technical Stack

- **Backend**: Python 3.11+, Flask, MLX
- **Frontend**: React, TypeScript, Vite, Ant Design
- **Real-time**: Flask-SocketIO, WebSockets
- **Storage**: SQLite for benchmarks, filesystem for models
- **Testing**: pytest, Jest, integration tests

### 📦 Installation

```bash
# Quick install
curl -sSL https://raw.githubusercontent.com/GerdsenAI/Impetus-LLM-Server/main/install.sh | bash

# Validate installation
impetus validate

# Or from source
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server
pip install -e .
impetus setup
```

### 🙏 Acknowledgments

- Apple MLX team for the excellent ML framework
- HuggingFace for model hosting infrastructure
- The open-source community for feedback and contributions

### 📝 Notes

This is a beta release. While the core functionality is stable and well-tested, you may encounter edge cases. Please report any issues on GitHub.

---

[0.1.0]: https://github.com/GerdsenAI/Impetus-LLM-Server/releases/tag/v0.1.0