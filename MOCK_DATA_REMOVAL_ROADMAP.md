# Mock Data Removal Roadmap

## Overview
This roadmap provides a systematic approach to remove all mock/dummy/placeholder implementations from the Impetus-LLM-Server and replace them with real functionality or honest documentation.

## Phase 1: Documentation Honesty (1 day)
**Goal**: Update all documentation to reflect actual capabilities

### Tasks:
1. [ ] Update README.md
   - Change "Universal model format support" to "GGUF model support"
   - Add "Planned Features" section for other formats
   - Remove misleading claims

2. [ ] Update ai.md
   - Change "MVP 100% COMPLETE" to "GGUF MVP Complete"
   - Add "Current Limitations" section
   - Update feature list to show implemented vs planned

3. [ ] Update memory.md
   - Add honest assessment of system state
   - Remove aspirational claims
   - Document what actually works

4. [ ] Update todo.md
   - Change MVP progress from "100%" to "~20% (GGUF only)"
   - Reorganize tasks to reflect reality

## Phase 2: Code Marking (2 days)
**Goal**: Clearly mark all placeholder code

### Tasks:
1. [ ] Add "NOT_IMPLEMENTED" markers
   ```python
   def generate(self, model_id: str, prompt: str, config=None):
       """NOT_IMPLEMENTED: Returns dummy response"""
       return "This is a placeholder response..."
   ```

2. [ ] Update class names
   - Rename `SafeTensorsInferenceEngine` to `SafeTensorsInferenceEnginePlaceholder`
   - Add `_PLACEHOLDER` suffix to all dummy classes

3. [ ] Add warning logs
   ```python
   self.logger.warning("Using placeholder implementation for SafeTensors")
   ```

4. [ ] Update error messages
   - Return clear "Not Implemented" errors instead of dummy responses

## Phase 3: Dummy Code Removal (1 week)
**Goal**: Remove unnecessary dummy code

### Tasks:
1. [ ] Remove dummy_model_loader.py
   - Remove imports from integrated_mlx_manager.py
   - Replace with "Not Implemented" errors

2. [ ] Remove MockMX class
   - Either install real MLX or remove MLX support claims
   - Update apple_frameworks_integration.py

3. [ ] Remove create_demo_models()
   - Stop creating fake model files
   - Return empty dict or remove method

4. [ ] Remove DummyInferenceEngine
   - Replace with NotImplementedError
   - Update base_inference.py

## Phase 4: Implement One Real Format (2 weeks)
**Goal**: Add real support for SafeTensors to validate multi-format claim

### Tasks:
1. [ ] Research SafeTensors loading
   - Study transformers library
   - Understand model structure

2. [ ] Implement SafeTensorsLoader
   - Real model loading
   - Metadata extraction
   - Memory management

3. [ ] Implement SafeTensorsInferenceEngine
   - Use transformers or similar
   - Real text generation
   - Proper tokenization

4. [ ] Test with real models
   - Download test SafeTensors models
   - Verify inference works
   - Benchmark performance

## Phase 5: Apple Silicon Reality (1 week)
**Goal**: Implement real Apple optimizations or remove claims

### Option A: Implement Real MLX
1. [ ] Install MLX: `pip install mlx`
2. [ ] Remove MockMX class
3. [ ] Implement real MLX model loading
4. [ ] Test MLX inference

### Option B: Remove MLX Claims
1. [ ] Remove MLX from supported formats
2. [ ] Remove MLX-related code
3. [ ] Update documentation
4. [ ] Focus on GGUF optimization

## Phase 6: Benchmark Reality (3 days)
**Goal**: Replace hardcoded benchmarks with real measurements

### Tasks:
1. [ ] Implement real CPU benchmark
   - Measure actual operations
   - Time real computations

2. [ ] Implement real GPU benchmark
   - Use Metal for actual work
   - Measure real throughput

3. [ ] Implement real memory benchmark
   - Test actual memory operations
   - Measure real bandwidth

4. [ ] Remove hardcoded values
   - Delete all fixed return values
   - Replace with measured results

## Phase 7: UI Implementation or Removal (1 week)
**Goal**: Build the Model Management UI or stop claiming it exists

### Option A: Build It
1. [ ] Create React components
2. [ ] Implement drag & drop
3. [ ] Add model search
4. [ ] Connect to backend

### Option B: Remove Claims
1. [ ] Remove UI mentions from docs
2. [ ] Mark as "Future Feature"
3. [ ] Remove UI-related endpoints
4. [ ] Focus on CLI/API usage

## Success Metrics

### Short Term (1 week)
- [ ] All documentation reflects reality
- [ ] All placeholder code clearly marked
- [ ] No more misleading claims

### Medium Term (1 month)
- [ ] Dummy code removed
- [ ] At least 2 formats with real implementation
- [ ] Real benchmarks replacing hardcoded values

### Long Term (3 months)
- [ ] All claimed features actually work
- [ ] OR claims reduced to match implementation
- [ ] System integrity restored

## Priority Order

1. **CRITICAL**: Fix documentation (prevents user frustration)
2. **HIGH**: Mark placeholder code (sets expectations)
3. **MEDIUM**: Implement SafeTensors (validates architecture)
4. **LOW**: Implement remaining formats (nice to have)

## Estimated Timeline

- Week 1: Documentation fixes + code marking
- Week 2-3: SafeTensors implementation
- Week 4: Benchmark reality + MLX decision
- Week 5+: Additional formats or scope reduction

## Conclusion

This roadmap provides a path to either:
1. Implement all claimed features (3+ months)
2. Reduce claims to match reality (1 week)

The recommended approach is to:
1. Immediately fix documentation (1 day)
2. Implement SafeTensors support (2 weeks)
3. Then reassess based on user needs

This would give you honest "dual-format support" (GGUF + SafeTensors) which is more defensible than current claims while still being achievable in a reasonable timeframe.