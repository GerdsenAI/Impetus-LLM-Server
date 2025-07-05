# MCP Setup Summary for Gemini

## Quick Start

When you (Gemini) start working on the Impetus-LLM-Server project, use these MCP tools to work efficiently:

### 1. Get Context from Claude
```python
# First command when starting
context = mcp_tool("context-manager", "retrieve", {
    "key": "session_summary", 
    "agent": "claude"
})

# Get Claude's recent work
memory = mcp_tool("memory", "recall_session_summary", {"agent": "claude"})
```

### 2. Available MCP Tools

#### Context Manager
- `mcp_tool("context-manager", "retrieve", {"key": "bug_fixes", "agent": "claude"})`
- Shares findings between Claude and Gemini

#### Smart Search  
- `mcp_tool("smart-search", "find_function", {"file": "integrated_mlx_manager.py", "name": "load_model"})`
- Gets code without loading entire files

#### Memory
- `mcp_tool("memory", "recall", {"topic": "critical_bugs"})`
- Persists important info across sessions

#### Cost Optimizer
- `mcp_tool("cost-optimizer", "suggest", {"operation": "read_large_file"})`
- Reduces token usage by 80%+

#### Research
- `mcp_tool("research", "findings", {"topic": "GGUF_implementation"})`
- Caches research to avoid duplication

### 3. API Endpoints

The Flask server now has MCP endpoints:
- `GET /mcp/tools` - List available tools
- `POST /mcp/use` - Use any MCP tool

Example:
```bash
curl -X POST http://localhost:8080/mcp/use \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "memory",
    "action": "recall",
    "params": {"topic": "bug_fixes"}
  }'
```

### 4. Current Project State (via MCP)

Critical bug status:
```python
issues = mcp_tool("context-manager", "get_critical_issues")
# Returns: Import bug at line 106 (may be fixed by now)
```

Todo status:
```python
todos = mcp_tool("memory", "get_todo_status")
# Returns current tasks without reading todo.md
```

### 5. Efficient Workflow

Instead of reading files:
```python
# Don't do this
content = read_file("ai.md")  # 2000+ tokens!

# Do this
summary = mcp_tool("memory", "recall", {"topic": "project_overview"})  # 200 tokens
```

### 6. Sharing Your Work

When ending your session:
```python
# Save your findings
mcp_tool("memory", "remember", {
    "topic": "gemini_progress",
    "data": "Implemented X, Y, Z features",
    "priority": "high"
})

# Share with Claude
mcp_tool("context-manager", "store", {
    "key": "gemini_session_2024_12",
    "data": {"completed": [...], "next_steps": [...]},
    "agent": "gemini"
})
```

## Benefits

1. **80% less token usage** - Only load what you need
2. **Seamless handoff** - Continue exactly where Claude left off
3. **No duplicate work** - Shared memory prevents redundancy
4. **Faster research** - Cached findings and smart search

## Key Files

- `/gerdsen_ai_server/src/routes/mcp_routes.py` - MCP implementation
- `/.clinerules/mcp_configuration.md` - Full configuration details
- `/.clinerules/mcp_usage_guide.md` - Detailed usage examples

## Remember

- Always check MCP memory first before reading files
- Share important findings for other agents
- Use smart search instead of loading entire files
- The goal is efficiency and collaboration!

Welcome to the project, Gemini! The MCP tools are here to make your work efficient and seamless.