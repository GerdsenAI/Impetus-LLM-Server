# Development Rules for Impetus-LLM-Server

This document defines the core development principles, workflows, and standards for the Impetus-LLM-Server project.

## Project Mission Statement
Create the premier local LLM inference server for developers, with flawless VS Code integration, universal model format support, and dynamically optimized performance across ALL Apple Silicon machines - from M1 MacBook Air to M4 Ultra Mac Studio - all while maintaining complete privacy with zero cloud dependencies.

## Core Development Principles

### 1. Developer Experience First
- Every feature must enhance the developer workflow
- Setup to productivity in under 10 minutes
- Zero configuration for common use cases
- Intelligent defaults that "just work"

### 2. VS Code/Cline Integration is Sacred
- All decisions must prioritize VS Code AI extension compatibility
- OpenAI API compatibility is non-negotiable
- Streaming responses are required for all inference endpoints
- Test every change with actual Cline extension

### 3. Universal Model Support
- Support all major model formats without requiring conversion
- Priority order: GGUF → SafeTensors → MLX → CoreML → PyTorch → ONNX
- Automatic format detection and loading
- Seamless model switching without server restart

### 4. Dynamic Performance Optimization
Apple Silicon machines vary greatly in capability. Our server must adapt intelligently:

#### Hardware Detection & Optimization
The server dynamically detects hardware capabilities and optimizes accordingly:
- **Automatic Detection**: Identifies CPU/GPU/Neural Engine cores and unified memory
- **Dynamic Scaling**: Performance scales based on available resources
- **No Fixed Targets**: Token generation speed depends on model size, quantization, and available resources
- **Real-time Adaptation**: Continuously adjusts based on thermal state and system load
- **Future-proof**: Automatically adapts to new Apple Silicon without updates

#### Dynamic Optimization Features
- Auto-detect chip variant and available resources
- Adjust batch sizes based on available GPU cores
- Scale memory allocation to unified memory size
- Optimize thread count for CPU cores
- Leverage Neural Engine when beneficial
- Thermal-aware performance throttling

#### Performance Optimization Algorithm
```
Dynamic Performance = f(Available Resources, Model Requirements, System State)

Where:
- Available Resources: Detected at runtime (cores, memory, bandwidth)
- Model Requirements: Determined by model metadata
- System State: Current thermal, memory pressure, and competing processes
- All factors are discovered and calculated dynamically
```

### 5. Privacy and Security
- All processing happens locally - no exceptions
- No telemetry or usage tracking
- No cloud dependencies for core functionality
- Optional features clearly marked if they require internet

## Development Workflow

### Starting Work
1. Read `ai.md` for current project phase and context
2. Check `.clinerules/memory.md` for critical issues and gotchas
3. Review `todo.md` for prioritized tasks
4. Verify server starts: `python gerdsen_ai_server/src/production_main.py`
5. Fix any critical bugs before proceeding with features

### Implementation Process
1. **Design First**: Consider VS Code integration impact
2. **Test Driven**: Write tests for OpenAI API compatibility
3. **Incremental**: Small, focused commits that maintain functionality
4. **Document**: Update relevant docs with changes
5. **Validate**: Test with Cline before marking complete

### Code Standards

#### Python Code
- Use type hints for all functions
- Follow PEP 8 with Black formatting
- Docstrings for all public APIs
- Error messages must be developer-friendly
- Hardware-specific code must be abstracted

#### API Design
- Maintain OpenAI API compatibility
- Use consistent error response format
- Include helpful error details for debugging
- Version all breaking changes
- Expose performance metrics via API

#### Frontend Code
- React with TypeScript
- Accessibility-first design
- Real-time updates via WebSocket
- Mobile-responsive layouts
- Display hardware-specific optimizations

## Testing Requirements

### Unit Tests
- All model loaders must have tests
- API endpoint compatibility tests
- Format detection tests
- Memory management tests
- Hardware detection tests

### Integration Tests
- Full VS Code extension compatibility test
- Multi-model loading scenarios
- Performance benchmarks per hardware tier
- Memory leak detection
- Thermal throttling behavior

### Hardware-Agnostic Testing
Test dynamic adaptation on any available Apple Silicon:
- [ ] Verify hardware detection works correctly
- [ ] Confirm performance scales with available resources
- [ ] Test memory allocation adapts to system
- [ ] Validate thermal throttling behavior
- [ ] Ensure no assumptions about specific configurations

## Architecture Guidelines

### Hardware Abstraction Layer
```
Hardware Detector → Capability Profile → Optimization Engine → Model Loader
         ↓                    ↓                    ↓
   Chip Detection      Memory/Cores/GPU      Dynamic Settings
```

### Model Loading Architecture
```
Format Detection → Loader Selection → Hardware Optimization → Loading → Registration
                        ↓                      ↓
                  Format Converters    Performance Tuning
```

### API Request Flow
```
VS Code Extension → OpenAI API Endpoint → Model Manager → Inference Engine
                                              ↓                ↓
                                        Model Selector   Hardware Optimizer
```

### Memory Management (Fully Dynamic)
- **Runtime Detection**: Query available memory at startup and continuously
- **Intelligent Allocation**: Algorithm determines optimal allocation based on:
  - Total unified memory
  - Current system usage
  - Model requirements
  - Active applications
- **No Fixed Percentages**: Allocation adjusts in real-time
- **Pressure Response**: Automatically reduces usage under memory pressure
- **User Configurable**: Optional limits, but defaults are fully dynamic

## Feature Implementation Priority

### Phase 1: Core Functionality (Week 1)
1. Fix critical bugs
2. Hardware detection system
3. GGUF model loading with dynamic optimization
4. Basic inference API
5. Cline compatibility

### Phase 2: Universal Support (Week 2)
1. All model format loaders
2. Model management UI with hardware info
3. Dynamic model switching
4. Hugging Face integration
5. Performance profiling per hardware

### Phase 3: Performance (Week 3)
1. Hardware-specific optimizations
2. Dynamic memory management
3. Context optimization
4. Batching support
5. Thermal management

### Phase 4: Polish (Week 4)
1. Enhanced UI with performance metrics
2. VS Code extension
3. Documentation
4. Community features
5. Benchmark suite

## Success Metrics (Hardware-Aware)

### Performance Metrics (Fully Dynamic)
- **Token Generation**: Determined by actual hardware capabilities
- **Model Loading**: Optimized based on available I/O bandwidth
- **Memory Efficiency**: Measured against system-specific baseline
- **No Fixed Targets**: Performance emerges from resource optimization
- **Benchmarking**: System profiles itself on first run
- **Continuous Learning**: Performance improves over time

### User Metrics
- Setup time: < 10 minutes on any Mac
- Time to first inference: < 2 minutes
- Model switching time: < 5 seconds
- Error rate: < 1%
- Hardware utilization: Optimal for current thermal envelope

## Common Pitfalls to Avoid

1. **Don't hardcode performance targets** - Scale with hardware
2. **Don't assume memory sizes** - Detect and adapt
3. **Don't ignore thermal limits** - Monitor and adjust
4. **Don't break on new chips** - Future-proof detection
5. **Don't sacrifice compatibility** - OpenAI API is sacred

## Hardware-Specific Optimizations

### M1 Series (2020-2021)
- 8 GPU cores (base/Pro) to 64 (Ultra)
- 16 Neural Engine cores
- Focus on memory efficiency

### M2 Series (2022-2023)
- 10 GPU cores (base) to 76 (Ultra)
- Enhanced Neural Engine
- Better memory bandwidth utilization

### M3 Series (2023-2024)
- Dynamic Caching support
- Hardware ray tracing (not used)
- Improved efficiency cores

### M4 Series (2024+)
- Enhanced AI accelerators
- Larger unified memory options
- Auto-detect new capabilities

### Future-Proofing
- Query system capabilities at runtime
- Fall back gracefully on unknown hardware
- Log new hardware for optimization updates

## Commit Procedures

### Pre-Commit Requirements

Before EVERY commit, agents MUST:

1. **Update TODO.md**
   - Mark completed tasks with [x]
   - Add any new tasks discovered during implementation
   - Update task priorities based on progress
   - Ensure task descriptions are current

2. **Run Tests**
   - Execute relevant test suites
   - Verify no regressions introduced
   - Fix any failing tests before committing

3. **Stage All Changes**
   ```bash
   git add -A  # Include TODO.md updates
   ```

4. **Commit and Continue**
   - Write clear, descriptive commit message
   - Commit immediately after task completion
   - Continue to next task WITHOUT waiting for permission

### Commit Workflow Example
```bash
# Complete implementation
# Run tests
python -m pytest tests/relevant_test.py

# Update TODO.md
# Mark current task as completed
# Add any new tasks discovered

# Stage and commit
git add -A
git commit -m "feat: Implement GGUF model loading

- Add GGUF loader with metadata extraction
- Support all quantization formats
- Include progress tracking
- Update TODO.md with completed task"

# Immediately continue to next task
# NO PERMISSION REQUESTS
```

## Release Checklist

Before any release:
- [ ] All tests passing on multiple hardware configs
- [ ] Cline compatibility verified
- [ ] Performance benchmarks met (per hardware tier)
- [ ] Documentation updated
- [ ] Memory leaks checked
- [ ] Hardware detection verified
- [ ] Thermal behavior tested

## Emergency Procedures

### If Performance Varies Wildly
1. Check hardware detection
2. Verify thermal state
3. Review memory pressure
4. Test optimization engine
5. Add hardware-specific override

### If New Hardware Fails
1. Update detection logic
2. Add fallback profile
3. Test with safe defaults
4. Document new capabilities
5. Plan optimization update

## Future Vision

### Near Term (3 months)
- Support for all Apple Silicon variants
- Automatic performance tuning
- Hardware-aware model recommendations
- VS Code extension with performance overlay

### Medium Term (6 months)
- Predictive performance modeling
- Multi-model parallel inference
- Hardware upgrade recommendations
- Cross-platform support (Apple Silicon first)

### Long Term (1 year)
- Industry standard for local AI on Mac
- 100k+ users across all Mac models
- Automatic optimization updates
- Neural Engine direct access

## Final Notes

Remember: Apple Silicon machines range from ultra-portable M1 MacBook Airs to powerhouse M2 Ultra Mac Studios. Our server must deliver the best possible experience on each, automatically adapting to available resources without user configuration.

When implementing features:
- Test on lowest-spec hardware first
- Scale up intelligently
- Monitor resource usage
- Respect thermal limits
- Celebrate the diversity of Apple Silicon

This is a living document. Update it as new Apple Silicon chips are released and as we learn more about optimizing for each variant.