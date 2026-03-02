# Impetus LLM Server - Quick Start Guide

v1.0.2 – Get up and running with Impetus in under 60 seconds

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

## API Key

The server **auto-generates** a secure API key on the first request to any `/v1/*` endpoint. The key is printed to the server console:

```
🔑 Generated API key: impetus-<random-token>
💡 Save this key for future API requests!
```

- All subsequent `/v1/*` requests require `Authorization: Bearer <key>`
- The key **changes every restart** — check the server console output each time
- To set a **persistent** key, use the environment variable:
  ```bash
  IMPETUS_API_KEY=my-secret-key python gerdsen_ai_server/src/main.py
  ```

## Using Impetus with VS Code

Configure your AI extension (Continue.dev, Cursor, Cline, etc.):
- **API Base**: `http://localhost:8080/v1`
- **API Key**: Check the server console output for the auto-generated key, or set `IMPETUS_API_KEY` for a persistent key
- **Model**: Use the model ID from the dashboard or `curl http://127.0.0.1:8080/v1/models`

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
# Health check (no auth needed)
curl -sS http://localhost:8080/api/health/status | jq
open http://localhost:8080/docs

# First request to /v1/* triggers API key generation (check server console)
curl -sS http://127.0.0.1:8080/v1/models | jq

# Save the key printed in the server console, then use it:
export IMPETUS_KEY="impetus-<your-generated-key>"

# List models
curl -sS -H "Authorization: Bearer $IMPETUS_KEY" \
  http://127.0.0.1:8080/v1/models | jq

# Load a model
curl -X POST http://127.0.0.1:8080/api/models/load \
  -H "Content-Type: application/json" \
  -d '{"model_id": "Qwen3-4B-Instruct-2507-MLX-4bit"}'

# Chat completion
curl -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $IMPETUS_KEY" \
  -d '{
    "model": "Qwen3-4B-Instruct-2507-MLX-4bit",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 512
  }'
```

### API Documentation
Open http://localhost:8080/docs for interactive API documentation

## Loading Local MLX Models

If you already have MLX models downloaded (e.g., from LM Studio), symlink them into the models directory instead of re-downloading:

```bash
# Symlink an existing model
ln -sf "/path/to/your/Model-Name-MLX-4bit" "$HOME/.impetus/models/Model-Name-MLX-4bit"

# Then load it via the API
curl -X POST http://127.0.0.1:8080/api/models/load \
  -H "Content-Type: application/json" \
  -d '{"model_id": "Model-Name-MLX-4bit"}'
```

Models must be in MLX safetensors format with a `config.json` file.

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

All models should be MLX-format safetensors (e.g., from `mlx-community` or `lmstudio-community` on HuggingFace).

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| **Qwen3-4B-Instruct-2507-MLX-4bit** | 2.1GB | Very Fast | Quick tasks, testing |
| **DeepSeek-R1-0528-Qwen3-8B-MLX-4bit** | 4.3GB | Fast | Reasoning |
| **Qwen3-14B-MLX-4bit** | 7.8GB | Fast | Higher quality |
| **Qwen3-Coder-30B-A3B-Instruct-MLX-4bit** | 16GB | Moderate | Code review & generation |
| **Phi-4-reasoning-plus-MLX-4bit** | 7.7GB | Fast | Reasoning tasks |
| **Magistral-Small-2509-MLX-4bit** | 13GB | Moderate | General use |

## Next Steps

- Explore more models in the Model Browser
- Check out the [API Documentation](http://localhost:8080/docs)
- Join our [GitHub Discussions](https://github.com/GerdsenAI/Impetus-LLM-Server/discussions)
- Report issues on [GitHub](https://github.com/GerdsenAI/Impetus-LLM-Server/issues)

---

**Enjoy your local AI!** 🚀