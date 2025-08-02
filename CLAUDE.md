# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Development Philosophy

This project emphasizes systematic problem-solving through:
1. **Socratic Method**: Question assumptions and seek evidence before implementing
2. **OODA Loop**: Observe → Orient → Decide → Act in iterative cycles
3. **Evidence-Based Decisions**: Measure, don't guess - especially for performance

## Project Overview

Impetus-LLM-Server is a high-performance machine learning model management system optimized for Apple Silicon hardware. The project consists of a Python backend server and a React frontend dashboard, focusing on MLX model management and inference.

### Current Status (January 2025)
- **Version**: v0.1.0 Released ✅
- **Current Branch**: `feature/complete-unit-tests`
- **Priority**: Completing unit test coverage for download manager, hardware detection, and error recovery
- **Test Coverage**: 84 tests passing, 3 test suites pending implementation

## Key Commands

### Testing Commands
```bash
# Run all tests
python -m pytest gerdsen_ai_server/tests/ -v

# Run specific test files
python -m pytest gerdsen_ai_server/tests/test_mlx_loader.py -v
python -m pytest gerdsen_ai_server/tests/test_model_warmup.py -v
python -m pytest gerdsen_ai_server/tests/test_api_models.py -v
python -m pytest gerdsen_ai_server/tests/test_kv_cache.py -v
python -m pytest gerdsen_ai_server/tests/test_integration.py -v
python -m pytest gerdsen_ai_server/tests/test_performance.py -v

# Run with coverage
python -m pytest gerdsen_ai_server/tests/ --cov=gerdsen_ai_server.src --cov-report=html
```

### Frontend Development (Root directory)
```bash
npm install         # Install dependencies
npm run dev         # Start Vite dev server for frontend
npm run build       # Build frontend for production
npm run lint        # Run ESLint for frontend code
npm run preview     # Preview production build
```

### Frontend Development (impetus-dashboard)
```bash
cd impetus-dashboard
pnpm install        # Install dependencies (uses pnpm)
pnpm dev            # Start Vite dev server
pnpm build          # Build with TypeScript and Vite
pnpm lint           # Run ESLint
pnpm preview        # Preview production build
```

### Backend Development
```bash
cd gerdsen_ai_server
python src/main.py  # Run the Flask server on port 5000

# Production deployment
impetus validate    # Check system compatibility
impetus setup      # Interactive setup wizard
impetus server     # Start the server
impetus models     # List available models
```

### Python Dependencies
- Main backend: `gerdsen_ai_server/requirements.txt`
- Production: `gerdsen_ai_server/requirements_production.txt`
- Development: `requirements_dev.txt`
- macOS specific: `requirements_macos.txt`

## Known Issues & Gotchas

### Source Code Access
- The `gerdsen_ai_server/src/` directory may have permission issues or contain compiled/binary files
- Source code might be in a compiled format for production deployment
- When testing, mock dependencies extensively to avoid hardware-specific issues

### Testing Environment
- Tests require Python 3.11+ with pytest
- Some tests may fail without actual Apple Silicon hardware
- Mock MLX and hardware dependencies when running tests in CI/CD

### Common Development Issues
1. **Git Lock Files**: If you encounter `.git/index.lock` errors, remove the lock file before git operations
2. **Large Uncommitted Files**: The project may accumulate large files (node_modules, __pycache__, etc.) - ensure .gitignore is properly configured
3. **Python Path Issues**: Tests expect imports from `src.` - ensure PYTHONPATH includes the gerdsen_ai_server directory

## Architecture Overview

### Backend Structure (gerdsen_ai_server/src/)
- **main.py**: Flask application entry point with WebSocket support
- **routes/**: API endpoints organized by functionality
  - hardware.py: Hardware detection and optimization
  - models.py: Model management endpoints
  - openai_api.py: OpenAI-compatible API
  - websocket.py: Real-time communication
- **model_loaders/**: Factory pattern for loading different model formats (GGUF, MLX, CoreML, ONNX, PyTorch, SafeTensors)
- **inference/**: Unified inference system with base classes
- **auth/**: OpenAI authentication integration
- **utils/**: Configuration, logging, and security utilities

### Key Integration Points
- **MLX Integration**: Direct Python API integration for Apple Silicon optimization
  - OBSERVE: Current MLX performance metrics and bottlenecks
  - ORIENT: Understand MLX's lazy computation and unified memory benefits
  - DECIDE: Choose optimal batch sizes and memory allocation strategies
  - ACT: Implement and measure performance improvements
  
- **Memory Management**: Sophisticated caching and persistence strategies
  - OBSERVE: Memory usage patterns and model loading times
  - ORIENT: Analyze cache hit rates and eviction patterns
  - DECIDE: Select appropriate caching tiers (L1/L2/L3)
  - ACT: Implement caching with monitoring
  
- **Apple Frameworks**: Integration with Metal, CoreML, and Neural Engine
  - OBSERVE: Hardware utilization across different operations
  - ORIENT: Map operations to optimal execution units
  - DECIDE: Balance between frameworks based on workload
  - ACT: Route operations dynamically based on performance
  
- **WebSocket**: Real-time model status and performance monitoring
  - OBSERVE: Message latency and connection stability
  - ORIENT: Understand client update requirements
  - DECIDE: Choose update frequency and data granularity
  - ACT: Implement with fallback mechanisms

### Frontend Structure
- Two separate frontend projects:
  1. Root package.json: Basic React frontend with Ant Design
  2. impetus-dashboard/: TypeScript React dashboard with Three.js

## Important Technical Details

1. **Apple Silicon Optimizations**: The system is specifically optimized for M-series chips with unified memory architecture
   - Question: How can we best leverage unified memory for this use case?
   - Question: What are the performance differences between M1, M2, and M3 chips?
   
2. **Model Formats**: Supports multiple formats including GGUF, MLX, CoreML, ONNX, PyTorch, and SafeTensors
   - Question: Which format provides the best performance/compatibility trade-off?
   - Question: How do we ensure consistent behavior across formats?
   
3. **Real-time Communication**: Uses Flask-SocketIO for WebSocket connections
   - Question: What latency is acceptable for real-time updates?
   - Question: How do we handle connection failures gracefully?
   
4. **Security**: Implements model validation, sandboxed execution, and access control
   - Question: What attack vectors should we consider?
   - Question: How do we balance security with performance?
   
5. **Performance**: Designed for high throughput (40-60 tokens/sec on M3 Ultra)
   - Question: What metrics best represent user-perceived performance?
   - Question: How do we maintain performance across different configurations?

## Development Notes

- The project is in active development with focus on performance optimization
- Uses modular architecture with clear separation of concerns
- Implements factory patterns for model loading flexibility
- Includes comprehensive error handling and logging
- Supports both development and production configurations

## Problem-Solving Approach

When working on this codebase, apply both the Socratic method and OODA loop for systematic problem-solving:

### Socratic Development Method

Use questioning to deeply understand problems before implementing solutions:

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

#### When Optimizing Performance
- What metrics prove this is a bottleneck?
- What are the trade-offs of this optimization?
- How will this affect different Apple Silicon models?
- Is this optimization maintainable long-term?
- What alternatives have we considered?

### OODA Loop Implementation

Structure your development process using Observe-Orient-Decide-Act:

#### 1. OBSERVE
Before making changes:
- Review relevant code sections and architecture
- Check performance metrics and logs
- Analyze memory usage patterns
- Monitor GPU/CPU utilization
- Examine existing model loader implementations
- Review error logs and stack traces

#### 2. ORIENT
Understand the context:
- Consider Apple Silicon unified memory architecture
- Evaluate available model formats (GGUF, MLX, CoreML, etc.)
- Understand the modular architecture patterns
- Review security and sandboxing requirements
- Assess WebSocket real-time communication needs
- Consider factory pattern implications

#### 3. DECIDE
Make informed choices:
- Select appropriate model loader based on format
- Choose caching strategy for memory optimization
- Determine if changes need WebSocket updates
- Decide on error handling approach
- Select testing strategy for changes
- Choose between synchronous/asynchronous implementation

#### 4. ACT
Implement with confidence:
- Make incremental, testable changes
- Follow existing code patterns and conventions
- Implement comprehensive error handling
- Add appropriate logging for debugging
- Test on relevant hardware configurations
- Monitor performance impact

### Combining Both Methods

When facing complex problems:

1. **Start with Socratic Questions** to understand the problem deeply
2. **Use OODA to structure your approach** to solving it
3. **Question your decisions** at each OODA stage
4. **Iterate based on observations** from your actions

Example workflow for a performance issue:
- **Question**: "Why is model loading slow?" (Socratic)
- **Observe**: Profile the loading process (OODA)
- **Question**: "What assumptions are we making about memory allocation?" (Socratic)
- **Orient**: Review MLX memory management patterns (OODA)
- **Question**: "What evidence supports our optimization approach?" (Socratic)
- **Decide**: Implement memory-mapped loading (OODA)
- **Act**: Code, test, and measure results (OODA)
- **Question**: "Did this solve the root cause or just the symptom?" (Socratic)

## Current Development Focus

### Immediate Priority: Unit Test Completion

The project has achieved v0.1.0 release with 84 passing tests, but requires completion of three critical test suites:

1. **Download Manager Tests** (`test_download_manager.py`)
   - Mock HuggingFace Hub API interactions
   - Test download progress tracking and WebSocket events
   - Test error scenarios (network failures, disk space)
   - Test concurrent downloads and cancellation

2. **Hardware Detection Tests** (`test_hardware_detection.py`)
   - Mock system hardware information
   - Test Apple Silicon chip detection (M1-M4)
   - Test memory and GPU capabilities detection
   - Test thermal monitoring and unsupported hardware handling

3. **Error Recovery Tests** (`test_error_recovery.py`)
   - Test out-of-memory recovery mechanisms
   - Test thermal throttling responses
   - Test retry logic with exponential backoff
   - Test failure loop prevention

### Testing Best Practices

When implementing tests:
- Use mocking extensively to avoid hardware dependencies
- Test both success and failure paths
- Ensure tests are deterministic and fast
- Follow existing test patterns in the codebase
- Add integration tests for complex workflows

### Next Priorities After Testing

1. **macOS Native Integration**
   - Menubar application with PyObjC
   - App bundle creation and code signing
   - Auto-update with Sparkle framework

2. **Advanced Inference Features**
   - Function calling support
   - JSON mode for structured output
   - Grammar-constrained generation

3. **Dashboard Enhancements**
   - Dark/Light mode
   - Model comparison features
   - 3D performance visualizations