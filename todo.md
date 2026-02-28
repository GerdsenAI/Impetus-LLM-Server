# Impetus-LLM-Server v2.0 Roadmap

## Completed

### Phase 1: Embeddings + Vector Store ✓
- [x] Hybrid ANE/GPU compute dispatcher (`compute_dispatcher.py`)
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
- [x] Fix `request.json` mutation bug in `completions()` — now builds proper Pydantic model
- [x] Remove `continue-on-error` on linting/type checking in CI (enforces quality gates)
- [x] Consolidate dev toolchain: dropped black + isort, replaced with ruff format
- [x] Updated `requirements_dev.txt` (ruff 0.15.4, mypy 1.19.1, pip-audit 2.10.0, safety 3.5.2, pre-commit 4.2.0, etc.)
- [x] Removed `[tool.black]` from pyproject.toml, migrated ruff config to `[tool.ruff.lint]`
- [x] Aligned `pyproject.toml` dependency bounds with installed versions (gunicorn, flask-cors, psutil, pydantic-settings)
- [x] Applied safe Python dependency bumps (mlx 0.31, mlx-lm 0.30.7, flask 3.1, pydantic 2.12, etc.)
- [x] Updated Docker base images: node:22-alpine, python:3.13-slim, pnpm → npm
- [x] Updated CI: Node 22, Python 3.13 added to test matrix, pnpm → npm
- [x] Fixed pre-existing frontend issues exposed by removing continue-on-error (antd → lucide-react, unused imports, tsconfig)

---

## TOP PRIORITY — Dependency Updates

Versions verified against PyPI/npm registries on 2026-02-27. "Installed" = what's in the venv/node_modules today.

### Python — Safe Upgrades (no breaking changes)

| Package | Installed | Latest | Bump | Notes |
|---------|-----------|--------|------|-------|
| mlx | 0.28.0 | 0.31.0 | minor | Apple Silicon ML perf improvements |
| mlx-lm | 0.26.3 | 0.30.7 | minor | LLM inference; test generate()/load() signatures |
| flask | 3.0.3 | 3.1.3 | patch | Security fixes, backwards-compatible |
| pydantic | 2.8.2 | 2.12.5 | minor | Bug fixes, new features |
| pydantic-settings | 2.4.0 | 2.13.1 | minor | Backwards-compatible |
| flask-socketio | 5.3.6 | 5.6.0 | minor | Backwards-compatible |
| chromadb | 1.5.2 | 1.5.2 | current | Already at latest |
| loguru | 0.7.2 | 0.7.3 | patch | Bug fix |
| sentencepiece | 0.2.0 | 0.2.1 | patch | Bug fix |
| requests | 2.32.4 | 2.32.5 | patch | Bug fix |
| eventlet | 0.36.1 | 0.40.4 | minor | **Deprecated** — maintenance-only, plan migration |

### Python — Breaking Upgrades (require code changes)

| Package | Installed | Latest | Bump | Risk | Key Breaking Changes |
|---------|-----------|--------|------|------|---------------------|
| huggingface-hub | 0.34.4 | 1.5.0 | **MAJOR** | HIGH | `requests` → `httpx`, `use_auth_token` → `token`, `hf_transfer` removed, `Repository` class removed. [Migration guide](https://huggingface.co/docs/huggingface_hub/v1.1.0/concepts/migration) |
| transformers | 4.55.2 | 5.2.0 | **MAJOR** | HIGH | TF/Flax dropped, `use_auth_token` → `token`, `TRANSFORMERS_CACHE` → `HF_HOME`, tokenizer consolidation. [Migration guide](https://github.com/huggingface/transformers/blob/main/MIGRATION_GUIDE_V5.md) |
| gunicorn | 23.0.0 | 25.1.0 | **MAJOR** | HIGH | **Eventlet worker deprecated** (removal in 26.0), Python 3.10+ required. Migrate to `gevent` or `gthread` worker |
| numpy | 2.3.2 | 2.4.2 | minor | LOW | Already on NumPy 2.x, incremental update |
| psutil | 7.0.0 | 7.2.2 | minor | LOW | Already on psutil 7.x |
| flask-cors | 6.0.1 | 6.0.2 | patch | LOW | Already on flask-cors 6.x |
| pyobjc-core | 11.1 | 12.1 | **MAJOR** | MED | macOS SDK binding updates |
| pyobjc-framework-Cocoa | 11.1 | 12.1 | **MAJOR** | MED | Must match pyobjc-core version |

### Python — Dev Tools

| Tool | Installed | Latest | Bump | Notes |
|------|-----------|--------|------|-------|
| ruff | 0.6.3 | 0.15.4 | minor | 2026 style guide, 800+ rules. **Replaces black + isort** |
| mypy | 1.11.2 | 1.19.1 | minor | Python 3.13 wheels, incremental improvement |
| black | 24.8.0 | 26.1.0 | **MAJOR** | **Drop in favor of `ruff format`** |
| isort | 5.13.2 | 8.0.0 | **MAJOR** | **Drop in favor of `ruff check --select I`** |
| pytest | 8.3.2 | 9.0.2 | **MAJOR** | Native TOML config, tab progress display |
| pytest-cov | 5.0.0 | 7.0.0 | **MAJOR** | Coverage plugin update |
| pip-audit | 2.6.3 | 2.10.0 | minor | Security scanning improvements |
| pre-commit | 3.8.0 | — | — | Check latest |

**Action: Consolidate dev toolchain** — Replace `black` + `isort` with `ruff format` + `ruff check --select I`. Reduces 5 tools to 2 (ruff + mypy).

### Node.js — Safe Upgrades

| Package | Installed | Latest | Bump | Notes |
|---------|-----------|--------|------|-------|
| socket.io-client | 4.8.3 | 4.8.3 | current | Already at latest |
| clsx | 2.1.1 | 2.1.1 | current | Already at latest |
| typescript | 5.9.3 | 5.9.3 | current | Already at latest |
| typescript-eslint | 8.56.1 | 8.56.1 | current | Stabilized from alpha |
| eslint-plugin-react-hooks | 5.2.0 | 7.0.1 | **MAJOR** | React 19 ecosystem alignment |
| lucide-react | 0.400.0 | 0.575.0 | minor | Icon renames possible, check usage |

### Node.js — Breaking Upgrades (staged)

**Stage 1 — Build tooling (independent of React):**

| Package | Installed | Latest | Bump | Key Changes |
|---------|-----------|--------|------|-------------|
| vite | 5.4.21 | 7.3.1 | **MAJOR x2** | Sass legacy removed, Environment API, splitVendorChunkPlugin removed |
| @vitejs/plugin-react | 4.3.1* | 5.1.4 | **MAJOR** | Paired with Vite 7 |
| eslint | 9.39.3 | 10.0.2 | **MAJOR** | eslintrc **completely removed**, flat config only, Node.js >=20.19 required |
| globals | 15.15.0 | 17.3.0 | **MAJOR x2** | ESLint compat |

**Stage 2 — React ecosystem (coordinated upgrade):**

| Package | Installed | Latest | Bump | Key Changes |
|---------|-----------|--------|------|-------------|
| react | 18.3.1 | 19.2.4 | **MAJOR** | `forwardRef` removed, `defaultProps` removed for FC, React Compiler, Actions, `use()` hook. [Upgrade guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide) |
| react-dom | 18.3.1 | 19.2.4 | **MAJOR** | Must match react version |
| @types/react | 18.3.28 | 19.2.14 | **MAJOR** | Must match react version |
| @types/react-dom | 18.3.7 | 19.2.3 | **MAJOR** | Must match react-dom version |
| @react-three/fiber | 8.18.0 | 9.5.0 | **MAJOR** | R3F v9 requires React 19. Node → ThreeElement types |
| @react-three/drei | 9.122.0 | 10.7.7 | **MAJOR** | Drei v10 requires R3F v9 |
| @types/three | 0.165.0 | 0.183.1 | minor | Must match three version |

**Stage 3 — UI libraries (independent):**

| Package | Installed | Latest | Bump | Key Changes |
|---------|-----------|--------|------|-------------|
| framer-motion | 11.18.2 | 12.34.3 | **MAJOR** | **Renamed to `motion`**. Import from `motion/react`. Drop-in replacement API |
| recharts | 2.15.4 | 3.7.0 | **MAJOR** | Internal props removed, `activeIndex` removed, `accessibilityLayer` default changed. [Migration guide](https://github.com/recharts/recharts/wiki/3.0-migration-guide) |
| three | 0.165.0* | 0.183.1 | minor | 18 minor releases; API deprecations per release |

### Docker / CI Base Images

| Image | Current | Recommended | Reason |
|-------|---------|-------------|--------|
| node:18-alpine | **EOL** (April 2025) | **node:22-alpine** | Node 18 is end-of-life. Node 22 is Active LTS (EOL April 2027) |
| python:3.11-slim | EOL May 2026 | **python:3.13-slim** | Project already runs Python 3.13.12 locally. 3.11 EOL in ~3 months |
| CI: Python 3.11/3.12 matrix | current | Add **3.13** | Match local dev environment |
| CI: Node 18 | current | **Node 22** | Match Docker base image |

### Strategic Concerns

1. **Eventlet is deprecated.** Gunicorn 26.0 will remove the eventlet worker entirely. Options:
   - Short-term: migrate to `gevent` worker
   - Long-term: FastAPI + Uvicorn (already in deferred roadmap)

2. **rumps is dormant.** Last release October 2022 (3+ years). No Python 3.13 updates. Monitor for macOS compatibility issues.

3. **huggingface-hub 1.x + transformers 5.x** must be upgraded together. Both rename `use_auth_token` → `token` and share breaking patterns.

---

## Next Priority — Ship

### Phase 3 Remaining
- [ ] Increase test coverage to 80% backend
- [ ] Add Playwright E2E tests for dashboard
- [ ] Performance regression benchmarks vs v1.0.2

### Phase 4: Polish + v2.0 Release
- [ ] DMG/standalone app packaging with ChromaDB bundled
- [ ] Test ChromaDB in sandboxed macOS app (file permissions)
- [ ] Update CLAUDE.md, README, API documentation
- [ ] Changelog, release notes, migration guide (v1.x → v2.0)
- [ ] Security scan (Trivy, zero critical vulns)
- [ ] Tag v2.0.0 release

---

## Deferred — Build When Triggered

### Core ML ANE Embeddings
> **Trigger:** Profiling shows embedding latency is a bottleneck, or batch embedding workloads exceed acceptable time.
- [x] Convert embedding model to Core ML via coremltools v9
- [x] Build ComputeDispatcher (route embeddings → ANE, LLM → GPU)
- [x] Hardware detection (M1/M2/M3/M4/M5 capabilities)
- [ ] Benchmark: target 3-5ms ANE vs 20-30ms GPU
- [ ] Graceful fallback to GPU when ANE unavailable
- Research: docs/research/research_findings_npu_gpu_cpu_compute_architecture.md

### FastAPI Migration
> **Trigger:** Flask blocks a specific feature (e.g., true async inference, HTTP/2, or WebSocket scaling beyond Socket.IO). **Also triggered by:** Gunicorn removing eventlet worker in v26.0.
- [ ] Migrate routes from Flask Blueprints to FastAPI APIRouter
- [ ] Replace Gunicorn + eventlet with Uvicorn ASGI
- [ ] Async streaming SSE for /v1/chat/completions
- [ ] Rewrite SocketIO integration
- [ ] Update menubar app server launcher
- [ ] Update CI, DMG packaging, all tests
- Research: docs/research/research_framework_ecosystem.md

### Frontend Modernization
> **Trigger:** Dashboard exceeds ~4,000 lines, or complex multi-page navigation is needed.
- [ ] React 18 → 19 upgrade (coordinated with R3F, drei, types)
- [ ] Vite 5 → 7, ESLint 9 → 10 (build tooling)
- [ ] framer-motion → motion (package rename)
- [ ] recharts 2 → 3
- [ ] Zustand v5 for state management
- [ ] TanStack Query v5 for server state + caching
- [ ] TanStack Router v1 for type-safe routing
- [ ] Tailwind CSS v4 migration
- [ ] Eliminate `any` types across frontend codebase
- Research: docs/research/frontend_modernization_research.md

### Advanced RAG
> **Trigger:** Naive RAG validates user demand and retrieval quality needs improvement.
- [ ] Hybrid search (BM25 + dense vector)
- [ ] Cross-encoder reranking
- [ ] Agentic RAG with multi-retriever patterns
- [ ] Qdrant migration (when vectors exceed 50M)
- Research: docs/research/VECTOR_DB_RAG_RESEARCH.md

### Observability & Monitoring
> **Trigger:** Deployed as multi-user service, or debugging production issues requires deeper instrumentation.
- [ ] OpenTelemetry instrumentation
- [ ] Prometheus metrics export
- [ ] Distributed tracing
- Research: docs/research/Impetus-LLM-Server-Architecture-Blueprint.md

---

## Research Reference

All research documents: `docs/research/`
- **Impetus-LLM-Server-Architecture-Blueprint.md** — Comprehensive blueprint + PDF
- **QUICK_REFERENCE_CARD.md** — One-page decision summary
- **research_framework_ecosystem.md** — Framework comparison (FastAPI, Litestar, Quart)
- **VECTOR_DB_RAG_RESEARCH.md** — Vector DB evaluation (ChromaDB, Qdrant, LanceDB)
- **research_findings_npu_gpu_cpu_compute_architecture.md** — Compute deep-dive (MLX, ANE, M5)
- **frontend_modernization_research.md** — Frontend stack analysis
- **community-health-viability-research.md** — Ecosystem health assessment
- **COMPUTE_ARCHITECTURE_DATA_TABLES.md** — Hardware reference tables
- **RESEARCH_SUMMARY_COMPUTE_ARCHITECTURE.md** — Compute exec summary

---

**Status:** v2.0 Phase 1-3 complete | Phase 4 next | v1.0.2 production stable
**Last Updated:** 2026-02-28 (Phase 3 quality hardening complete)
