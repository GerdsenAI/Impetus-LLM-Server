# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Impetus-LLM-Server is a local LLM inference server optimized for Apple Silicon, providing an OpenAI-compatible API powered by MLX. It includes a native macOS menu bar app, a React+Three.js dashboard, and production deployment tooling.

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

# Format
black src/ tests/        # line length 120
isort src/ tests/
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

- **`impetus-dashboard/`** — React 18 + Vite frontend with Three.js 3D visualization, Socket.IO real-time updates, and Recharts metrics. Vite proxies `/api`, `/v1`, `/socket.io` to backend port 8080.

- **`gerdsen_ai_server/src/services/`** — Background services: `model_discovery.py` (HuggingFace search), `download_manager.py` (model downloads), `benchmark_service.py` (perf testing), `rag_pipeline.py` (RAG orchestration), `vector_store.py` (vector storage), `embedding_bridge.py` (embedding generation), `model_warmup.py` (pre-loading models).

- **`gerdsen_ai_server/src/inference/`** — KV cache management for multi-turn conversations (`kv_cache_manager.py`, `mlx_kv_generation.py`).

### Additional Route Blueprints

All registered in `create_app()`:
- `routes/models.py` — Model management (load/unload/list) at `/api/models`
- `routes/health.py` — Health endpoints (`/api/health`, `/api/health/live`, `/api/health/ready`, `/api/health/status`, `/api/metrics`, `/api/metrics/json`) at `/api`
- `routes/hardware.py` — Hardware info, GPU metrics, compute capabilities, performance mode at `/api/hardware`
- `routes/documents.py` — Document ingestion, semantic search, collection management at `/api/documents`
- `routes/websocket.py` — Socket.IO real-time handlers (registered separately via SocketIO, not as a blueprint)

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
- **Frontend**: pnpm install + eslint + tsc + vite build, Ubuntu runner
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
