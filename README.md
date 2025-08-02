# Impetus LLM Server

**v1.0.0** - Production-ready local LLM server optimized for Apple Silicon, providing OpenAI-compatible API endpoints with enterprise-grade security, monitoring, and deployment capabilities.

## 📑 Table of Contents
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [Production Deployment](#-production-deployment)
- [Development](#-development)
- [Performance](#-performance)
- [Troubleshooting](#-troubleshooting)

## 🚀 Features

### Core Functionality
- **Apple Silicon Optimization**: Dynamic detection and optimization for M1, M2, M3, and M4 chips (including Pro, Max, and Ultra variants)
- **OpenAI-Compatible API**: Full compatibility with VS Code extensions (Cline, Continue, Cursor, etc.)
- **MLX Framework Integration**: Leverages Apple's MLX for optimal performance on unified memory architecture
- **Real-time Hardware Monitoring**: CPU, GPU, memory, and thermal state tracking with Metal performance metrics
- **WebSocket Updates**: Live performance metrics and system status broadcasting

### Model Management
- **Model Discovery**: Browse and download from curated list of optimized models
- **One-Click Download & Load**: Automatic model loading after download with progress tracking
- **Performance Benchmarking**: Measure actual tokens/second, first token latency, and GPU utilization
- **Smart Memory Management**: Automatic model unloading on memory pressure
- **Error Recovery**: Comprehensive error handling with automatic recovery strategies
- **KV Cache**: Optimized multi-turn conversation performance with key-value caching
- **Model Warmup**: Eliminate cold start latency with pre-compiled Metal kernels

### Production Features (v1.0.0)
- **Gunicorn Production Server**: Enterprise-grade WSGI server with worker management
- **API Documentation**: Interactive Swagger UI at `/docs` with auto-generated OpenAPI specs
- **Health Monitoring**: Kubernetes-compatible liveness and readiness probes
- **Input Validation**: Comprehensive Pydantic schema validation for all endpoints
- **CI/CD Pipeline**: Complete GitHub Actions workflows for testing and deployment
- **Container Support**: Docker and Kubernetes deployment configurations

### Developer Experience
- **Zero Configuration**: Works out of the box with sensible defaults
- **Environment Variables**: Full configuration through .env file
- **Comprehensive Logging**: Structured logs with Loguru
- **Enhanced Metrics**: Prometheus-compatible metrics with detailed breakdowns
- **CORS Support**: Configurable for web app integration
- **Security**: Bearer token authentication and request sanitization

## 📋 Requirements

### System Requirements
- **macOS**: 13.0+ on Apple Silicon (M1/M2/M3/M4 series)
- **Memory**: 8GB RAM minimum, 16GB+ recommended for larger models
- **Storage**: 10GB+ free space for models

### Software Requirements
- **Python**: 3.11+
- **Node.js**: 18+ with pnpm
- **MLX**: Installed automatically with pip

## 🛠 Installation

### Quick Install (Recommended)
```bash
# One-line installer
curl -sSL https://raw.githubusercontent.com/GerdsenAI/Impetus-LLM-Server/main/install.sh | bash

# Validate installation
impetus validate
```

### Install from Source
```bash
# Clone and install
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server
pip install -e .

# Run setup wizard
impetus setup
```

### Manual Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server
```

#### 2. Backend Setup
```bash
# Navigate to backend
cd gerdsen_ai_server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
```

#### 3. Frontend Setup
```bash
# Navigate to frontend (in new terminal)
cd impetus-dashboard

# Install dependencies
pnpm install
```

#### 4. VS Code Integration
Configure your AI extension with:
- **Base URL**: `http://localhost:8080`
- **API Key**: Your configured key from .env
- **Model**: Any loaded model ID (e.g., `mlx-community/Mistral-7B-Instruct-v0.3-4bit`)

## 🚀 Usage

### Quick Start
```bash
# Start the server
impetus server

# Or start directly
impetus-server
```

Access the dashboard at `http://localhost:5173`

### CLI Commands
```bash
# System validation
impetus validate

# Interactive setup
impetus setup

# Start server
impetus server

# List models
impetus models

# Show help
impetus --help
```

### Manual Start
```bash
# Terminal 1: Start backend
cd gerdsen_ai_server
source venv/bin/activate
python src/main.py

# Terminal 2: Start frontend
cd impetus-dashboard
pnpm dev
```

### API Endpoints

#### OpenAI-Compatible Endpoints
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completions (streaming supported)
- `POST /v1/completions` - Text completions

#### Model Management Endpoints
- `GET /api/models/discover` - Browse available models with performance estimates
- `POST /api/models/download` - Download model with auto-load option
- `GET /api/models/list` - List loaded models with benchmark status
- `POST /api/models/load` - Load a model into memory
- `POST /api/models/unload` - Unload a model from memory
- `POST /api/models/benchmark/{model_id}` - Run performance benchmark
- `GET /api/models/benchmark/{model_id}/history` - Get benchmark history
- `GET /api/models/cache/status` - Get KV cache statistics
- `POST /api/models/cache/clear` - Clear KV cache
- `GET/PUT /api/models/cache/settings` - Manage cache settings
- `POST /api/models/warmup/{model_id}` - Warm up model to eliminate cold start
- `GET /api/models/warmup/status` - Get warmup status for all models
- `POST /api/models/warmup/{model_id}/benchmark` - Benchmark cold vs warm performance

#### Hardware Monitoring Endpoints
- `GET /api/hardware/info` - Get hardware information
- `GET /api/hardware/metrics` - Get real-time metrics including GPU
- `GET /api/hardware/gpu/metrics` - Detailed GPU/Metal metrics
- `GET /api/hardware/optimization` - Get optimization recommendations
- `POST /api/hardware/performance-mode` - Set performance mode

#### Health Check Endpoints (v1.0.0)
- `GET /api/health/live` - Kubernetes liveness probe
- `GET /api/health/ready` - Kubernetes readiness probe
- `GET /api/health/status` - Detailed component health status
- `GET /api/health/metrics` - Prometheus-compatible metrics
- `GET /api/health/metrics/json` - JSON format metrics

#### Documentation Endpoints (v1.0.0)
- `GET /docs` - Interactive Swagger UI documentation
- `GET /api/docs/openapi.json` - OpenAPI 3.0 specification

### Configuration

Configure via `.env` file in `gerdsen_ai_server/`:

```bash
# Server
IMPETUS_HOST=0.0.0.0
IMPETUS_PORT=8080
IMPETUS_API_KEY=your-secret-key

# Models
IMPETUS_DEFAULT_MODEL=mlx-community/Mistral-7B-Instruct-v0.3-4bit
IMPETUS_MAX_LOADED_MODELS=3

# Performance
IMPETUS_PERFORMANCE_MODE=balanced  # efficiency, balanced, performance
IMPETUS_MAX_TOKENS=2048
IMPETUS_TEMPERATURE=0.7

# Logging
IMPETUS_LOG_LEVEL=INFO
```

## 🚀 Production Deployment

**v1.0.0** includes comprehensive production deployment capabilities with multiple deployment options.

### Quick Production Start
```bash
# Install production dependencies
cd gerdsen_ai_server
pip install -r requirements_production.txt

# Configure environment
cp .env.example .env
# Edit .env with IMPETUS_API_KEY and other settings

# Start production server
./start_production.sh
```

### Deployment Options

#### 1. Docker Compose (Recommended)
```bash
# Clone and configure
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server
cp .env.example .env

# Start complete stack
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f impetus-server
```

#### 2. Kubernetes
```bash
# Apply Kubernetes manifests
kubectl apply -f docs/kubernetes/

# Check deployment
kubectl get pods -n impetus-system
kubectl logs -f deployment/impetus-server -n impetus-system
```

#### 3. Native Installation with Gunicorn
```bash
# Install and configure
pip install -r requirements_production.txt

# Start with Gunicorn
gunicorn --config gunicorn_config.py wsgi:application

# Or use the startup script
./start_production.sh
```

### Production Features
- **Load Balancing**: nginx reverse proxy with SSL termination
- **Health Monitoring**: Kubernetes liveness and readiness probes
- **Auto-scaling**: Horizontal pod autoscaling based on CPU/memory
- **Security**: Input validation, CORS, rate limiting, SSL/TLS
- **Observability**: Prometheus metrics, structured logging, tracing

#### 4. Service Management
```bash
# macOS (launchd)
sudo cp service/impetus.plist /Library/LaunchDaemons/
sudo launchctl load /Library/LaunchDaemons/impetus.plist

# Linux (systemd)
sudo cp service/impetus.service /etc/systemd/system/
sudo systemctl enable impetus
sudo systemctl start impetus
```

#### 5. Health Monitoring
Monitor service health with built-in endpoints:
- `/health` - Basic health check
- `/api/hardware/metrics` - System metrics
- `/api/models/list` - Model status

### Docker Deployment (Experimental)
```bash
docker build -t impetus-llm-server .
docker run -p 8080:8080 -v ./models:/models impetus-llm-server
```

## 🔧 Development

### Project Structure
```
Impetus-LLM-Server/
├── gerdsen_ai_server/           # Backend (Flask + MLX)
│   ├── src/
│   │   ├── main.py             # Application entry point
│   │   ├── config/             # Configuration management
│   │   ├── routes/             # API endpoints
│   │   ├── model_loaders/      # Model loading infrastructure
│   │   ├── utils/              # Utilities and helpers
│   │   └── inference/          # Inference engines
│   ├── requirements.txt        # Python dependencies
│   └── .env.example           # Environment configuration
├── impetus-dashboard/          # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── App.tsx           # Main application
│   │   └── main.tsx          # Entry point
│   ├── package.json          # Node dependencies
│   └── vite.config.ts        # Vite configuration
├── CLAUDE.md                  # Development philosophy
├── README.md                  # This file
└── todo.md                    # Project roadmap
```

### Development Workflow
```bash
# Run tests
cd gerdsen_ai_server
pytest tests/

# Lint code
pnpm lint  # Frontend
ruff check src/  # Backend

# Type checking
pnpm tsc  # Frontend
mypy src/  # Backend
```

## 📊 Performance

### Expected Performance (7B Models)
- **M4 Series**: 80-120 tokens/second
- **M3 Series**: 60-100 tokens/second  
- **M2 Series**: 40-80 tokens/second
- **M1 Series**: 30-60 tokens/second
- **Model Loading**: <5 seconds with memory mapping
- **First Token**: <200ms when warmed up

### Optimization Features
- **MLX Framework**: Optimized for Apple Silicon unified memory
- **Dynamic Batching**: Automatic batch size optimization
- **Memory Management**: Smart model loading/unloading
- **Thermal Monitoring**: Automatic performance adjustment
- **Per-Core Monitoring**: Real-time CPU usage tracking
- **KV Cache**: LRU cache management for conversations
- **Model Warmup**: Pre-compilation and performance optimization

## 🛡 Security

- **API Key Authentication**: Bearer token authentication
- **CORS Configuration**: Controlled cross-origin access
- **Local Processing**: All data stays on your machine
- **No Telemetry**: Zero external data collection
- **Input Validation**: Comprehensive request validation

## 🐛 Troubleshooting

See our comprehensive [Troubleshooting Guide](TROUBLESHOOTING.md) for detailed solutions.

### Quick Diagnostics
```bash
# Run system validation
impetus validate

# Check server status
impetus server --check
```

### Common Issues
- **Installation problems**: See [Troubleshooting Guide](TROUBLESHOOTING.md#-installation-issues)
- **Connection errors**: See [Troubleshooting Guide](TROUBLESHOOTING.md#-connection-issues)
- **Model loading**: See [Troubleshooting Guide](TROUBLESHOOTING.md#-model-loading-issues)
- **Performance**: See [Troubleshooting Guide](TROUBLESHOOTING.md#-performance-issues)

For detailed solutions and advanced debugging, check the full [Troubleshooting Guide](TROUBLESHOOTING.md).

## 🙏 Acknowledgments

- **Apple MLX Team**: For the excellent ML framework for Apple Silicon
- **OpenAI**: For the API specification
- **VS Code AI Extensions**: For driving local LLM adoption

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for Apple Silicon**

