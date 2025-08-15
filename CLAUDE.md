# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Development Philosophy

This project emphasizes systematic problem-solving through:
1. **Socratic Method**: Question assumptions and seek evidence before implementing
2. **OODA Loop**: Observe → Orient → Decide → Act in iterative cycles
3. **Evidence-Based Decisions**: Measure, don't guess - especially for performance

## Project Overview

Impetus-LLM-Server is a **production-ready** local LLM server optimized for Apple Silicon, featuring MLX integration for high-performance inference.

### Current Status: v1.0.1 - MLX Integration Complete ✅

#### Working Features
- ✅ **MLX Model Support**: Successfully loads and runs MLX models from HuggingFace
- ✅ **OpenAI API Compatibility**: Full `/v1/chat/completions` endpoint support
- ✅ **Streaming & Non-streaming**: Both response modes fully functional
- ✅ **Auto-loading**: Models load automatically when requested via API
- ✅ **Standalone macOS App**: Self-contained .app with embedded Python runtime
- ✅ **Production Server**: Gunicorn with Apple Silicon optimization
- ✅ **React Dashboard**: Beautiful Three.js frontend interface

#### Technical Stack
- **Inference**: MLX (Apple's machine learning framework)
- **Server**: Flask + Gunicorn + eventlet (WebSocket support)
- **Models**: Support for Mistral, Llama, Phi, Qwen (4-bit and 8-bit quantized)
- **API**: OpenAI-compatible endpoints for seamless integration
- **Frontend**: React + Three.js dashboard

## Active Development: Menu Bar App

Currently building a native macOS menu bar application for seamless background operation:
- Status indicators (idle/active/error)
- Model management from menu
- Server lifecycle control
- Resource monitoring
- Launch at login support

## Dependencies & Requirements

### Core Dependencies
```bash
# MLX and ML
mlx>=0.28.0              # Apple's ML framework
mlx-lm>=0.26.3           # MLX language model support
sentencepiece>=0.2.0     # Required for tokenizers
transformers>=4.52.1     # HuggingFace transformers
huggingface-hub>=0.34.0  # Model downloading

# Web Framework
flask>=3.1.0
flask-cors>=6.0.0
flask-socketio>=5.5.0
eventlet>=0.40.0         # WebSocket support
gunicorn                 # Production server

# Utilities
pydantic>=2.11.0         # Data validation
loguru>=0.7.0            # Logging
psutil>=7.0.0            # System monitoring
```

### System Requirements
- macOS 13.0+ (Ventura or later)
- Apple Silicon (M1/M2/M3/M4)
- Python 3.11+
- 8GB RAM minimum (16GB recommended)

## Project Structure

```
gerdsen_ai_server/
├── src/
│   ├── main.py                    # Flask application entry
│   ├── model_loaders/
│   │   └── mlx_loader.py          # MLX model loading/inference
│   ├── routes/
│   │   └── openai_api.py          # OpenAI-compatible endpoints
│   ├── menubar/                   # [NEW] Menu bar app
│   │   ├── app.py                 # Menu bar application
│   │   └── server_manager.py      # Server lifecycle
│   └── config/
│       └── settings.py            # Configuration management
├── installers/
│   ├── macos_standalone_app.sh    # Creates .app bundle
│   └── production_installer.sh    # Server deployment
└── impetus-dashboard/              # React frontend
```

## Development Workflow

### Setting Up Development Environment
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r gerdsen_ai_server/requirements.txt
pip install sentencepiece eventlet  # Additional required packages

# Run development server
cd gerdsen_ai_server
python src/main.py
```

### Testing MLX Inference
```bash
# Test via API
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Building for Distribution
```bash
cd installers
./macos_standalone_app.sh  # Creates self-contained .app
```

## Known Issues & Solutions

### Issue: MLX model loading fails silently
**Solution**: Ensure `sentencepiece` is installed for tokenizer support

### Issue: WebSocket connections fail
**Solution**: Install `eventlet` for proper WebSocket handling

### Issue: Model validation errors in API
**Solution**: Fixed in `openai_api.py` - handles both dict and Pydantic objects

## Performance Optimization

### MLX-Specific Optimizations
- Memory-mapped model loading for faster startup
- Lazy model loading to reduce initial memory usage
- KV cache support (infrastructure in place, implementation pending)
- Batch inference support for multiple requests

### Server Optimizations
- Gunicorn with eventlet workers for concurrent requests
- Auto-detection of Apple Silicon capabilities
- Performance mode selection based on hardware

## Testing Guidelines

### Essential Tests Before Commit
1. Model loading from HuggingFace
2. Basic inference via API
3. Streaming response functionality
4. Dashboard connectivity
5. Menu bar app launch (when implemented)

### Performance Benchmarks
- Target: 50-110 tokens/sec on Apple Silicon
- Measure with different model sizes (3B, 7B, 13B)
- Monitor memory usage during inference

## Future Enhancements

### High Priority
- [ ] Complete menu bar application
- [ ] Implement true KV cache for multi-turn conversations
- [ ] Add temperature/top_p sampling to MLX generation
- [ ] Support for vision models (LLaVA, etc.)

### Medium Priority
- [ ] Model quantization tools
- [ ] Fine-tuning support via MLX
- [ ] Batch inference optimization
- [ ] Plugin system for custom models

### Low Priority
- [ ] Windows/Linux support
- [ ] Cloud sync for models
- [ ] Model marketplace integration

## Contributing Guidelines

1. **Test on Apple Silicon**: All changes must be tested on M1/M2/M3/M4
2. **Preserve API Compatibility**: Don't break OpenAI API compatibility
3. **Document Changes**: Update this file with significant changes
4. **Performance First**: Measure impact of changes on inference speed
5. **User Experience**: Prioritize simplicity for end users

## Contact & Support

- GitHub Issues: Report bugs and feature requests
- Documentation: See `/docs` folder for detailed guides
- API Reference: http://localhost:8080/docs when server is running