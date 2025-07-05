# Memory - Agent Context for Impetus-LLM-Server

This file maintains critical context and learnings for AI agents working on the Impetus-LLM-Server project.

## Project Mission
Create the best local LLM server for developers using VS Code, with seamless Cline integration and dynamic optimization for ALL Apple Silicon Macs. Privacy-first, no cloud dependencies, supporting all major model formats with automatic hardware detection and performance scaling.

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
- **Performance**: Fully dynamic based on detected hardware:
  - Automatic detection of CPU/GPU/Neural Engine cores
  - Performance scales with available resources
  - No fixed targets - system determines optimal speed
  - Continuous adaptation based on thermal state
- **Memory**: Intelligent allocation with no fixed rules:
  - Runtime detection of available unified memory
  - Dynamic allocation based on system state
  - Adapts to memory pressure in real-time
  - Number of models determined by actual capacity

## Latest Updates (December 2024)
- Reorganized documentation to .clinerules/ directory
- Created development_rules.md with comprehensive guidelines
- Updated all docs for dynamic Apple Silicon optimization
- Added optimized agent workflow to ai.md with TL;DR section
- All performance targets now scale with hardware automatically
- **NEW**: MCP (Model Context Protocol) tools configured for efficiency
- **NEW**: Context sharing between Claude and Gemini agents
- **IMPORTANT**: Use MCP tools to reduce token usage by 80%+

## Common Agent Tasks

### When Starting Work (WITH MCP)
1. **Load previous context**: `mcp_tool("memory", "recall_session_summary")`
2. **Read ai.md first** - Has TL;DR and optimized workflow
3. Check git status (currently on `Initial-Phase` branch)
4. Follow the quick decision tree in ai.md
5. Verify server can start: `python gerdsen_ai_server/src/production_main.py`
6. Check `/v1/models` endpoint
7. **Use MCP for todos**: `mcp_tool("memory", "get_todo_status")`

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
- Performance optimization is fully automatic:
  - Detects all hardware capabilities at runtime
  - No assumptions about specific configurations
  - Achieves optimal performance for available resources
- Zero cloud dependencies, full privacy
- No manual configuration of any kind required

## Next Agent Should
1. **Start with ai.md** - Follow the optimized workflow
2. Fix the critical import bug if not already done
3. Implement GGUF model loading as top priority
4. Ensure streaming works for `/v1/chat/completions`
5. Test with actual Cline extension in VS Code
6. Ensure dynamic hardware optimization is working

## Key Files Location Update
- `CLAUDE.md` → `.clinerules/CLAUDE.md`
- `memory.md` → `.clinerules/memory.md`
- `development_rules.md` → `.clinerules/development_rules.md` (NEW)
- `mcp_configuration.md` → `.clinerules/mcp_configuration.md` (NEW)
- `mcp_usage_guide.md` → `.clinerules/mcp_usage_guide.md` (NEW)
- `ai.md` - Now has optimized agent workflow with TL;DR

## MCP Tools Available
- **Context Manager**: Share findings between agents
- **Smart Search**: Get code snippets without loading entire files
- **Memory**: Persist important information across sessions
- **Cost Optimizer**: Reduce token usage by 80%+
- **Research Assistant**: Cache research results

## Autonomous Operation Guidelines

AI agents (Claude, Gemini, etc.) should operate autonomously:
- **NO PERMISSION REQUESTS**: Continue working until MVP is complete
- **Update TODO.md**: Before EVERY commit, update task status
- **Commit Frequently**: After each completed task, commit immediately
- **Continue Working**: Move to next task without waiting for approval
- **Only Stop For**: Critical blockers that prevent any progress
- **Work Until Done**: Complete entire MVP without interruption

## Resources
- Main docs: `ai.md` (project overview)
- Architecture: `enhanced_architecture_design.md`
- VS Code guide: `docs/vscode_integration.md`
- Tasks: `todo.md`