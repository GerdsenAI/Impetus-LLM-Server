# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Development Philosophy

This project emphasizes systematic problem-solving through:
1. **Socratic Method**: Question assumptions and seek evidence before implementing
2. **OODA Loop**: Observe → Orient → Decide → Act in iterative cycles
3. **Evidence-Based Decisions**: Measure, don't guess - especially for performance

## Project Overview

Impetus-LLM-Server is a production-ready machine learning model management system optimized for Apple Silicon hardware. The project consists of a Python backend server and a React frontend dashboard, focusing on MLX model management and inference.

### Current Focus: Production MVP Sprint (v1.0.0)
The project has completed v0.1.0 with all core features. We are now focused on production hardening in a single sprint:
- Replace Flask dev server with Gunicorn
- Implement CI/CD pipeline
- Add comprehensive input validation
- Create health check endpoints
- Generate OpenAPI documentation
- Write production deployment guide

## Development Environment Setup

### Virtual Environment (Required)
Always use a virtual environment to ensure consistent dependencies. The project uses Python 3.11+.

```bash
# Create virtual environment (already created at .venv)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux

# Verify Python version
python --version  # Should show Python 3.11+

# Install backend dependencies
pip install -r gerdsen_ai_server/requirements.txt

# For production dependencies
pip install -r gerdsen_ai_server/requirements_production.txt
```

**Important**: Always activate the virtual environment before running any Python commands!

## Key Commands

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
# ALWAYS activate virtual environment first!
source .venv/bin/activate

cd gerdsen_ai_server
python src/main.py  # Run the Flask server on port 5000
```

### Python Dependencies
- Main backend: `gerdsen_ai_server/requirements.txt`
- Production: `gerdsen_ai_server/requirements_production.txt`
- Development: `requirements_dev.txt`
- macOS specific: `requirements_macos.txt`

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
   - Achieved: 50-110 tokens/sec depending on chip
   - Achieved: <5s model loading with memory mapping
   - Achieved: <200ms first token latency when warmed
   
2. **Model Formats**: Supports MLX format with safetensors for optimal performance
   - MLX provides best performance on Apple Silicon
   - Memory-mapped loading reduces memory footprint by 20-30%
   
3. **Real-time Communication**: Uses Flask-SocketIO for WebSocket connections
   - Sub-50ms latency for status updates
   - Automatic reconnection on connection loss
   
4. **Security**: Production focus on input validation and API hardening
   - Pydantic models for all request/response validation
   - Rate limiting and request size limits
   - Bearer token authentication
   
5. **Performance**: Production-ready performance metrics
   - 84 passing tests covering unit, integration, and performance
   - Handles concurrent requests with proper queuing
   - Automatic thermal throttling detection and adaptation

## Development Notes

- **Current Sprint**: Production MVP (v1.0.0) - Hardening for deployment
- **Architecture**: Modular design with clear separation of concerns
- **Patterns**: Factory pattern for extensibility, strategy pattern for model loaders
- **Testing**: 84+ tests with >80% coverage on critical paths
- **Deployment**: Supports development, staging, and production configurations

### Production MVP Checklist
When implementing production features:
1. Ensure backward compatibility with existing API
2. Add comprehensive input validation
3. Include unit and integration tests
4. Document configuration options
5. Update deployment guides

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

## Production Readiness Guidelines

### When Adding Production Features

1. **Gunicorn Configuration**
   - Question: What's the optimal worker count for Apple Silicon?
   - Consider: CPU cores, memory limits, model sizes
   - Test: Load testing with concurrent requests

2. **Input Validation**
   - Question: What are all possible attack vectors?
   - Implement: Pydantic models for type safety
   - Validate: Model IDs, token limits, temperature ranges

3. **Health Checks**
   - Question: What constitutes "healthy" for our service?
   - Include: Model loading status, memory usage, GPU availability
   - Design: Kubernetes-compatible liveness and readiness probes

4. **CI/CD Pipeline**
   - Question: What should block a deployment?
   - Include: Tests, linting, type checking, security scans
   - Automate: Version bumping and changelog generation

5. **API Documentation**
   - Question: What do developers need to integrate successfully?
   - Generate: OpenAPI spec from code
   - Include: Authentication, rate limits, error codes

### Production Deployment Priorities
1. **Reliability** over features
2. **Security** over convenience
3. **Performance** with measurement
4. **Documentation** as code