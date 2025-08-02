# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Development Philosophy

This project emphasizes systematic problem-solving through:
1. **Socratic Method**: Question assumptions and seek evidence before implementing
2. **OODA Loop**: Observe → Orient → Decide → Act in iterative cycles
3. **Evidence-Based Decisions**: Measure, don't guess - especially for performance

## Project Overview

Impetus-LLM-Server is a **production-ready** machine learning model management system optimized for Apple Silicon hardware. The project consists of a Python backend server and a React frontend dashboard, focusing on MLX model management and inference.

### Status: Production Ready v1.0.0 ✅
The project has successfully completed the Production MVP Sprint and is now **enterprise-ready** with:
- ✅ Gunicorn production server with Apple Silicon optimization
- ✅ Complete CI/CD pipeline with GitHub Actions
- ✅ Comprehensive API validation with Pydantic schemas
- ✅ Kubernetes-compatible health check endpoints
- ✅ Interactive OpenAPI documentation with Swagger UI
- ✅ Enterprise deployment guides (Docker, Kubernetes, native)
- ✅ Security hardening and input validation
- ✅ Production monitoring and observability

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

# Development mode
python src/main.py  # Run the Flask server on port 8080

# Production mode (v1.0.0)
./start_production.sh  # Run with Gunicorn
```

### Python Dependencies
- Main backend: `gerdsen_ai_server/requirements.txt`
- Production: `gerdsen_ai_server/requirements_production.txt`
- Development: `requirements_dev.txt`
- macOS specific: `requirements_macos.txt`

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
  - openai_schemas.py: OpenAI-compatible endpoint validation
  - model_schemas.py: Model management validation
  - hardware_schemas.py: Hardware monitoring validation
  - health_schemas.py: Health check validation
- **model_loaders/**: Factory pattern for loading different model formats (GGUF, MLX, CoreML, ONNX, PyTorch, SafeTensors)
- **inference/**: Unified inference system with base classes
- **auth/**: OpenAI authentication integration
- **utils/**: Configuration, logging, security utilities, and validation helpers
  - validation.py: Request validation decorators and utilities
  - openapi_generator.py: Auto-generated API documentation

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
   - 84+ passing tests covering unit, integration, and performance
   - Handles 100+ concurrent requests with Gunicorn workers
   - Automatic thermal throttling detection and adaptation
   - Sub-10ms health check response times

6. **Production Features (v1.0.0)**: Enterprise-grade deployment capabilities
   - Gunicorn production server with worker management
   - Interactive API documentation with Swagger UI at /docs
   - Kubernetes-compatible health probes (liveness/readiness)
   - Comprehensive input validation with Pydantic schemas
   - CI/CD pipeline with automated testing and deployment
   - Docker and Kubernetes deployment configurations

## Development Notes

- **Status**: Production Ready v1.0.0 ✅ - Enterprise deployment ready
- **Architecture**: Modular design with clear separation of concerns
- **Patterns**: Factory pattern for extensibility, strategy pattern for model loaders
- **Testing**: 84+ tests with >80% coverage on critical paths
- **Deployment**: Production-ready with multiple deployment options (Docker, Kubernetes, native)

### Production Features Completed ✅
1. ✅ Gunicorn production server with worker management
2. ✅ Comprehensive input validation with Pydantic schemas
3. ✅ Kubernetes-compatible health check endpoints
4. ✅ Interactive API documentation with OpenAPI generation
5. ✅ CI/CD pipeline with automated testing and deployment
6. ✅ Enterprise deployment guides and configurations

### Development Guidelines
When adding new features:
1. Always use Pydantic schemas for request/response validation
2. Add health checks for new components in /api/health/status
3. Update OpenAPI documentation with proper examples
4. Include comprehensive unit and integration tests
5. Follow security best practices (input validation, authentication)
6. Update deployment configurations if needed

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

## Production Readiness Guidelines (✅ COMPLETED)

All production features have been successfully implemented in v1.0.0:

### ✅ Completed Production Features

1. **✅ Gunicorn Configuration** - Optimal worker count for Apple Silicon
   - Implemented: Auto-detected worker configuration based on CPU cores
   - Configured: Memory monitoring and automatic worker recycling
   - Tested: Load testing with 100+ concurrent requests

2. **✅ Input Validation** - Comprehensive security and type safety
   - Implemented: Pydantic models for all API endpoints
   - Validated: Model IDs, token limits, temperature ranges, all parameters
   - Protected: Against malformed requests and injection attacks

3. **✅ Health Checks** - Kubernetes-compatible monitoring
   - Implemented: /api/health/live (liveness), /api/health/ready (readiness)
   - Included: Model loading status, memory usage, GPU availability
   - Designed: Production-ready probe configurations

4. **✅ CI/CD Pipeline** - Automated testing and deployment
   - Implemented: GitHub Actions workflows for testing, security, deployment
   - Included: Tests, linting, type checking, security scans with Trivy
   - Automated: Docker builds, performance testing, release generation

5. **✅ API Documentation** - Interactive developer experience
   - Generated: Auto-generated OpenAPI 3.0 specs from Pydantic schemas
   - Included: Authentication, rate limits, error codes, live testing
   - Available: Interactive Swagger UI at /docs

6. **✅ Enterprise Deployment** - Multiple deployment options
   - Implemented: Docker Compose, Kubernetes manifests, native installation
   - Configured: nginx reverse proxy, SSL/TLS, monitoring stack
   - Documented: Comprehensive deployment and troubleshooting guides

### Production Deployment Status
✅ **Reliability** - Health checks, graceful degradation, error recovery  
✅ **Security** - Input validation, authentication, container hardening  
✅ **Performance** - 100+ concurrent requests, sub-10ms health checks  
✅ **Documentation** - Interactive API docs, deployment guides, troubleshooting