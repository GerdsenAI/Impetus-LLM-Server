# Impetus LLM Server - Quick Start Guide

**v1.0.0** - Get up and running with production-ready Impetus in 5 minutes!

## Prerequisites

- macOS 13.0+ on Apple Silicon (M1/M2/M3/M4)
- Python 3.11+
- 8GB+ RAM (16GB recommended)
- 10GB+ free disk space

## Installation

### Option 1: Install from source (Recommended)

```bash
# Clone the repository
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the server
pip install -e .

# Install a model (Mistral 7B)
impetus --setup
```

### Option 2: Docker (Production Ready)

```bash
# Clone and start with Docker Compose
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server
docker-compose up -d

# Check status
docker-compose logs -f impetus-server
```

### Option 3: Quick install script

```bash
curl -sSL https://raw.githubusercontent.com/GerdsenAI/Impetus-LLM-Server/main/install.sh | bash
```

## First Run

1. **Start the server**:
   ```bash
   # Development mode
   impetus-server
   
   # Production mode (v1.0.0)
   cd gerdsen_ai_server
   ./start_production.sh
   ```

2. **Open the dashboard** in your browser:
   ```
   http://localhost:5173
   ```

3. **Test the API**:
   ```bash
   curl http://localhost:8080/v1/models
   ```

4. **View API Documentation** (v1.0.0):
   ```
   http://localhost:8080/docs
   ```

## Download Your First Model

1. **Via Dashboard**: 
   - Open http://localhost:5173
   - Click "Model Browser"
   - Select "Mistral 7B Instruct" 
   - Click "Download & Load"

2. **Via API**:
   ```bash
   curl -X POST http://localhost:8080/api/models/download \
     -H "Content-Type: application/json" \
     -d '{"model_id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit", "auto_load": true}'
   ```

## VS Code Integration

Configure your AI extension (Cline, Continue, Cursor):

- **Base URL**: `http://localhost:8080`
- **API Key**: `your-api-key` (from IMPETUS_API_KEY env var)
- **Model**: `mlx-community/Mistral-7B-Instruct-v0.3-4bit`

## Basic Configuration

Create `.env` file in project root:

```bash
# Server
IMPETUS_HOST=0.0.0.0
IMPETUS_PORT=8080
IMPETUS_API_KEY=your-secret-key

# Model
IMPETUS_DEFAULT_MODEL=mlx-community/Mistral-7B-Instruct-v0.3-4bit

# Performance
IMPETUS_PERFORMANCE_MODE=balanced
```

## Common Commands

```bash
# List loaded models
curl http://localhost:8080/api/models/list

# Check hardware info
curl http://localhost:8080/api/hardware/info

# Run benchmark
curl -X POST http://localhost:8080/api/models/benchmark/your-model-id

# Chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "your-model-id",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Run as a Service

### macOS (launchd)
```bash
# Install service
sudo cp service/impetus.plist /Library/LaunchDaemons/
sudo launchctl load /Library/LaunchDaemons/impetus.plist

# Start/stop
sudo launchctl start impetus
sudo launchctl stop impetus
```

### Linux (systemd)
```bash
# Install service
sudo cp service/impetus.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable impetus

# Start/stop
sudo systemctl start impetus
sudo systemctl stop impetus
```

## Troubleshooting

For common issues and solutions, see our comprehensive [Troubleshooting Guide](TROUBLESHOOTING.md).

Quick fixes:
- **Server won't start**: Check port 8080 with `lsof -i :8080`
- **Model won't load**: Try smaller 4-bit model, check memory
- **Performance issues**: Use `IMPETUS_PERFORMANCE_MODE=performance`
- **Connection errors**: Run `impetus validate` to check system

Need more help? Check the full [Troubleshooting Guide](TROUBLESHOOTING.md).

## Next Steps

- Read the [full documentation](README.md)
- Browse [available models](http://localhost:5173)
- Join our [community](https://github.com/GerdsenAI/Impetus-LLM-Server/discussions)

---

**Need help?** Open an issue at https://github.com/GerdsenAI/Impetus-LLM-Server/issues