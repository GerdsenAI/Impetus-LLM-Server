# Agent Session Initialization Protocol

This document provides a standardized way for Act agents to properly initialize with project memory and context.

## Quick Start for Act Agents

### 1. Essential Context Loading (First 30 seconds)
Run these commands immediately when starting any session:

```bash
# Load critical project status
cat .clinerules/memory.md | head -50

# Check current project phase
grep -A 5 "MVP Status" .clinerules/memory.md

# Get latest session updates  
grep -A 10 "Development Session July" .clinerules/memory.md

# Check what's currently running
ps aux | grep python | grep -v grep
lsof -i :8080
```

### 2. Project State Quick Assessment
```bash
# Check if server is running
curl -s http://localhost:8080/v1/models | jq . || echo "Server not running"

# Check frontend status
curl -s http://localhost:3000 | head -10 || echo "Frontend not running"

# Get git status
git status --porcelain
git branch --show-current
```

### 3. Memory Context Summary
Based on `.clinerules/memory.md`, here's what you need to know:

#### ✅ MVP STATUS: 100% COMPLETE
- Real GGUF inference working (138.61 tokens/sec on M3 Ultra)
- All 6 model format loaders implemented
- OpenAI-compatible API fully functional
- VS Code/Cline integration tested and validated
- Electron app "Impetus" built and installed

#### 🎯 CURRENT FOCUS: Post-MVP Enhancements
- Performance Dashboard implementation
- Model Management UI improvements  
- Hugging Face integration
- Distribution improvements

#### 🚨 CRITICAL KNOWLEDGE
1. **Server Paths**: Use `gerdsen_ai_server/src/production_main.py` for main server
2. **Real Models**: TinyLlama working at `~/Models/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf`
3. **Testing**: Comprehensive Puppeteer test suite at `tests/puppeteer/`
4. **Frontend**: React app in `gerdsen-ai-frontend/` (currently running)

## 4. MCP Tools Available (80% Token Reduction)

The project has production-ready MCP tools for efficient operation:

### Context Loading
```python
# Instead of reading large files, use:
context = mcp_tool("memory", "recall_session_summary")
project_state = mcp_tool("context-manager", "get_project_state")
```

### Smart Code Access
```python
# Instead of reading entire files:
code_snippet = mcp_tool("smart-search", "get_function", {
    "file": "integrated_mlx_manager.py", 
    "function": "load_gguf_model"
})
```

### Research Cache
```python
# Cached research (80% faster):
findings = mcp_tool("research", "get_findings", {"topic": "React performance dashboard"})
```

## 5. Common Agent Tasks & Solutions

### Starting Development Work
```bash
# 1. Check if virtual environment needed
python3 -c "import flask" 2>/dev/null || echo "Need venv setup"

# 2. Activate venv if exists
[ -d ".venv" ] && source .venv/bin/activate

# 3. Start server if needed
python gerdsen_ai_server/src/production_main.py &

# 4. Verify APIs
curl http://localhost:8080/v1/models
```

### Frontend Development
```bash
# Frontend is already running on :3000
# Backend should run on :8080
# Check current tab: gerdsen-ai-frontend/src/App.jsx open
```

### Testing & Validation
```bash
# Run comprehensive tests
cd tests/puppeteer && node run-tests.js

# Quick API test
python test_real_gguf_inference.py

# VS Code integration test
python test_vscode_integration.py
```

## 6. Session Memory Protocol

### At Session Start
1. ✅ Load `.clinerules/memory.md` summary (lines 1-100)
2. ✅ Check MCP workspace: `a51a230fe3ecce44`
3. ✅ Verify critical systems (server, frontend, models)
4. ✅ Review latest development session notes

### During Work
1. 🔄 Use MCP tools for file access (80% token reduction)
2. 🔄 Save important findings to shared context
3. 🔄 Update session progress in memory.md if needed

### At Session End
1. 📝 Document any important discoveries
2. 📝 Update `.clinerules/memory.md` if critical changes made
3. 📝 Export context for next agent session

## 7. Emergency Recovery

### If Server Won't Start
```bash
# Check dependencies
pip list | grep -E "(flask|llama-cpp-python|pyppeteer)"

# Use enhanced server
python gerdsen_ai_server/src/production_main_enhanced.py

# Check for port conflicts
lsof -i :8080
```

### If Frontend Issues
```bash
cd gerdsen-ai-frontend
pnpm install
pnpm dev
```

### If Tests Fail
```bash
# Quick health check
python validate_functionality.py

# Full test suite
cd tests/puppeteer && npm test
```

## 8. Quick Reference

### Project Structure
- **Backend**: `gerdsen_ai_server/src/` (Flask + Python)
- **Frontend**: `gerdsen-ai-frontend/src/` (React + Vite)
- **Electron**: `impetus-electron/` (macOS app)
- **Tests**: `tests/` (Python) + `tests/puppeteer/` (Node.js)

### Key APIs
- **OpenAI Compatible**: `http://localhost:8080/v1/*`
- **Model Management**: `http://localhost:8080/api/models`
- **Frontend UI**: `http://localhost:3000`

### Documentation
- **Architecture**: `docs/enhanced_architecture_design.md`
- **VS Code Guide**: `docs/vscode_integration.md`
- **Memory Context**: `.clinerules/memory.md`

---

**Remember**: This project has 100% complete MVP with real inference working. Focus on enhancements, not rebuilding core functionality. Use MCP tools for 80% token reduction.
