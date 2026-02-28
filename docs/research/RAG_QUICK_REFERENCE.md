# RAG & Vector Database Quick Reference
## Impetus-LLM-Server Implementation Guide

---

## Vector Database Selection Matrix

### For Impetus MVP (Embedded, Single-Machine)

**PRIMARY CHOICE: ChromaDB v1.5+**
- 25K GitHub stars, 432K weekly downloads
- 4x faster Rust rewrite (2025)
- Easiest to integrate (3 lines of Python)
- M1 8GB safe for ~1M vectors
- SQLite persistence, zero network latency
- Limitation: not for 50M+ vectors

**FALLBACK FOR PRODUCTION: Qdrant**
- 29K GitHub stars, proven enterprise-grade
- 4ms p50 latency, 24x compression (2025)
- GPU acceleration via Metal (MPS)
- Horizontal scaling via sharding
- Requires Docker/server deployment

**ALTERNATIVE FOR MULTIMODAL: LanceDB**
- 9.1K stars, Arrow-native efficiency
- 100x less memory than ChromaDB
- GPU indexing via MPS (M2 Max tested)
- Beta status (v0.27) approaching 1.0
- Future-proof for multimodal embeddings

---

## Embedding Model Selection Matrix

### For Impetus MVP

**PRIMARY: nomic-embed-text-v1.5**
- 137M parameters (fits M1 8GB)
- MTEB-beating: 62.39 (short), 85.53 (long)
- ~100ms per document latency
- Matryoshka: slice 768D → 256D on-the-fly
- 261MB model size (float16)

**FOR SPEED: all-MiniLM-L6-v2**
- 22M parameters (ultra-light)
- 20-30ms per document
- Fall-back for real-time search
- 44MB model size
- Lower quality (44 MTEB) but acceptable for fuzzy matches

**FOR HIGHEST QUALITY: e5-mistral-7b-4bit**
- 7B parameters (quantized 4-bit)
- Highest MTEB: 69.5+
- 500-800ms per document (batch offline)
- ~2GB size (requires M2 16GB)
- Best for critical retrieval (deployment guides, security docs)

**RECOMMENDATION:** Start with nomic-embed-v1.5. Upgrade to e5-mistral for high-stakes retrieval. Use all-MiniLM as fallback for real-time queries.

---

## RAG Pattern Selection

| Pattern | Latency | Quality | Complexity | MVP? |
|---------|---------|---------|-----------|------|
| **Naive RAG** | 50-100ms | 70% | Low | YES |
| **Advanced RAG** | 200-500ms | 85% | Medium | Month 2 |
| **Agentic RAG** | 500-2000ms | 95% | High | Month 4+ |

**MVP Path:** Naive RAG → Advanced RAG (reranking) → Agentic RAG

---

## Code & Doc Chunking Strategy

### Recommended: Recursive + Semantic Hybrid

**Split by structure (primary):**
- Python: class/function definitions (preserve signatures)
- Markdown: ## headings (keep code blocks with explanation)
- Config: section breaks

**Example chunk sizes:**
- Function body: 512 tokens
- Markdown section: 1024 tokens
- Class definition: 768 tokens
- Overlap: 10-20% (100-200 tokens)

**Tools:**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    separators=["\nclass ", "\ndef ", "\n\n", "\n", " "],
    chunk_size=512,
    chunk_overlap=100,
)
```

---

## Hybrid Search Stack (Advanced RAG)

```
User Query
  └─ [SPARSE] BM25 full-text search
       └─ [DENSE] Vector similarity search
            └─ [FUSION] Reciprocal Rank Fusion (RRF)
                 └─ [RERANK] ColBERT / BGE-M3 (optional)
                      └─ Top-5 results to LLM
```

**Performance:**
- Dense-only: 0.72 NDCG@10
- Sparse-only: 0.65 NDCG@10
- Hybrid (RRF): 0.81 NDCG@10 (+22% vs dense)
- Hybrid + ColBERT: 0.87 NDCG@10 (+21% vs RRF)

---

## Apple Silicon Memory & Performance

### M1 8GB Constraints (MVP Viable)

| Component | Memory | Notes |
|-----------|--------|-------|
| macOS + system | 2GB | Fixed |
| Flask + Python | 200MB | Baseline |
| MLX runtime | 500MB | On-demand |
| nomic-embed-v1.5 | 261MB | Float16 |
| ChromaDB (1M vecs) | 3GB | 768D vectors |
| **Total** | **6.2GB** | **1.8GB headroom** |

### M2 16GB Ideal (Production)

Supports concurrent requests, e5-mistral-7b loading, and GPU acceleration via MPS.

---

## Implementation Timeline

### Week 1-2: MVP Foundation
- [ ] Setup ChromaDB with PersistentClient
- [ ] Load nomic-embed-text-v1.5 via mlx-embedding-models
- [ ] Chunk codebase (CLAUDE.md, main.py, model_loaders.py)
- [ ] Test vector embedding pipeline

### Week 3: Naive RAG
- [ ] Implement `/v1/rag/index` endpoint (document ingestion)
- [ ] Implement `/v1/chat/completions?rag_mode=true` (query retrieval)
- [ ] Stream augmented LLM responses via SSE
- [ ] Benchmark latency (target: <150ms including LLM generation)

### Week 4: Advanced RAG
- [ ] Add query rewriting (LLM-based)
- [ ] Implement hybrid search (BM25 + vector)
- [ ] Add reranker (bge-reranker-base)
- [ ] Implement answer validation (grounding check)

### Week 5+: Agentic RAG & Production
- [ ] Multi-retriever agents (code search, wiki, docs)
- [ ] Tool-use patterns (AST search, grep, semantic search)
- [ ] Monitoring & observability (latency, hit rates)
- [ ] Optional: Qdrant cluster for high-scale deployments

---

## Key Metrics to Track

### Vector DB Health
- `vector_count`: Total indexed vectors
- `index_build_time`: Seconds to index new documents
- `query_latency_p50`: Milliseconds, target <30ms
- `retrieval_recall`: Top-5 retrieval accuracy

### RAG Pipeline
- `augmentation_latency`: Query → embedding → retrieval time
- `generation_latency`: With augmented context
- `answer_grounding_score`: % of answers grounded in context
- `user_satisfaction`: Feedback on answer quality

### Infrastructure
- `memory_usage`: GB of RAM consumed
- `cpu_utilization`: Percent during batch indexing
- `concurrent_requests`: Handle at least 5 simultaneous
- `disk_usage`: ChromaDB .db file size

---

## Critical Gotchas

1. **M1 8GB Limit:** Cannot run e5-mistral-7b without quantization; nomic-embed is safest.

2. **Chunking Matters:** Poor chunking kills RAG quality. Recursive + semantic hybrid outperforms fixed-length by 15-20%.

3. **Hybrid Search is Worth It:** +22% NDCG@10 vs. dense-only justifies 200ms latency overhead (reranking).

4. **Metadata is Essential:** Filter by file type, author, date to avoid stale docs in retrieval.

5. **Batch Embedding Bottleneck:** 1000 docs takes 50-80s on M1. Use ThreadPoolExecutor for parallel embedding.

6. **ChromaDB Scaling Ceiling:** Designed for MVP (~50M vectors max). Plan Qdrant migration path early.

7. **LLM Context Window:** Ensure retrieved chunks + original query fit in model context (2048+ tokens for most models).

---

## Cost & Infrastructure

### Embedded Deployment (MVP)
- **Compute:** Existing M1/M2 Mac (no additional cost)
- **Storage:** ~5GB for 1M vectors + codebase
- **Development:** 4-5 weeks engineer-time

### Server Deployment (Production)
- **Compute:** Docker container (4GB RAM, 2 CPU)
- **Storage:** 10GB SSD for 10M vectors
- **Bandwidth:** Negligible (local vector DB)
- **Monitoring:** CloudWatch / Prometheus

### Optional: Qdrant Cloud Scale
- **Free tier:** 1GB, cloud-hosted
- **Paid:** $25/month → $99/month Hybrid Cloud
- **Alternative:** Self-hosted Qdrant cluster (Kubernetes)

---

## File Locations in Impetus

**New service:** `gerdsen_ai_server/src/services/rag_service.py`
- RAG orchestration
- Vector DB lifecycle
- Query embedding

**New config:** `gerdsen_ai_server/src/config/rag_settings.py`
- Enable flag
- Model selection
- Chunking params

**New route:** `gerdsen_ai_server/src/routes/rag_api.py`
- `/v1/rag/index` — Ingest
- `/v1/rag/status` — Health
- `/v1/chat/completions?rag_mode=true` — Query

**Dependencies:** Add to `requirements.txt`
```
chromadb>=1.5.1
mlx-embedding-models>=0.1.0
sentence-transformers>=3.0.0  # For reranking
lancedb>=0.27  # For future multimodal
```

---

## Further Reading

- **Full Research:** `VECTOR_DB_RAG_RESEARCH.md` (634 lines, complete analysis)
- **ChromaDB Docs:** https://docs.trychroma.com/
- **Qdrant Docs:** https://qdrant.tech/documentation/
- **MLX Guide:** https://ml-explore.github.io/mlx/build/html/index.html
- **RAG Patterns Survey:** https://arxiv.org/html/2501.09136v3

---

**Last Updated:** February 27, 2026
**Status:** Ready for Development Sprint
