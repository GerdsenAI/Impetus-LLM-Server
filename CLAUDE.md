# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Development Philosophy

This project emphasizes systematic problem-solving through:
1. **Socratic Method**: Question assumptions and seek evidence before implementing
2. **OODA Loop**: Observe → Orient → Decide → Act in iterative cycles
3. **Evidence-Based Decisions**: Measure, don't guess - especially for performance

## Project Overview

Impetus-LLM-Server is a **production-ready** local LLM server optimized for Apple Silicon. The project provides both a standalone macOS app for end users and a full development environment for contributors.

### Status: v1.0.0 - Distribution Ready ✅
The project now features:
- ✅ **Standalone macOS App**: Self-contained .app with embedded Python runtime
- ✅ **Zero-dependency Installation**: Users just download and run
- ✅ **Production Server**: Gunicorn with Apple Silicon optimization
- ✅ **Beautiful Dashboard**: React/Three.js frontend
- ✅ **OpenAI API Compatibility**: Works with all major AI tools
- ✅ **Comprehensive Installers**: Multiple distribution options
- ✅ **Enterprise Features**: Health checks, monitoring, API docs

## Building for Distribution

### Creating the Standalone App (Recommended)
```bash
cd installers
./macos_standalone_app.sh
# Creates Impetus-Standalone-1.0.0.dmg with embedded Python
```

This creates a fully self-contained app that users can download and run without any dependencies.

### Other Distribution Options
- `installers/macos_simple_app.sh` - Lighter app requiring system Python
- `installers/production_installer.sh` - Server deployment with Gunicorn/nginx
- `installers/docker_installer.sh` - Container-based deployment

See `installers/README.md` for detailed information on each option.

## Development Environment Setup

### Virtual Environment (Required for Development)
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux

# Install backend dependencies
pip install -r gerdsen_ai_server/requirements.txt

# For production dependencies
pip install -r gerdsen_ai_server/requirements_production.txt
```

### Frontend Development
```bash
cd impetus-dashboard
pnpm install        # Install dependencies
pnpm dev            # Start dev server
pnpm build          # Build for production
```

### Backend Development
```bash
# Activate virtual environment first!
source .venv/bin/activate

cd gerdsen_ai_server

# Development mode
python src/main.py  # Run Flask server on port 8080

# Production mode
./start_production.sh  # Run with Gunicorn
```

## Architecture Overview

### Backend Structure (gerdsen_ai_server/src/)
- **main.py**: Flask application entry point with WebSocket support
- **wsgi.py**: Production WSGI entry point for Gunicorn
- **routes/**: API endpoints organized by functionality
  - hardware.py: Hardware detection and optimization
  - models.py: Model management endpoints
  - openai_api.py: OpenAI-compatible API with validation
  - health.py: Production health checks and monitoring
  - websocket.py: Real-time communication
- **schemas/**: Pydantic validation schemas for all API endpoints
- **model_loaders/**: Factory pattern for loading different model formats
- **inference/**: Unified inference system with base classes
- **utils/**: Configuration, logging, security utilities

### Frontend Structure
- **impetus-dashboard/**: Modern TypeScript React dashboard with Three.js visualization

### Key Integration Points
- **MLX Integration**: Direct Python API integration for Apple Silicon optimization
- **Memory Management**: Sophisticated caching and persistence strategies  
- **Apple Frameworks**: Integration with Metal, CoreML, and Neural Engine
- **WebSocket**: Real-time model status and performance monitoring

## Important Technical Details

1. **Apple Silicon Optimizations**
   - 50-110 tokens/sec depending on chip
   - <5s model loading with memory mapping
   - <200ms first token latency when warmed
   
2. **Model Formats**
   - MLX provides best performance on Apple Silicon
   - Memory-mapped loading reduces memory footprint by 20-30%
   
3. **Real-time Communication**
   - Sub-50ms latency for status updates
   - Automatic reconnection on connection loss
   
4. **Security**
   - Pydantic models for all request/response validation
   - Rate limiting and request size limits
   - Bearer token authentication
   
5. **Performance**
   - 84+ passing tests with >80% coverage
   - Handles 100+ concurrent requests
   - Automatic thermal throttling detection

## User Data Locations

When running as a standalone app, user data is stored in:
```
~/Library/Application Support/Impetus/
├── config/          # Configuration files
├── models/          # Downloaded models
├── cache/           # Model cache
└── logs/            # Application logs
```

## Development Guidelines

When adding new features:
1. Always use Pydantic schemas for request/response validation
2. Add health checks for new components in /api/health/status
3. Update OpenAPI documentation with proper examples
4. Include comprehensive unit and integration tests
5. Follow security best practices
6. Test with the standalone app builder

## Testing

```bash
# Run all tests
pytest gerdsen_ai_server/tests/

# Run with coverage
pytest --cov=gerdsen_ai_server gerdsen_ai_server/tests/

# Run specific test file
pytest gerdsen_ai_server/tests/test_api_models.py
```

## Problem-Solving Approach

### Socratic Development Method

Use questioning to deeply understand problems:

#### When Debugging Issues
- What is the exact error or unexpected behavior?
- What assumptions might be causing this issue?
- Have we verified these assumptions with evidence?
- What is the simplest test case that reproduces this?
- Could this be related to Apple Silicon-specific behavior?

#### When Adding Features
- What problem does this feature solve?
- Who will benefit from this feature?
- What are the performance implications?
- How does this integrate with existing architecture?
- What are the security considerations?

### OODA Loop Implementation

Structure your development process:

#### 1. OBSERVE
- Review relevant code sections and architecture
- Check performance metrics and logs
- Analyze memory usage patterns
- Monitor GPU/CPU utilization

#### 2. ORIENT
- Consider Apple Silicon unified memory architecture
- Evaluate available model formats
- Understand the modular architecture patterns
- Review security requirements

#### 3. DECIDE
- Select appropriate implementation approach
- Choose caching strategy for memory optimization
- Determine testing strategy
- Decide on error handling approach

#### 4. ACT
- Make incremental, testable changes
- Follow existing code patterns
- Implement comprehensive error handling
- Add appropriate logging
- Test on relevant hardware

## Release Process

1. **Update Version Numbers**
   - Update version in `setup.py`, `package.json`, installer scripts
   
2. **Build Standalone App**
   ```bash
   cd installers
   ./macos_standalone_app.sh
   ```
   
3. **Test on Clean System**
   - Test app on a Mac without development tools
   - Verify all features work correctly
   
4. **Create GitHub Release**
   - Upload the .dmg file
   - Include changelog and installation instructions
   
5. **Update Documentation**
   - Ensure README points to latest release
   - Update any version-specific documentation

## Common Issues and Solutions

### App Won't Start
- Check logs in `~/Library/Application Support/Impetus/logs/`
- Verify port 8080 is not in use
- Check for Python runtime issues in the embedded environment

### Performance Issues
- Monitor thermal state with built-in monitoring
- Check model size vs available memory
- Verify MLX is using Metal acceleration

### Build Issues
- Ensure all dependencies are installed
- Check that you're on Apple Silicon Mac
- Verify Python 3.11+ is available for building