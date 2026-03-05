# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Impetus-LLM-Server is a local LLM inference server optimized for Apple Silicon, providing an OpenAI-compatible API powered by MLX. It includes a native macOS menu bar app, a React dashboard with real-time hardware/performance monitoring, and production deployment tooling.

**Requirements**: macOS 14.0+ (Sonoma), Apple Silicon (M1+), Python 3.11+, 8GB RAM (16GB recommended)

## Development Commands

### Backend (Python/Flask)

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r gerdsen_ai_server/requirements.txt
pip install -r gerdsen_ai_server/requirements_dev.txt

# Run dev server (port 8080)
cd gerdsen_ai_server && python src/main.py

# Run production server (Gunicorn + eventlet)
python start_production.py

# Run menu bar app
python run_menubar.py
```

### Frontend (React/Vite)

```bash
cd impetus-dashboard
npm install
npm run dev       # Dev server on port 5173, proxies to :8080
npm run build     # TypeScript + Vite production build
npm run lint      # ESLint
```

### Testing

```bash
cd gerdsen_ai_server

# All tests
pytest tests/ -v

# Single test file
pytest tests/test_api_models.py -v

# With coverage (matches CI)
pytest tests/ -v --cov=src --cov-report=xml --cov-report=term

# By marker
pytest -m "not slow" -v
pytest -m integration -v
```

Test markers: `integration`, `unit`, `slow`

### Linting & Type Checking

```bash
cd gerdsen_ai_server

# Lint (ruff) - line length 120, targets py311
ruff check src/ tests/ --output-format=github

# Type check
mypy src/ --ignore-missing-imports

# Format (ruff replaces black + isort)
ruff format src/ tests/
ruff check --select I --fix src/ tests/
```

### Building for Distribution

```bash
# DMG installer (requires active venv)
source .venv/bin/activate
./installers/create_dmg.sh

# Standalone .app (self-contained, no system Python needed)
cd installers && ./macos_standalone_app.sh
```

## Architecture

### Request Flow

```
Client (curl/SDK/Dashboard) → Flask App (main.py:create_app)
  → openai_api.py blueprint (/v1/chat/completions, /v1/models)
    → Pydantic schema validation (schemas/openai_schemas.py)
      → MLXLoader (model_loaders/mlx_loader.py)
        → MLX inference on Apple Silicon GPU
          → Streaming SSE or JSON response
```

### Key Components

- **`gerdsen_ai_server/src/main.py`** — Flask app factory (`create_app()`). Registers all blueprints, initializes SocketIO (threading mode for Python 3.13 compat), manages app state (`loaded_models`, `metrics`).

- **`gerdsen_ai_server/src/routes/openai_api.py`** — Primary API surface. OpenAI-compatible `/v1/chat/completions` with streaming support and `/v1/models` listing. Handles both dict and Pydantic request objects.

- **`gerdsen_ai_server/src/model_loaders/`** — Model loading and inference. `mlx_loader.py` (primary MLX inference, memory-mapped, auto-downloads from HuggingFace, 4-bit/8-bit quantized models), `coreml_loader.py` (Core ML/ANE), `compute_dispatcher.py` (routes to best backend), `mlx_embedding_loader.py` + `embedding_converter.py` (embedding models).

- **`gerdsen_ai_server/src/config/settings.py`** — Pydantic settings classes (`ServerSettings`, `ModelSettings`, `InferenceSettings`, `HardwareSettings`). All overridable via `IMPETUS_` prefixed env vars.

- **`gerdsen_ai_server/src/menubar/`** — Native macOS menu bar app using rumps + PyObjC. `server_manager.py` manages server process lifecycle, `permissions_manager.py` handles macOS permissions, `onboarding.py` provides first-run tour.

- **`impetus-dashboard/`** — React 18 + Vite frontend with Socket.IO real-time updates, Recharts performance charts, and hardware monitoring. Three.js/R3F still in `package.json` but not currently used. Vite proxies `/api`, `/v1`, `/socket.io` to backend port 8080.

- **`gerdsen_ai_server/src/services/`** — Background services: `model_discovery.py` (HuggingFace search), `download_manager.py` (model downloads), `benchmark_service.py` (perf testing), `rag_pipeline.py` (RAG orchestration), `vector_store.py` (vector storage), `embedding_bridge.py` (embedding generation), `model_warmup.py` (pre-loading models).

- **`gerdsen_ai_server/src/inference/`** — KV cache management for multi-turn conversations (`kv_cache_manager.py`, `mlx_kv_generation.py`).

### Additional Route Blueprints

All registered in `create_app()`:
- `routes/models.py` — Model management (load/unload/list) at `/api/models`
- `routes/health.py` — Health endpoints (`/api/health`, `/api/health/live`, `/api/health/ready`, `/api/health/status`, `/api/metrics`, `/api/metrics/json`) at `/api`
- `routes/hardware.py` — Hardware info, GPU metrics, compute capabilities, performance mode at `/api/hardware`
- `routes/documents.py` — Document ingestion, semantic search, collection management at `/api/documents`
- `routes/websocket.py` — Socket.IO real-time handlers (registered separately via SocketIO, not as a blueprint)

### API Key Authentication

The server auto-generates a secure API key on the **first request** to any `/v1/*` endpoint. The key is printed to the server console:

```
🔑 Generated API key: impetus-<random-token>
💡 Save this key for future API requests!
```

- All subsequent `/v1/*` requests require `Authorization: Bearer <key>`
- The key changes every time the server restarts
- To set a persistent key, use the `IMPETUS_API_KEY` environment variable:
  ```bash
  IMPETUS_API_KEY=my-secret-key python gerdsen_ai_server/src/main.py
  ```
- The first request to `/v1/*` after startup (before auth is generated) will succeed without a key

### Loading Local MLX Models

Models are stored in `~/.impetus/models/`. To use existing MLX models from another location (e.g., LM Studio models), **symlink** them:

```bash
# Symlink a local model into the models directory
ln -sf "/path/to/your/Model-Name-MLX-4bit" "$HOME/.impetus/models/Model-Name-MLX-4bit"

# Then load via API
curl -X POST http://127.0.0.1:8080/api/models/load \
  -H "Content-Type: application/json" \
  -d '{"model_id": "Model-Name-MLX-4bit"}'
```

The model loader resolves paths as: `settings.model.models_dir / model_id` (for local names) or `settings.model.models_dir / model_id.replace('/', '_')` (for HuggingFace-style IDs like `mlx-community/Mistral-7B`). If the local path doesn't exist, it falls back to downloading from HuggingFace Hub.

### Production Entry Points

| Entry | Use |
|-------|-----|
| `gerdsen_ai_server/src/main.py` | Flask dev server |
| `gerdsen_ai_server/wsgi.py` | Gunicorn WSGI target (`wsgi:application`) |
| `start_production.py` | Production launcher script |
| `run_menubar.py` | Menu bar app (starts server internally) |

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`):
- **Backend**: ruff + mypy + pytest on Python 3.11/3.12/3.13, macOS runner
- **Frontend**: npm install + eslint + tsc + vite build, Ubuntu runner
- **Security**: Trivy vulnerability scanner
- **Integration**: Starts server, tests health/API endpoints (main branch + PRs)

## Key Conventions

- **API Compatibility**: All API changes must maintain OpenAI API compatibility. The `/v1/chat/completions` endpoint is the primary contract.
- **MLX-Only Inference**: This project uses Apple's MLX framework exclusively — no PyTorch/ONNX. MLX imports are guarded for non-macOS environments.
- **Pydantic Schemas**: All API request/response models live in `gerdsen_ai_server/src/schemas/`. Route handlers must handle both dict and Pydantic model inputs.
- **Environment Variables**: Server config uses `IMPETUS_` prefix (e.g., `IMPETUS_HOST`, `IMPETUS_PORT`).
- **Ruff Config**: Line length 120, target py311. Rules: E, F, W, I, N, UP, B, A, C4, PT, SIM, RUF. Ignores: E501, B008, RUF012. Defined in `pyproject.toml`.
- **Installers require macOS 14.0+** (Sonoma). All installer scripts in `installers/` enforce this minimum.

## Known Gotchas

- `sentencepiece` must be installed for tokenizer support — MLX model loading fails silently without it
- `eventlet` is required for WebSocket/Socket.IO — falls back to threading mode without it
- DMG/standalone app builds require an active virtual environment to properly bundle site-packages
- The bundled app's `launcher.sh` sets `PYTHONPATH` to isolate from system Homebrew paths
- Tests require `conftest.py` in `gerdsen_ai_server/tests/` for module namespace aliasing — without it, pytest can't resolve `src.*` imports
- Pydantic v2 is used — validators use `@field_validator` (not the deprecated `@validator`)
- The `.env` file must only contain `IMPETUS_`-prefixed vars, or the `Settings` class needs `extra="ignore"` in its `model_config` — otherwise Pydantic rejects unknown env vars and all route blueprints fail to register silently
- The API key is auto-generated on the first `/v1/*` request and printed to the server console — it changes on every restart (set `IMPETUS_API_KEY` for persistence)
- macOS reports high `memory.percent` due to filesystem caching — memory checks should use `available` GB rather than `percent` to avoid false rejections on Apple Silicon
