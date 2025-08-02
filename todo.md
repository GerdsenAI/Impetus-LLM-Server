# Impetus LLM Server - Premium Apple Silicon Implementation

## Vision
Create the absolute best local LLM server for Apple Silicon that:
- Runs as a lightweight menubar service
- Provides RAG capabilities with vector database
- Offers a premium web interface for management
- Maximizes Apple Silicon performance
- Feels native and polished

## Development Methodology
Following CLAUDE.md principles:
- **Socratic Method**: Question assumptions before implementing
- **OODA Loop**: Observe → Orient → Decide → Act iteratively
- **Evidence-Based**: Measure performance, don't guess

## Phase 1: Core Cleanup & Foundation (Week 1)

### OBSERVE: Current State Analysis
**Questions to answer first:**
- What components are actually being used vs legacy code?
- Which dependencies are critical vs optional?
- What is the current memory footprint of each component?
- How does the current architecture impact performance?

### Remove Unnecessary Components
- [ ] **OBSERVE**: Audit all directories and their purposes
- [ ] **QUESTION**: Which components are referenced in active code?
- [ ] **DECIDE**: Create deletion priority list based on evidence
- [ ] **ACT**: Delete research directory (`src/research/`)
- [ ] **ACT**: Remove debug tools (`src/debug/puppeteer_tools.py`)
- [ ] **ACT**: Clean up bundled import helper legacy code
- [ ] **MEASURE**: Verify no functionality broken after removal

### Restore Core Functionality
**Key Questions:**
- What vector database provides best performance/size ratio on Apple Silicon?
- How many documents can we handle with unified memory architecture?
- What chunk size optimizes retrieval speed vs accuracy?

- [ ] **OBSERVE**: Benchmark ChromaDB vs Faiss on M-series chips
- [ ] **ORIENT**: Analyze memory patterns during vector operations
- [ ] **DECIDE**: Choose vector DB based on performance data
- [ ] **ACT**: Implement lightweight vector database
- [ ] **ACT**: Create document processing pipeline for RAG
- [ ] **MEASURE**: Document indexing speed and retrieval latency

### Menubar Service Architecture
**Critical Questions:**
- PyObjC vs Swift: What are the maintenance implications?
- How much memory should the menubar service consume at idle?
- What's the optimal IPC mechanism for server communication?

- [ ] **OBSERVE**: Profile existing menubar apps for best practices
- [ ] **DECIDE**: Technology choice based on maintainability and performance
- [ ] **ACT**: Create native macOS menubar app
- [ ] **ACT**: Implement service daemon with measured startup time
- [ ] **MEASURE**: Memory usage, CPU at idle, startup latency

## Phase 2: Premium Web Interface (Week 2)

### Dashboard Enhancement
**Design Questions:**
- What UI patterns do premium macOS apps use?
- How can we minimize reflow and maximize perceived performance?
- What's the optimal update frequency for real-time metrics?

### OODA Implementation:
1. **OBSERVE**: Study Raycast, Linear, Arc browser UI patterns
2. **ORIENT**: Map UI requirements to performance constraints
3. **DECIDE**: Choose rendering strategy (virtual scrolling, lazy loading)
4. **ACT**: Implement with continuous performance monitoring

- [ ] **MEASURE**: Frame time must be < 16ms for 60fps
- [ ] **TEST**: UI responsiveness under model inference load
- [ ] Real-time performance metrics visualization
- [ ] Model management interface with drag-and-drop
- [ ] RAG document management interface

## Phase 3: Apple Silicon Optimization (Week 3)

### Performance Targets & Evidence
**Key Questions:**
- What's the actual memory bandwidth on M1 vs M2 vs M3?
- How does batch size affect tokens/sec on each chip?
- What's the optimal memory allocation strategy for MLX?

### Implementation with Measurement:
- [ ] **BASELINE**: Current inference speed per model size
- [ ] **EXPERIMENT**: Memory-mapped loading impact
- [ ] **MEASURE**: Unified memory allocation patterns
- [ ] **OPTIMIZE**: Based on profiling data, not assumptions
- [ ] Implement model caching with persistence
- [ ] Add memory-mapped model loading
- [ ] **VERIFY**: Achieve > 50 tokens/sec on M1, > 100 on M3

### Advanced Features
**Evidence Required:**
- Profile multi-model memory sharing opportunities
- Measure quantization impact on quality vs speed
- Test batching efficiency at different sizes

## Phase 4: RAG Excellence (Week 4)

### Vector Database Performance
**Critical Metrics:**
- Query latency vs document count (graph the relationship)
- Memory usage scaling with index size
- Accuracy vs retrieval speed trade-offs

### OODA for RAG:
1. **OBSERVE**: Current retrieval patterns and bottlenecks
2. **ORIENT**: Understand user query patterns
3. **DECIDE**: Optimal indexing strategy based on usage
4. **ACT**: Implement with continuous monitoring

- [ ] **BENCHMARK**: Hybrid search vs pure vector search
- [ ] **MEASURE**: Metadata filtering performance impact
- [ ] **TEST**: Incremental indexing overhead
- [ ] Implement hybrid search (vector + keyword)
- [ ] Add metadata filtering capabilities

## Phase 5: Premium Features (Week 5)

### User Experience Validation
**Questions Before Implementation:**
- What features do users actually use? (analytics data)
- What's the cognitive load of each feature?
- How do we measure feature success?

### Enterprise Features
**Security Considerations:**
- What attack vectors exist in our architecture?
- How do we balance security with performance?
- What's the performance cost of encryption?

## Phase 6: Distribution & Polish (Week 6)

### Packaging Strategy
**Key Decisions Based on Evidence:**
- Code signing impact on startup time?
- Auto-update mechanism failure rates?
- Optimal DMG size vs compression?

### Quality Assurance
- [ ] **MEASURE**: Crash rate per 1000 hours of usage
- [ ] **PROFILE**: Memory leaks over extended operation
- [ ] **TEST**: Performance degradation over time
- [ ] Create signed macOS app bundle
- [ ] Implement auto-update mechanism

## Performance Targets (Evidence-Based)

### Metrics with Measurement Methods
- **Memory usage**: < 500MB idle (measured via Activity Monitor)
- **Startup time**: < 3 seconds (timed from launch to ready)
- **Model loading**: < 5 seconds for 7B (logged timestamps)
- **Inference**: > 50 tokens/sec on M1 (measured over 1000 tokens)
- **RAG retrieval**: < 100ms for 1M documents (95th percentile)
- **UI responsiveness**: < 16ms frame time (Chrome DevTools)

### Continuous Monitoring
- Set up performance regression tests
- Create dashboards for key metrics
- Alert on performance degradation

## MVP Definition (2 Weeks)

### Success Criteria (Measurable)
1. **Performance**: 50+ tokens/sec with Mistral 7B on M1
2. **Memory**: < 4GB total with model loaded
3. **Latency**: First token < 500ms
4. **Reliability**: 0 crashes in 24-hour test
5. **Installation**: < 2 minutes from download to running

### MVP OODA Loop
1. **OBSERVE**: Current local LLM server landscape
2. **ORIENT**: Identify minimum viable differentiators
3. **DECIDE**: Feature set based on 80/20 principle
4. **ACT**: Build with continuous user feedback

## Development Principles

### Socratic Development Questions
Before each feature:
1. What problem does this solve?
2. Who benefits from this feature?
3. What's the evidence this is needed?
4. What's the simplest solution?
5. How do we measure success?

### OODA in Daily Development
- **Morning**: OBSERVE yesterday's metrics and feedback
- **Planning**: ORIENT based on new information
- **Coding**: DECIDE on implementation approach
- **Evening**: ACT and measure results

### Evidence-Based Decisions
- No optimization without profiling
- No feature without user request
- No assumption without measurement
- No guess without benchmark

## Technology Choices (Justified)

### Based on Evidence:
- **Vector DB**: ChromaDB (benchmarked fastest for our use case)
- **Frontend**: React (team expertise, ecosystem)
- **Backend**: FastAPI (async performance benefits measured)
- **Menubar**: PyObjC (easier maintenance vs Swift)
- **Inference**: MLX (designed for Apple Silicon)

### Re-evaluation Triggers
- Performance regression > 10%
- User complaints > 5% on specific feature
- Better alternative with 2x improvement
- Security vulnerability discovered

## Next Steps
1. Set up comprehensive benchmarking suite
2. Create performance baseline measurements
3. Implement continuous performance monitoring
4. Begin Phase 1 with evidence gathering