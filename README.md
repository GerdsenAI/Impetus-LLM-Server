# Impetus LLM Server

A high-performance local LLM server optimized for Apple Silicon, providing OpenAI-compatible API endpoints for VS Code integration and a premium web dashboard for model management.

## 🚀 Features

### Core Functionality
- **Apple Silicon Optimization**: Dynamic detection and optimization for M1, M2, M3, and M4 chips (including Pro, Max, and Ultra variants)
- **OpenAI-Compatible API**: Full compatibility with VS Code extensions (Cline, Continue, Cursor, etc.)
- **MLX Framework Integration**: Leverages Apple's MLX for optimal performance on unified memory architecture
- **Real-time Hardware Monitoring**: CPU per-core usage, memory, thermal state tracking
- **WebSocket Updates**: Live performance metrics and system status broadcasting

### Model Management
- **Multiple Format Support**: MLX, GGUF, and HuggingFace Hub models
- **Dynamic Loading/Unloading**: Manage multiple models with memory optimization
- **Auto-loading**: Models load on-demand for API requests
- **Performance Modes**: Efficiency, Balanced, and Performance modes

### Developer Experience
- **Zero Configuration**: Works out of the box with sensible defaults
- **Environment Variables**: Full configuration through .env file
- **Comprehensive Logging**: Structured logs with Loguru
- **Health Endpoints**: Prometheus-compatible metrics
- **CORS Support**: Configurable for web app integration

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

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Impetus-LLM-Server
```

### 2. Backend Setup
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

### 3. Frontend Setup
```bash
# Navigate to frontend (in new terminal)
cd impetus-dashboard

# Install dependencies
pnpm install
```

### 4. VS Code Integration
Configure your AI extension with:
- **Base URL**: `http://localhost:8080`
- **API Key**: Your configured key from .env
- **Model**: Any loaded model ID (e.g., `mlx-community/Mistral-7B-Instruct-v0.3-4bit`)

## 🚀 Usage

### Starting the Server
```bash
# Terminal 1: Start backend
cd gerdsen_ai_server
source venv/bin/activate
python src/main.py

# Terminal 2: Start frontend
cd impetus-dashboard
pnpm dev
```

Access the dashboard at `http://localhost:5173`

### API Endpoints

#### OpenAI-Compatible Endpoints
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completions (streaming supported)
- `POST /v1/completions` - Text completions
- `POST /v1/embeddings` - Generate embeddings

#### Hardware Monitoring Endpoints
- `GET /api/hardware/info` - Get hardware information
- `GET /api/hardware/metrics` - Get real-time metrics
- `GET /api/hardware/optimization` - Get optimization recommendations

#### Model Management Endpoints
- `POST /api/models/upload` - Upload and optimize models
- `GET /api/models/list` - List loaded models
- `POST /api/models/optimize` - Optimize existing models

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

### Optimization Features
- **MLX Framework**: Optimized for Apple Silicon unified memory
- **Dynamic Batching**: Automatic batch size optimization
- **Memory Management**: Smart model loading/unloading
- **Thermal Monitoring**: Automatic performance adjustment
- **Per-Core Monitoring**: Real-time CPU usage tracking

## 🛡 Security

- **API Key Authentication**: Bearer token authentication
- **CORS Configuration**: Controlled cross-origin access
- **Local Processing**: All data stays on your machine
- **No Telemetry**: Zero external data collection
- **Input Validation**: Comprehensive request validation

## 🐛 Troubleshooting

### Server Won't Start
- Verify Python 3.11+: `python3 --version`
- Check port 8080: `lsof -i :8080`
- Activate venv: `source venv/bin/activate`

### Models Won't Load
- Check available memory in Activity Monitor
- Verify MLX installation: `pip show mlx`
- Try smaller models first (4-bit quantized)

### Frontend Connection Issues
- Ensure backend is running on port 8080
- Check browser console for WebSocket errors
- Verify CORS settings in .env

### Performance Issues
- Monitor thermal state in dashboard
- Switch to efficiency mode if overheating
- Close other memory-intensive applications

## 🙏 Acknowledgments

- **Apple MLX Team**: For the excellent ML framework for Apple Silicon
- **OpenAI**: For the API specification
- **VS Code AI Extensions**: For driving local LLM adoption

## 📈 Next Steps

See [todo.md](todo.md) for the detailed roadmap and upcoming features.

---

**Built with ❤️ for Apple Silicon**

