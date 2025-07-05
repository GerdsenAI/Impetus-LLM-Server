# Memory - Agent Context for Impetus-LLM-Server

This file maintains critical context and learnings for AI agents working on the Impetus-LLM-Server project.

## Project Mission
Create the best local LLM server for developers using VS Code, with seamless Cline integration and dynamic optimization for ALL Apple Silicon Macs. Privacy-first, no cloud dependencies, supporting all major model formats with automatic hardware detection and performance scaling.

## Key Technical Context

### Critical Bug Status
- **RESOLVED**: IntegratedMLXManager import error fixed
- **File**: `gerdsen_ai_server/src/integrated_mlx_manager.py`
- **Line**: 106 - Now correctly uses `EnhancedAppleFrameworksIntegration()`
- **Status**: Server starts properly

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
- **NEW**: TODO.md reorganized with clear MVP section at top
- **NEW**: MVP = Load any model + use with Cline (nothing more needed)

## Latest Updates (January 2025)
- **NEW**: IMPETUS acronym defined - "Intelligent Model Platform Enabling Taskbar Unified Server"
- **COMPLETED**: All 6 model format loaders implemented (GGUF, SafeTensors, MLX, CoreML, PyTorch, ONNX)
- **COMPLETED**: Model loader factory pattern with automatic format detection
- **COMPLETED**: Integration of factory pattern into IntegratedMLXManager
- **COMPLETED**: Unified inference interface across all formats (UnifiedInferenceEngine)
- **COMPLETED**: Enhanced OpenAI API endpoints with model switching capabilities
- **COMPLETED**: Complete Electron app "Impetus" with native macOS taskbar integration
- **COMPLETED**: Python environment bundling system for self-contained distribution
- **NEW**: MVP now ~95% complete (All formats + factory + unified inference + complete Electron app + Python bundling implemented)
- **UPDATED**: Only Cline integration testing remains for MVP completion

## MVP Context
The project now has a clear MVP definition in TODO.md:
- **MVP Goal**: Load ANY local model format and use it with Cline via Electron app "Impetus"
- **Current Status**: ~95% complete (All 6 formats + factory + unified inference + complete Electron app + Python bundling implemented)
- **Completed**: 
  - All 6 model format loaders (GGUF, SafeTensors, MLX, CoreML, PyTorch, ONNX)
  - Model loader factory pattern with automatic format detection
  - IntegratedMLXManager integration with factory pattern
  - Unified inference interface (UnifiedInferenceEngine)
  - Enhanced OpenAI API endpoints with model switching
  - Complete Electron app "Impetus" with native macOS taskbar integration
  - Python environment bundling system for self-contained distribution
- **Remaining**: End-to-end testing with Cline extension
- **Priority**: Complete MVP section before ANY other features
- **Success**: When a developer can use Cline with a local model through the Impetus taskbar app
- **UI/Advanced Features**: All moved to post-MVP (not required for success)
- **Electron App Features Implemented**:
  - ✅ Taskbar/menu bar application for quick access
  - ✅ Server start/stop controls
  - ✅ Model selection from taskbar
  - ✅ Native macOS performance optimization
  - ✅ Minimal resource usage when idle
  - ✅ Bundled Python environment for easy installation

## Common Agent Tasks

### When Starting Work (WITH MCP)
1. **Load previous context**: `mcp_tool("memory", "recall_session_summary")`
2. **Read ai.md first** - Has TL;DR and optimized workflow
3. **Check TODO.md MVP section** - This is your primary focus
4. Check git status (currently on `Initial-Phase` branch)
5. Follow the quick decision tree in ai.md
6. Verify server can start: `python gerdsen_ai_server/src/production_main.py`
7. Check `/v1/models` endpoint
8. **Use MCP for todos**: `mcp_tool("memory", "get_todo_status")`
9. **Focus on MVP tasks only** - Ignore post-MVP features until complete

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
- Electron app "Impetus" provides native taskbar experience
- One-click server management from menu bar
- Performance optimization is fully automatic:
  - Detects all hardware capabilities at runtime
  - No assumptions about specific configurations
  - Achieves optimal performance for available resources
- Zero cloud dependencies, full privacy
- No manual configuration of any kind required

## Next Agent Should
1. **Start with ai.md** - Follow the optimized workflow
2. **Check TODO.md MVP section** - This defines completion criteria
3. Focus on completing remaining MVP tasks in order:
   - ✅ All model format loaders implemented (GGUF, SafeTensors, MLX, CoreML, PyTorch, ONNX)
   - ✅ Model loader factory pattern with automatic format detection
   - ✅ Unified inference interface across all formats
   - ✅ Enhanced OpenAI API endpoints with model switching
   - ✅ Create Electron app "Impetus" with taskbar integration (COMPLETED)
   - ✅ Python environment bundling system (COMPLETED)
   - ⏳ Test with actual Cline extension (REMAINING)
4. **Current Priority**: Test complete IMPETUS system with Cline integration
5. **MVP Complete = Success** - When any model loads and works with Cline via Impetus app
6. Only work on post-MVP features after MVP section is complete
7. Update TODO.md MVP section progress before each commit

## Electron App Technical Context (COMPLETED)
- **App Name**: IMPETUS (Intelligent Model Platform Enabling Taskbar Unified Server)
- **Type**: Menu bar/taskbar application (macOS) - IMPLEMENTED
- **Key Features** (ALL IMPLEMENTED):
  - ✅ Runs Flask server as background process
  - ✅ Taskbar icon with status indicator
  - ✅ Quick model selection menu
  - ✅ Server start/stop controls
  - ✅ Real-time status monitoring
  - ✅ Native macOS design (Apple HIG compliant)
  - ✅ Model switching capabilities
  - ⏳ Auto-start on boot option (not implemented yet)
- **Tech Stack**: Electron + Python (bundled) - IMPLEMENTED
- **Performance**: Native macOS APIs for optimal performance - IMPLEMENTED
- **Distribution**: Single .app bundle with all dependencies - BUNDLING SYSTEM IMPLEMENTED
- **Python Bundling**: Complete system for self-contained distribution - IMPLEMENTED
- **Build Commands**: npm run dist-with-python for complete package - READY

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
