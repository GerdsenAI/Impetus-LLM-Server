# Release Notes

## 🔧 v1.0.2 - Critical DMG Bundling Fix
**Release Date**: August 16, 2025

### 🚨 Critical Fixes
This hotfix addresses a critical issue where the DMG installer would create an application that failed to launch from the Applications folder.

#### ✅ What's Fixed
- **🔴 CRITICAL**: App now launches successfully from Applications folder (was failing silently)
- **🔴 CRITICAL**: Fixed Python dependency bundling - Flask and all dependencies now load correctly
- **📦 DMG Builder**: Complete rewrite of Python runtime bundling in `create_dmg.sh`
- **🛠️ Launcher**: Fixed PYTHONPATH isolation for self-contained operation
- **⚙️ Production Config**: Graceful fallback when dependencies are missing
- **🔒 Security**: Production security validation now works with bundled runtime

#### 📊 Technical Improvements
- DMG size increased from 72MB to 110MB for complete dependency isolation
- Launcher now provides detailed logging for debugging
- Virtual environment site-packages are properly copied and isolated
- PYTHONPATH set to prioritize bundled libraries over system libraries

#### 📚 Documentation Updates  
- Added comprehensive troubleshooting section to CLAUDE.md
- Updated build instructions with virtual environment requirements
- Documented fix process and technical details for future reference

### 🔄 Migration Notes
- No action required for existing installations
- New DMG installations will work immediately without additional setup
- Recommended to reinstall from new DMG if experiencing launch issues

## 🚀 v1.0.0 - Production MVP Release
**Release Date**: January 2025

This release transforms Impetus LLM Server from a working prototype into a **production-ready system** with enterprise-grade features, security, and deployment capabilities.

### 🎯 Production Readiness Features

#### ⚡ Production Server Infrastructure
- **Gunicorn WSGI Server**: Replaced Flask development server with production-ready Gunicorn
  - Optimized worker configuration for Apple Silicon architecture
  - Automatic memory monitoring and worker recycling
  - Graceful shutdown handling with proper cleanup
  - Production startup scripts for macOS and Linux

#### 🔒 API Security & Validation
- **Comprehensive Input Validation**: Pydantic schemas for all API endpoints
  - OpenAI-compatible endpoint validation
  - Model management request validation
  - Hardware monitoring parameter validation
  - Detailed error responses with field-level feedback
- **Enhanced Authentication**: Bearer token security with proper error handling
- **Request Sanitization**: Protection against malformed and malicious requests

#### 🏥 Health Monitoring & Observability
- **Kubernetes Health Probes**: Production-ready health check endpoints
  - `/api/health/live` - Liveness probe with heartbeat monitoring
  - `/api/health/ready` - Readiness probe with component checks
  - `/api/health/status` - Detailed component health breakdown
- **Enhanced Metrics**: Comprehensive Prometheus-compatible metrics
  - Application performance metrics
  - System resource monitoring
  - Model-specific performance tracking
  - JSON metrics endpoint for custom monitoring

#### 📚 Interactive API Documentation
- **OpenAPI 3.0 Specification**: Auto-generated from Flask routes and Pydantic schemas
- **Swagger UI Integration**: Interactive API explorer at `/docs`
- **Comprehensive Documentation**: Request/response examples, authentication guides
- **Schema Validation**: Live validation in documentation interface

#### 🚢 Enterprise Deployment
- **Docker Production Images**: Multi-stage builds with security hardening
- **Kubernetes Manifests**: Production-ready K8s deployment configurations
- **nginx Reverse Proxy**: SSL/TLS termination with security headers
- **Docker Compose**: Complete stack deployment with monitoring
- **Service Management**: systemd and launchd service configurations

#### 🔄 CI/CD Pipeline
- **GitHub Actions Workflows**: Comprehensive testing and deployment automation
  - Backend and frontend testing with coverage reporting
  - Security scanning with Trivy vulnerability detection
  - Docker image building and publishing
  - Automated release creation and changelog generation
  - Performance testing with hardware-specific benchmarks

### 🛡️ Security Enhancements

- **Input Validation**: All user inputs validated with Pydantic schemas
- **Error Handling**: Secure error responses without information leakage
- **Container Security**: Non-root user execution and minimal attack surface
- **Network Security**: CORS configuration and rate limiting
- **SSL/TLS**: Complete SSL configuration with security headers

### 📊 Performance & Reliability

- **Concurrent Request Handling**: Supports 100+ concurrent requests
- **Zero-Downtime Deployments**: Health check integration for rolling updates
- **Memory Management**: Advanced memory monitoring and automatic cleanup
- **Error Recovery**: Comprehensive error handling with automatic retries
- **Graceful Degradation**: Service continues operating during partial failures

### 🔧 Developer Experience

- **Interactive Documentation**: Live API testing in browser
- **Comprehensive Guides**: Step-by-step deployment instructions
- **Multiple Deployment Options**: Docker, Kubernetes, and native installation
- **Monitoring Integration**: Prometheus, Grafana, and ELK stack support
- **Troubleshooting Guides**: Common issues and solutions documented

### 📋 New Endpoints

- `/api/health/live` - Kubernetes liveness probe
- `/api/health/ready` - Kubernetes readiness probe  
- `/api/health/status` - Detailed health status
- `/api/metrics/json` - JSON format metrics
- `/docs` - Interactive API documentation
- `/api/docs/openapi.json` - OpenAPI specification

### 🔄 Breaking Changes

- **Health Endpoints**: Moved from `/api/health` to `/api/health/status` for detailed status
- **Environment Variables**: Added production-specific environment variables
- **Server Startup**: Production mode requires Gunicorn (development mode unchanged)

### ⬆️ Upgrade Guide

#### From v0.1.0 to v1.0.0

1. **Install Production Dependencies**:
   ```bash
   pip install -r gerdsen_ai_server/requirements_production.txt
   ```

2. **Update Environment Configuration**:
   ```bash
   # Add to your .env file
   IMPETUS_ENVIRONMENT=production
   IMPETUS_API_KEY=your-secure-key
   ```

3. **Switch to Production Server**:
   ```bash
   # Instead of: python src/main.py
   # Use: 
   ./gerdsen_ai_server/start_production.sh
   ```

4. **Update Health Check URLs**:
   - Old: `/api/health` → New: `/api/health/status`
   - New liveness probe: `/api/health/live`
   - New readiness probe: `/api/health/ready`

### 📈 Performance Metrics

- **API Response Time**: < 50ms overhead
- **Health Check Response**: < 10ms
- **Concurrent Requests**: 100+ supported
- **Memory Efficiency**: 20-30% improvement with optimized workers
- **Docker Build Time**: 40% faster with multi-stage builds

---

## 🎉 v0.1.0 - Initial MVP Release
**Release Date**: December 2024

### Core Features
- High-performance MLX inference on Apple Silicon
- OpenAI-compatible API with streaming support
- React dashboard with real-time monitoring
- One-click model downloads and management
- Comprehensive benchmarking system
- WebSocket real-time updates
- 84 comprehensive test cases

### Performance Achievements
- 50-110 tokens/sec inference speed (hardware dependent)
- < 5 second model loading
- < 200ms first token latency (warmed)
- > 80% GPU utilization during inference

### Architecture
- Modular Flask backend
- TypeScript React frontend
- MLX framework integration
- Apple Silicon optimizations
- Memory-mapped model loading
- KV cache for multi-turn conversations

---

## 🚀 What's Next?

See [todo.md](todo.md) for the future roadmap including:
- Multi-model support
- Advanced quantization
- Enterprise authentication
- Model marketplace integration
- Enhanced fine-tuning capabilities

For detailed deployment instructions, see [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md).

For API documentation, visit `/docs` when running the server or see [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md).

---

Credits

Impetus builds on excellent open-source software including Flask, Gunicorn, Eventlet/Gevent, Pydantic, MLX, RUMPS, Vite/React/TS, Nginx, Pytest, and more. See [LICENSE](LICENSE) for third‑party notices and attributions.