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
- **M1/M2 (Base)**: Optimize for efficiency, target 15-25 tokens/sec
- **M1/M2 Pro**: Balance performance/memory, target 25-40 tokens/sec
- **M1/M2 Max**: Leverage additional GPU cores, target 40-60 tokens/sec
- **M1/M2/M3/M4 Ultra**: Maximum performance, target 60-100+ tokens/sec
- **Future M-series**: Automatic capability detection and scaling

#### Dynamic Optimization Features
- Auto-detect chip variant and available resources
- Adjust batch sizes based on available GPU cores
- Scale memory allocation to unified memory size
- Optimize thread count for CPU cores
- Leverage Neural Engine when beneficial
- Thermal-aware performance throttling

#### Performance Targets (Dynamically Scaled)
```
Base Performance = Chip Performance Factor × Model Efficiency × Thermal Headroom

Where:
- Chip Performance Factor: M1=1.0, M1 Pro=1.8, M1 Max=2.5, M1 Ultra=4.0, etc.
- Model Efficiency: GGUF Q4=1.0, Q5=0.85, Q8=0.7, FP16=0.5
- Thermal Headroom: 100% when cool, scales down under load
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

### Hardware-Specific Testing
Test on diverse Apple Silicon hardware:
- [ ] M1 MacBook Air (base performance tier)
- [ ] M1/M2 Pro (mid-tier)
- [ ] M1/M2 Max (high-tier)
- [ ] M1/M2 Ultra (maximum performance)
- [ ] Memory configurations: 8GB, 16GB, 32GB, 64GB+

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

### Memory Management (Dynamic)
- Base allocation: 10% of unified memory
- Model allocation: Up to 60% of unified memory
- Buffer: 30% for system and other apps
- Auto-adjust based on system pressure
- Configurable limits with hardware-aware defaults

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

### Performance Metrics (Dynamically Scaled)
- **M1 Base**: 15+ tokens/sec on 7B models
- **M1 Pro**: 25+ tokens/sec on 7B models, 15+ on 13B
- **M1 Max**: 40+ tokens/sec on 7B models, 25+ on 13B
- **M1 Ultra**: 60+ tokens/sec on 7B models, 40+ on 13B, 20+ on 30B
- **Model Loading**: 5-10x faster than baseline (scaled by chip)
- **Memory Efficiency**: 30-50% reduction vs naive implementation

### User Metrics
- Setup time: < 10 minutes on any Mac
- Time to first inference: < 2 minutes
- Model switching time: < 5 seconds
- Error rate: < 1%
- Hardware utilization: > 80% of available resources

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