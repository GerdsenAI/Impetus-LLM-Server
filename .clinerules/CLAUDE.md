# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GerdsenAI Impetus LLM Server is a production-ready macOS application for managing Apple Silicon hardware optimization, machine learning models, and AI workloads with OpenAI-compatible API endpoints. The system is specifically optimized for Apple Silicon (M1-M4 series) and provides real-time hardware monitoring with VS Code extension compatibility.

## Common Development Commands

### Python Backend
```bash
# Install dependencies
pip install -r requirements_production.txt  # Production dependencies
pip install -e ".[dev]"                    # Development dependencies (pytest, black, flake8, mypy)

# Run tests
python -m pytest tests/                    # Run all tests
python validate_functionality.py           # Run validation tests
python -m pytest tests/test_production_functionality.py  # Run specific test

# Code quality
black src/ gerdsen_ai_server/src/         # Format code
flake8 src/ gerdsen_ai_server/src/        # Lint code
mypy src/ gerdsen_ai_server/src/          # Type checking

# Start server
python gerdsen_ai_server/src/production_main.py  # Production server (port 8080)
python test_server.py                            # Test server (port 8081)
```

### Frontend (React)
```bash
cd gerdsen-ai-frontend
pnpm install    # Install dependencies
pnpm dev        # Start development server
pnpm build      # Build production bundle
pnpm lint       # Run ESLint
```

### macOS Build
```bash
./scripts/build_macos.sh    # Build macOS app bundle
python setup_macos.py py2app  # Alternative build method
```

## High-Level Architecture

### Core Components

1. **API Layer** (`app.py`, `gerdsen_ai_server/src/production_main.py`)
   - Flask-based REST API with OpenAI compatibility
   - WebSocket support via Socket.IO for real-time metrics
   - CORS-enabled for cross-origin requests

2. **Model Management** (`gerdsen_ai_server/src/integrated_mlx_manager.py`)
   - Multi-format support: MLX, CoreML, ONNX, PyTorch, TensorFlow
   - In-memory caching with persistent storage
   - Dynamic optimization based on hardware capabilities
   - Currently using dummy model system for development

3. **Apple Silicon Integration** (`src/production/`)
   - Hardware detection for M1-M4 series (Pro, Max, Ultra variants)
   - Framework integration: CoreML, MLX, Metal Performance Shaders
   - GPU memory wiring and Neural Engine utilization
   - Thermal management with dynamic throttling

4. **Frontend Options**
   - React app in `gerdsen-ai-frontend/` (modern UI)
   - Static HTML/JS in `ui/` (multiple implementations)
   - Planned SwiftUI native interface

### API Structure
```
/api/
├── hardware/     # Hardware detection and metrics
├── terminal/     # Terminal execution
├── service/      # Service management
├── models/       # Model management
├── optimization/ # Performance tuning
/v1/              # OpenAI-compatible endpoints
├── models
├── chat/completions
├── completions
├── embeddings
```

### Key Services

- **IntegratedMLXManager**: Central model loading and management
- **EnhancedAppleSiliconDetector**: Hardware capability detection
- **RealTimeMetricsCollector**: Performance monitoring
- **EnhancedAppleFrameworksIntegration**: Apple framework optimization

## Important Implementation Notes

1. **OpenAI API Compatibility**: Full compatibility for VS Code extensions (Cline, Continue). Default port 8080, API key authentication.

2. **Performance**: Fully dynamic optimization for all Apple Silicon:
   - Automatically detects CPU/GPU/Neural Engine cores
   - Performance scales with available resources
   - No fixed targets - adapts to hardware capabilities
   - Model loading speed based on I/O bandwidth
   - Memory usage optimized for each system

3. **Current State**: Hybrid implementation with production Flask server and dummy model system. Active development on model integration (see modified files in git status).

4. **Branch Strategy**: Working on `Initial-Phase` branch, PRs target `main`.

5. **Apple Silicon Focus**: Dynamic optimization for ALL Apple Silicon Macs:
   - Automatic detection of M1/M2/M3/M4 variants (Base/Pro/Max/Ultra)
   - Scales performance based on available GPU cores and unified memory
   - Thermal-aware throttling to maintain sustainable performance
   - Future-proof design for upcoming Apple Silicon chips

6. **Security**: Local-only processing, model validation with checksums, sandboxed execution for untrusted models.

## VS Code Integration

Configure extensions to use:
- Base URL: `http://localhost:8080/v1`
- API Key: `sk-dummy-api-key-for-development`
- Model: `gpt-4` or check `/v1/models` for available models

## Agent Workflow Guidelines

When working on this project, follow this workflow:

1. **Start by reading**: Always check `ai.md` first for project context and current phase
2. **Check MVP section**: Read `TODO.md` MVP section - this is your primary goal
3. **Check memory**: Read `memory.md` for critical context and known issues
4. **Review MVP tasks**: Focus ONLY on tasks in the MVP section of `todo.md`
5. **MVP = Success**: Goal is to load ANY model and use with Cline (nothing more)
6. **Test with real extensions**: Always verify changes work with actual Cline extension
7. **Ignore post-MVP**: Don't work on UI, performance, or other enhancements until MVP complete

## Model Format Implementation Priority

When implementing model support, prioritize in this order:
1. GGUF (.gguf) - Most common quantized format
2. SafeTensors (.safetensors) - Hugging Face standard
3. MLX (.mlx, .npz) - Apple Silicon optimized
4. Others as needed

## Key Success Metrics

### MVP Success (Primary Goal)
- ✅ Load ANY local model format (GGUF, SafeTensors, MLX, etc.)
- ✅ Use loaded model with Cline in VS Code
- ✅ Basic chat completions working
- ✅ Zero errors during normal usage

### Post-MVP Success (Enhancement Goals)
- Setup time < 10 minutes for new users
- Performance automatically optimized for hardware
- Model management UI for easy switching
- Support for all VS Code AI extensions
- Zero manual configuration required

## Autonomous Mode

When working on this project, agents should operate autonomously:
- **NO PERMISSION REQUESTS**: Work continuously until MVP completion
- **Update TODO.md**: Update task status before EVERY commit
- **Commit Workflow**: Complete task → Update TODO.md → Commit → Next task
- **Continue Without Prompting**: Don't wait for user approval between tasks
- **Self-Directed**: Follow the task list and roadmap independently
- **Only Stop When**: Encountering critical blockers that prevent all progress

This applies to all AI agents: Claude, Gemini, or any other agent working on the project.