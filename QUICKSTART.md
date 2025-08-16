# Impetus LLM Server - Quick Start Guide

v1.0.0 – Get up and running with Impetus in under 60 seconds

## For End Users - Just Download and Run!

### 1. Download Impetus
- Go to [Releases](https://github.com/GerdsenAI/Impetus-LLM-Server/releases)
- Download `Impetus-Standalone-1.0.0.dmg`
- Open the DMG file
- Drag **Impetus** to your Applications folder

### 2. Run Impetus
- Double-click **Impetus** in Applications
- The dashboard will open automatically in your browser
- That's it! No setup, no terminal, no dependencies needed

### 3. Download Your First Model
- In the dashboard, click "Model Browser"
- Choose a model (we recommend **Mistral 7B** to start)
- Click "Download & Load"
- Once loaded, you're ready to use AI locally!

## System Requirements

- **macOS** 13.0 or later
- **Apple Silicon** Mac (M1, M2, M3, or M4)
- **8GB RAM** minimum (16GB recommended)
- **10GB disk space** for models

## Using Impetus with VS Code

Configure your AI extension (Continue.dev, Cursor, Cline, etc.):
- **API Base**: `http://localhost:8080/v1`
- **API Key**: Check `~/Library/Application Support/Impetus/config/server.env`
- **Model**: Use the model ID from the dashboard

## For Developers

### Building from Source

```bash
# Clone the repository
git clone https://github.com/GerdsenAI/Impetus-LLM-Server.git
cd Impetus-LLM-Server

# Build the standalone app
cd installers
./macos_standalone_app.sh

# Your app is ready in build_standalone/Impetus.app
```

### Development Mode (backend only)

```bash
python3 -m venv .venv
source .venv/bin/activate
# Install developer requirements
pip install -r gerdsen_ai_server/requirements_dev.txt

# Run the Flask dev server (development only)
python gerdsen_ai_server/src/main.py

# Or run production-grade locally (recommended)
./gerdsen_ai_server/start_production.sh
# or
python ./start_production.py
```

### Docker Deployment

```bash
# Using the Docker installer
cd installers
./docker_installer.sh

# Or manually with docker-compose
docker-compose up -d
```

## API Quick Reference

### Test the API
```bash
# Health and docs
curl -sS http://localhost:8080/api/health/status | jq
open http://localhost:8080/docs

# List available models (OpenAI-compatible)
curl -sS http://localhost:8080/v1/models | jq

# Chat completion (replace YOUR_API_KEY)
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "mistral-7b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### API Documentation
Open http://localhost:8080/docs for interactive API documentation

## Configuration

The app stores all data in:
```
~/Library/Application Support/Impetus/
├── config/server.env    # Configuration and API key
├── models/              # Downloaded models
├── cache/               # Model cache
└── logs/                # Application logs
```

## Troubleshooting

### App Won't Open
- Right-click Impetus and select "Open" (first time only)
- Check Console.app for errors
 - If macOS blocks the app, go to System Settings → Privacy & Security → Security → "Open Anyway" for Impetus.

### Port Already in Use
```bash
# Find what's using port 8080
lsof -i :8080

# Kill the process if needed
kill -9 <PID>
```

### Performance Issues
- Close other heavy applications
- Try a smaller model (4-bit versions)
- Check Activity Monitor for resource usage
 - In the menubar app, try Performance Mode → Efficiency

### View Logs
```bash
tail -n 200 "${HOME}/Library/Application Support/Impetus/logs/impetus_server.log"
```

## Recommended Models

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **Mistral 7B** | 4GB | Fast | Great | General use |
| **Llama 3 8B** | 5GB | Fast | Excellent | Conversations |
| **Phi-3 Mini** | 2GB | Very Fast | Good | Quick tasks |
| **Qwen 2.5** | 4GB | Fast | Great | Code & technical |

## Next Steps

- Explore more models in the Model Browser
- Check out the [API Documentation](http://localhost:8080/docs)
- Join our [GitHub Discussions](https://github.com/GerdsenAI/Impetus-LLM-Server/discussions)
- Report issues on [GitHub](https://github.com/GerdsenAI/Impetus-LLM-Server/issues)

---

**Enjoy your local AI!** 🚀