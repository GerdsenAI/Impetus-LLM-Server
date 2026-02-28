# Compute Architecture Quick Reference Card
## Impetus-LLM-Server Modernization - One-Page Cheat Sheet

**Research Date**: February 27, 2026 | **Status**: Complete | **Confidence**: High

---

## The Bottom Line

```
Current: MLX GPU only for LLM inference
Future:  MLX GPU (primary) + Core ML ANE (embeddings) + M5 neural accelerators
Impact:  10-30× embedding speedup, 4× prefill speedup on M5, minimal overhead
Effort:  4-5 weeks development
```

---

## Hardware Capabilities (M-Series Macs)

| Component | What It Does | Best For | Throughput |
|---|---|---|---|
| **MLX GPU** | General ML inference | LLM decoding (all sizes) | 230+ tok/s |
| **Core ML ANE** | Specialized neural ops | Embeddings, small models | 20-40 tok/s (LLM), 3-5ms (embed) |
| **M5 GPU Neural Acc** | Matrix multiplication | Prefill (prompt processing) | 200-400 tok/s |

**Decision Rule**: ANE = embeddings ✓ | ANE = LLM ✗

---

## Quick Performance Comparison

### LLM Inference (Sustained)
- **MLX (M4 Max)**: 230 tok/s
- **MLX (M5)**: 300+ tok/s (4× faster prefill, same decode)
- **Core ML GPU**: 150 tok/s
- **Core ML ANE**: 20 tok/s ← Too slow!

### Embeddings (384-dim)
- **PyTorch CPU**: 150 ms ⚠
- **Core ML ANE**: 3-5 ms ✓ (30-50× speedup)
- **MLX GPU**: 20 ms ✓ (backup)

---

## What's Changed in 2025-2026

### M5 GPU Neural Accelerators (October 2025)
- NEW: Tensor cores (one per GPU core)
- BENEFIT: 4× speedup for matrix math
- REQUIREMENT: M5 or later
- EFFORT: Zero (MLX handles automatically)

### M4/M5 Quantization Support
- NEW: INT8 W8A8 mode on ANE (M4+)
- NEW: 6-bit palettization support
- BENEFIT: 3-4× speedup, 35% memory savings

---

## Three Implementation Options

### Option A: MLX Only (Current)
- Effort: 0 weeks
- Embedding latency: 20-30 ms (GPU)
- Pro: Simple, works on all M-series
- Con: Embedding not optimized

### Option B: Hybrid (Recommended)
- Effort: 4-5 weeks
- Embedding latency: 3-5 ms (ANE)
- LLM throughput: 230+ tok/s (GPU)
- Pro: Best embedding speed, MLX still primary
- Con: Adds complexity, requires hardware detection

### Option C: ANE-First (Not Recommended)
- Effort: 6-8 weeks
- Embedding latency: 3-5 ms ✓
- LLM throughput: 20 tok/s ✗
- Pro: Lower power consumption
- Con: LLM too slow; complex conversion

**RECOMMENDATION: Option B (Hybrid)**

---

## Implementation Phases (4-5 Weeks)

```
Week 1-2: Core ML Embedding Service
├─ Convert DistilBERT → Core ML
├─ Add POST /api/embeddings endpoint
└─ Benchmark: target < 10 ms per batch

Week 2-3: Hardware Detection
├─ Create ComputeDispatcher
├─ Route embeddings → ANE, LLM → GPU
└─ Fallback for M1/M2/M3 (no ANE)

Week 3-4: M5 Optimization
├─ Detect M5 GPU neural accelerators
├─ Enable mixed-precision quantization
└─ Benchmark: 4× prefill improvement

Week 4-5: Testing & Docs
├─ Unit tests (Core ML loader)
├─ Integration tests (dashboard)
└─ Benchmark script + guide
```

---

## Technology Stack Decision Matrix

**For LLM Inference**: Use **MLX** (GPU)
- Throughput: 230+ tok/s
- Maturity: Production-ready (v0.30.6)
- Community: Large, active
- Reason: Best sustained throughput, no ANE support needed

**For Embeddings**: Use **Core ML** (ANE)
- Latency: 3-5 ms (vs. 20 ms GPU)
- Memory: 6.6× less than PyTorch
- Maturity: Production-ready
- Reason: 10-30× speedup, optimal for ANE

**For Model Conversion**: Use **coremltools** (v9.0)
- Formats: PyTorch, ONNX, TensorFlow
- Quantization: INT4, INT8, palettization
- Maturity: Mature (enterprise adoption)
- Reason: Official tool, wide compatibility

**For ANE-Only Models**: Use **ANEMLL** (future iOS)
- Models: Pre-converted 1-3B LLMs
- Status: Beta (emerging)
- Use case: iOS client app (future)
- Reason: Not suitable for server today

---

## Key Constraints & Gotchas

### ANE Constraints
- **No FP32**: Use FP16 + CPU fallback for LayerNorm/softmax
- **No BF16**: Use M5 GPU neural accelerators instead
- **Memory limit**: ~75% of system RAM (hard-coded)
- **Memory layout**: Misalignment can cause 32× memory blowup
- **No dynamic shapes**: Prefer fixed tensor dimensions

### MLX Limitations
- **No ANE**: Mark "wontfix"; use Core ML for ANE workloads
- **GPU-only inference**: No training support in server context
- **Thread safety**: Single-model per thread (use Flask worker pool)

### Core ML Caveats
- **Model size**: Convert time increases with size (pre-compile at load)
- **Precision loss**: Test quantization accuracy (expect 0.5-2% loss)
- **iOS compatibility**: ANE available on iOS 15+ (track device minimum)

---

## Data Type Cheat Sheet

| Type | ANE | GPU | Best Use |
|---|---|---|---|
| **FP32** | ✗ | ✓ | CPU fallback only |
| **FP16** | ✓ | ✓ | Default, safe |
| **BF16** | ✗ | ✓ | M5 GPU (not ANE) |
| **INT8** | ✓ | ✓ | Weights + activations (fast on ANE) |
| **INT4** | ⚠ | ✓ | Weights only (better on GPU) |

---

## Code Snippet: Hardware Detection

```python
def get_compute_dispatcher():
    """Detect hardware & return optimizer"""
    chip = detect_apple_silicon_chip()  # M1, M4, M5, etc.
    has_ane = detect_apple_neural_engine()
    has_m5_neural_acc = chip.startswith("M5") or chip.startswith("A19")

    if has_ane:
        embedding_backend = CoreMLEmbeddingBackend()  # ANE
    else:
        embedding_backend = MLXEmbeddingBackend()  # GPU fallback

    if has_m5_neural_acc:
        lm_backend = MLXLoaderM5Optimized()  # Mixed-precision
    else:
        lm_backend = MLXLoaderStandard()  # Default quantization

    return HybridDispatcher(embedding_backend, lm_backend)
```

---

## Risk Summary (Quick Mitigation)

| Risk | Severity | Mitigation |
|---|---|---|
| Conversion failure | Medium | Test on DistilBERT first |
| ANE memory issues | Low | Validate tensor shapes |
| Accuracy loss > 1% | Low | A/B test quantization |
| M4 regression | Very Low | Benchmark M4 fallback |

---

## File References

| File | Purpose |
|---|---|
| `research_findings_...md` | Complete technical analysis (8,000+ words) |
| `RESEARCH_SUMMARY_...md` | Executive summary (key findings, phases, risks) |
| `COMPUTE_ARCHITECTURE_...md` | Reference tables (specs, benchmarks, comparisons) |
| `RESEARCH_DELIVERY_SUMMARY.txt` | Integration checklist + next steps |

---

## Links to Authoritative Sources

1. **ANE Specifications**: https://github.com/hollance/neural-engine
2. **M5 GPU Accelerators**: https://machinelearning.apple.com/research/exploring-llms-mlx-m5
3. **Core ML Llama 3.1**: https://machinelearning.apple.com/research/core-ml-on-device-llama
4. **MLX Status**: https://github.com/ml-explore/mlx/issues/18
5. **coremltools**: https://apple.github.io/coremltools/

---

## Decision Checklist

- [ ] Stakeholders agree on hybrid MLX + Core ML approach?
- [ ] M1/M2/M3 compatibility acceptable (graceful fallback)?
- [ ] Embedding latency target met (< 10 ms)?
- [ ] 4-5 week timeline feasible?
- [ ] Team familiar with coremltools + Core ML basics?
- [ ] Fallback plan if conversion fails (GPU-only embeddings)?

---

## Common Questions

**Q: Why not ANE for LLM?**
A: ANE throughput (20-40 tok/s) is 10× slower than GPU (230+ tok/s). ANE excels at small models and embeddings, not large LLM inference.

**Q: Do I need M5?**
A: No. M4 and earlier work fine (MLX GPU). M5 provides 4× prefill speedup via GPU neural accelerators.

**Q: Will this break existing users?**
A: No. Hybrid dispatch is transparent (hardware detection + fallback). M1/M2/M3 default to GPU embeddings.

**Q: How much faster are embeddings on ANE?**
A: 10-30× faster than CPU, 3-5× faster than GPU. Latency drops from 20 ms (GPU) to 3-5 ms (ANE).

**Q: What's the simplest implementation?**
A: Start with Core ML embedding service (2-3 weeks). Hardware dispatcher and M5 optimization come later.

---

**Last Updated**: February 27, 2026 | **Research Status**: Complete | **Ready for Stakeholder Review**
