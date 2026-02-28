# Impetus LLM Server — v2.0 Modernization Roadmap

## Completed

### v1.0.2 — Production MVP (August 2025)
- [x] Flask + MLX inference engine (230+ tok/s on Apple Silicon)
- [x] OpenAI-compatible API with streaming SSE (/v1/chat/completions)
- [x] React 18 + Three.js dashboard with real-time monitoring
- [x] CI/CD pipeline (GitHub Actions: ruff, mypy, pytest, Trivy)
- [x] Gunicorn production server with health checks
- [x] macOS menu bar app (rumps + PyObjC) + DMG installer
- [x] 84+ tests passing

### chore/modernize — Research Phase (February 2026)
- [x] Architecture Blueprint (6-facet research, 14 documents, PDF)
- [x] Framework ecosystem analysis (FastAPI, Litestar, Quart, Starlette)
- [x] Vector DB & RAG evaluation (ChromaDB, Qdrant, LanceDB)
- [x] Compute architecture analysis (MLX GPU, Core ML ANE, M5 neural accelerators)
- [x] Frontend modernization research (Zustand, TanStack, Tailwind v4)
- [x] Community health & viability assessment
- [x] Research consolidated in docs/research/
- [x] Repository cleanup and organization

---

## Priority — Ship First

### Phase 1: Embeddings + Vector Store (Weeks 1-2)
- [ ] Implement /v1/embeddings endpoint (MLX GPU, ~20ms latency)
- [ ] Integrate ChromaDB v1.5+ as local embedded vector store
- [ ] Add document ingestion endpoint (POST /v1/documents)
- [ ] Add similarity search endpoint
- [ ] Embedding model: nomic-embed-text-v1.5 (137M params, 261MB)
- [ ] Memory profiling on M1 8GB (budget: ~6.2GB total)
- [ ] Unit + integration tests for each new endpoint

### Phase 2: RAG Pipeline + Chat UI (Weeks 3-4)
- [ ] Naive RAG: query ChromaDB → inject context → generate
- [ ] Add context_documents support to /v1/chat/completions
- [ ] Simple chat interface component in dashboard
- [ ] Document upload UI in dashboard
- [ ] E2E RAG flow test (upload → embed → query → response)

### Phase 3: Quality Hardening (Weeks 5-6)
- [ ] Fix: remove continue-on-error on linting/type checking in CI
- [ ] Fix: request.json mutation bug in openai_api.py completions()
- [ ] Increase test coverage to 80% backend
- [ ] Add Playwright E2E tests for dashboard
- [ ] Performance regression benchmarks vs v1.0.2

### Phase 4: Polish + v2.0 Release (Weeks 7-8)
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
- [ ] Convert embedding model to Core ML via coremltools v9
- [ ] Build ComputeDispatcher (route embeddings → ANE, LLM → GPU)
- [ ] Hardware detection (M1/M2/M3/M4/M5 capabilities)
- [ ] Benchmark: target 3-5ms ANE vs 20-30ms GPU
- [ ] Graceful fallback to GPU when ANE unavailable
- Research: docs/research/research_findings_npu_gpu_cpu_compute_architecture.md

### FastAPI Migration
> **Trigger:** Flask blocks a specific feature (e.g., true async inference, HTTP/2, or WebSocket scaling beyond Socket.IO).
- [ ] Migrate routes from Flask Blueprints to FastAPI APIRouter
- [ ] Replace Gunicorn + eventlet with Uvicorn ASGI
- [ ] Async streaming SSE for /v1/chat/completions
- [ ] Rewrite SocketIO integration
- [ ] Update menubar app server launcher
- [ ] Update CI, DMG packaging, all tests
- Research: docs/research/research_framework_ecosystem.md

### Frontend Modernization
> **Trigger:** Dashboard exceeds ~4,000 lines, or complex multi-page navigation is needed.
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

**Status:** v2.0 development planned | v1.0.2 production stable
**Last Updated:** February 2026
