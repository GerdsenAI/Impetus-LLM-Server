# Memory - Agent Context for Impetus-LLM-Server

This file maintains critical context and learnings for AI agents working on the Impetus-LLM-Server project.

## Project Mission
Create the best local LLM server for developers using VS Code, with seamless Cline integration and Apple Silicon optimization. Privacy-first, no cloud dependencies, supporting all major model formats.

## Key Technical Context

### Critical Bug (Must Fix First)
- **File**: `gerdsen_ai_server/src/integrated_mlx_manager.py`
- **Line**: 106
- **Issue**: Wrong import - using `AppleFrameworksIntegration()` instead of `EnhancedAppleFrameworksIntegration()`
- **Impact**: Server won't start until fixed

### Primary Integration Target
- **VS Code Extension**: Cline (and Continue.dev, CodeGPT, etc.)
- **API**: OpenAI-compatible at `http://localhost:8080/v1/*`
- **Key Endpoints**: `/v1/chat/completions`, `/v1/models`
- **Authentication**: Optional, default key: `sk-dev-gerdsen-ai-local-development-key`

### Model Format Priority
1. **GGUF** - Most common for quantized models (Code Llama, Mistral)
2. **SafeTensors** - Hugging Face standard
3. **MLX** - Apple Silicon optimized
4. Others: CoreML, PyTorch, ONNX

### Architecture Decisions
- **Model Loading**: Dynamic, format-agnostic with factory pattern
- **UI**: React frontend for model management
- **Performance**: Dynamically scaled by hardware:
  - M1 Base: 15+ tokens/sec
  - M1 Pro: 25+ tokens/sec
  - M1 Max: 40+ tokens/sec
  - M1 Ultra: 60+ tokens/sec
  - Auto-detection and optimization for all variants
- **Memory**: Intelligent allocation based on unified memory:
  - 8GB systems: 1 model at a time
  - 16GB systems: 2-3 small models
  - 32GB+ systems: Multiple large models

## Common Agent Tasks

### When Starting Work
1. Check git status (currently on `Initial-Phase` branch)
2. Verify server can start: `python gerdsen_ai_server/src/production_main.py`
3. Check `/v1/models` endpoint
4. Review `todo.md` for current priorities

### When Implementing Features
1. Always maintain OpenAI API compatibility
2. Test with actual VS Code extensions (Cline)
3. Focus on developer experience over complexity
4. Implement streaming for all inference endpoints

### Testing Commands
```bash
# Start server
python gerdsen_ai_server/src/production_main.py

# Test API
curl http://localhost:8080/v1/models

# Run tests
python -m pytest tests/
python validate_functionality.py

# Format/lint
black src/ gerdsen_ai_server/src/
flake8 src/ gerdsen_ai_server/src/
```

## Known Gotchas
1. **Dummy Models**: Current implementation uses dummy models - need real implementation
2. **Port Conflicts**: Default 8080, but docs sometimes reference 5000
3. **Frontend**: Multiple UI implementations - React app is primary
4. **Dependencies**: Different requirement files for macOS vs production

## Success Metrics
- Developer can use Cline with local model in <10 minutes
- Support all major model formats without conversion
- Performance scales automatically with hardware:
  - Detects Apple Silicon variant (M1-M4, Base/Pro/Max/Ultra)
  - Optimizes for available GPU cores and memory
  - Achieves maximum possible tokens/sec for each chip
- Zero cloud dependencies, full privacy
- No manual performance tuning required

## Next Agent Should
1. Fix the critical import bug if not already done
2. Implement GGUF model loading as top priority
3. Ensure streaming works for `/v1/chat/completions`
4. Test with actual Cline extension in VS Code

## Resources
- Main docs: `ai.md` (project overview)
- Architecture: `enhanced_architecture_design.md`
- VS Code guide: `docs/vscode_integration.md`
- Tasks: `todo.md`