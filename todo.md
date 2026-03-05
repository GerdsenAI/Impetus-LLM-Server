# Impetus-LLM-Server Roadmap

## Completed

### v1.0 Core Server ✓
- [x] Flask app factory (`create_app()`) with blueprint registration
- [x] OpenAI-compatible API (`/v1/chat/completions`, `/v1/models`, `/v1/completions`)
- [x] MLX model loader with memory-mapped loading, auto-download from HuggingFace
- [x] Streaming SSE and non-streaming JSON responses
- [x] Model management routes (`/api/models/load`, `/unload`, `/list`, `/download`, `/discover`, `/recommended`)
- [x] Model warmup service (pre-loading, async warmup, kernel compilation tracking)
- [x] Download manager with progress callbacks and WebSocket updates
- [x] Benchmark service (per-model perf testing, history, cross-model comparison)
- [x] KV cache manager for multi-turn conversations
- [x] Health routes (`/api/health`, `/live`, `/ready`, `/status`, `/metrics`)
- [x] Hardware monitoring (`/api/hardware/info`, `/metrics`, `/performance-mode`)
- [x] WebSocket real-time events (model status, hardware metrics, download progress, inference stats)
- [x] Pydantic v2 settings with `IMPETUS_` env var prefix
- [x] Error recovery system (`with_error_recovery` decorator, structured error responses)
- [x] macOS menu bar app (rumps + PyObjC): server manager, permissions, onboarding, single-instance lock
- [x] React 18 + Vite dashboard with real-time Socket.IO connection
  - [x] `HardwareMonitor` — chip info, P/E core layout, per-core CPU usage bars (color-coded), memory, thermal state
  - [x] `PerformanceMetrics` — Recharts real-time line charts (CPU%, memory%), request count, tokens generated, avg latency cards
  - [x] `ModelManager` — load/unload models, status display, memory usage per model
  - [x] `ModelBrowser` — discover + download models from HuggingFace
  - [x] `ChatInterface` — multi-turn chat with model selector, RAG toggle, conversation history
  - [x] `DocumentUpload` — file reader, document ingestion, collection management for RAG
  - [x] `ConnectionStatus`, `ErrorBoundary`, `Header` — connection indicator, error recovery, nav
  - [x] Three.js / R3F / drei still in `package.json` (vestigial — not imported by any component)
- [x] Gunicorn + eventlet production server, WSGI entry point
- [x] DMG and standalone `.app` installers
- [x] CI/CD: GitHub Actions (ruff, mypy, pytest, frontend build, Trivy, integration tests)

### Phase 1: Embeddings + Vector Store ✓
- [x] Hybrid ANE/GPU compute dispatcher (`compute_dispatcher.py`)
- [x] MLX embedding model loader (`mlx_embedding_loader.py`) + embedding converter
- [x] `/v1/embeddings` endpoint with OpenAI-compatible schema
- [x] ChromaDB v1.5 local embedded vector store (`vector_store.py`)
- [x] Document ingestion endpoint (`POST /api/documents/ingest`)
- [x] Similarity search endpoint (`POST /api/documents/search`)
- [x] Collection management endpoints (list, info, delete)
- [x] Text chunking utility (`document_chunker.py`)
- [x] Embedding bridge for ChromaDB (`embedding_bridge.py`)
- [x] Unit + integration tests (chunker, vector store, documents API)

### Phase 2: RAG Pipeline + Chat UI ✓
- [x] Naive RAG pipeline (`rag_pipeline.py`): query ChromaDB → inject context → generate
- [x] `use_rag`, `rag_collection`, `context_documents` fields on ChatCompletionRequest
- [x] RAG context injection in `/v1/chat/completions`
- [x] ChatInterface component with model selector + RAG toggle
- [x] DocumentUpload component with file reader + collection management
- [x] RAG pipeline tests (unit + integration with Flask test client)

### Phase 3: Quality Hardening ✓
- [x] Fix `request.json` mutation bug in `completions()`
- [x] Remove `continue-on-error` on linting/type checking in CI
- [x] Consolidate dev toolchain: replaced black + isort with ruff format
- [x] Updated dev dependencies, pyproject.toml, CI (Python 3.13, Node 22)
- [x] Docker base images updated (node:22-alpine, python:3.13-slim)
- [x] Fixed frontend issues exposed by strict CI (antd → lucide-react, unused imports, tsconfig)

### Phase 3.5: Runtime Bug Fixes + Docs ✓
- [x] Fix: Pydantic `Settings` rejecting `.env` vars — added `extra="ignore"` to `model_config`
- [x] Fix: `_load_model_internal` returning bare int instead of dict → `TypeError` on insufficient memory
- [x] Fix: Memory check used `memory.percent > 75%` (unreliable on macOS) + hardcoded 8GB — now estimates from disk, checks available GB
- [x] Symlinked local MLX model (`Qwen3-4B-Instruct-2507-MLX-4bit`) for testing
- [x] End-to-end verified: server → model load → chat completion (OpenAI-compatible response)
- [x] Updated all docs: CLAUDE.md, QUICKSTART.md, README.md, TROUBLESHOOTING.md, API_DOCUMENTATION.md
- [x] Added API key auto-generation docs, local model loading guide, updated model tables
- [x] Created `test_server.sh` end-to-end test script

---

## In Progress

### Phase 4: Testing & Release Prep
- [x] Increase test coverage to 80% backend (achieved 80.57%, 432 tests)
- [x] Add Playwright E2E tests for dashboard (23 tests, 4 spec files)
- [x] Performance regression benchmarks vs v1.0.2 (MetricsCalculator, perf_baselines.json)
- [ ] DMG/standalone app packaging with ChromaDB bundled
- [ ] Test ChromaDB in sandboxed macOS app (file permissions)
- [ ] Security scan (Trivy, zero critical vulns)

### Phase 5: v2.0 Release
- [ ] Changelog and release notes
- [ ] Migration guide (v1.x → v2.0)
- [ ] Final doc review + version bump
- [ ] Tag v2.0.0 release

---

## Dependency Upgrades (Staged)

### Safe Upgrades (do anytime)
- [ ] mlx 0.28→0.31, mlx-lm 0.26→0.30 (perf improvements)
- [ ] flask 3.0→3.1, pydantic 2.8→2.12, flask-socketio 5.3→5.6
- [ ] loguru, sentencepiece, requests (patch bumps)
- [ ] ruff 0.6→0.15, mypy 1.11→1.19, pip-audit, safety, pre-commit
- [ ] numpy 2.3→2.4, psutil 7.0→7.2, flask-cors 6.0→6.0.2 (minor/patch)

### Breaking Upgrades (require code changes)
- [ ] huggingface-hub 0.34→1.x + transformers 4.55→5.x (coordinated; `use_auth_token`→`token`, `requests`→`httpx`)
- [ ] gunicorn 23→25 (eventlet worker deprecated; migrate to `gevent` or `gthread`)
- [ ] pyobjc-core/Cocoa 11→12 (match macOS SDK)
- [ ] pytest 8→9, pytest-cov 5→7

### Frontend Breaking Upgrades (staged)
- [ ] **Stage 1 — Build tooling:** vite 5→7, @vitejs/plugin-react 4→5, eslint 9→10
- [ ] **Stage 2 — React ecosystem:** react 18→19, react-dom, @react-three/fiber 8→9, drei 9→10
- [ ] **Stage 3 — UI libraries:** framer-motion→motion, recharts 2→3, three 0.165→0.183

### Strategic Concerns
1. **Eventlet is deprecated.** Gunicorn 26.0 will remove the eventlet worker. Migrate to `gevent` (short-term) or FastAPI + Uvicorn (long-term).
2. **rumps is dormant.** Last release Oct 2022. Monitor for macOS compatibility issues.

---

## Deferred — Build When Triggered

### Core ML ANE Embeddings
> **Trigger:** Embedding latency is a bottleneck or batch workloads exceed acceptable time.
- [x] ComputeDispatcher, hardware detection (done)
- [ ] Benchmark: target 3-5ms ANE vs 20-30ms GPU
- [ ] Graceful fallback to GPU when ANE unavailable

### FastAPI Migration
> **Trigger:** Flask blocks async inference, HTTP/2, or WebSocket scaling. Also triggered by Gunicorn removing eventlet worker.
- [ ] Migrate Flask Blueprints → FastAPI APIRouter
- [ ] Replace Gunicorn + eventlet with Uvicorn ASGI
- [ ] Async streaming SSE for `/v1/chat/completions`
- [ ] Update SocketIO, menubar, CI, packaging, tests

### Frontend Modernization
> **Trigger:** Dashboard exceeds ~4,000 lines or needs multi-page navigation.
- [ ] React 18→19 coordinated upgrade (R3F, drei, types)
- [ ] Zustand v5, TanStack Query v5, TanStack Router v1
- [ ] Tailwind CSS v4, eliminate `any` types

### Advanced RAG
> **Trigger:** Naive RAG validates demand and retrieval quality needs improvement.
- [ ] Hybrid search (BM25 + dense vector)
- [ ] Cross-encoder reranking
- [ ] Agentic RAG with multi-retriever patterns
- [ ] Qdrant migration (when vectors exceed 50M)

### Observability & Monitoring
> **Trigger:** Multi-user deployment or production debugging needs instrumentation.
- [ ] OpenTelemetry, Prometheus metrics, distributed tracing

---

## Research Reference

All research documents in `docs/research/`:
- Architecture Blueprint, Quick Reference Card
- Framework comparison (FastAPI, Litestar, Quart)
- Vector DB evaluation (ChromaDB, Qdrant, LanceDB)
- Compute deep-dive (MLX, ANE, M5)
- Frontend stack analysis, community health assessment

---

**Status:** v2.0 Phases 1–3.5 complete | Phase 4 (testing & packaging) next | v1.0.2 production stable
**Last Updated:** 2026-03-04
