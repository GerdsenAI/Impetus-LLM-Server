# MCP Tools Usage Guide

Quick reference for using MCP tools efficiently in the Impetus-LLM-Server project.

## Quick Start for New Sessions

### Claude Starting a Session
```python
# 1. Load previous context
context = mcp_tool("memory", "recall_session_summary")

# 2. Check for critical updates
updates = mcp_tool("context-manager", "get_updates", {"since": "last_session"})

# 3. Load only what's needed
if "working_on_model_loading" in context:
    code = mcp_tool("smart-search", "get_function", {
        "file": "integrated_mlx_manager.py",
        "function": "load_gguf_model"
    })
```

### Gemini Continuing Work
```python
# 1. Get Claude's context
claude_work = mcp_tool("context-manager", "get_agent_context", {"agent": "claude"})

# 2. Load current state
state = mcp_tool("memory", "get_project_state")

# 3. Continue seamlessly
# No need to re-read all files!
```

## Common Workflows

### 1. Researching Implementation
Instead of:
```python
# BAD: Loading entire files
file_content = read_file("integrated_mlx_manager.py")  # 800+ lines!
```

Do this:
```python
# GOOD: Get only what you need
implementation = mcp_tool("smart-search", "find_implementation", {
    "feature": "GGUF loading",
    "include_imports": true,
    "max_lines": 50
})
```

### 2. Tracking Progress
Instead of:
```python
# BAD: Re-reading todo.md every time
todos = read_file("todo.md")
```

Do this:
```python
# GOOD: Get current status
status = mcp_tool("memory", "get_todo_status", {"filter": "in_progress"})
```

### 3. Sharing Findings
When you discover something important:
```python
# Save for other agents
mcp_tool("context-manager", "store_finding", {
    "topic": "bug_fix",
    "data": {
        "file": "integrated_mlx_manager.py",
        "line": 106,
        "fix": "Changed to EnhancedAppleFrameworksIntegration",
        "status": "completed"
    },
    "share_with": ["gemini"]
})
```

### 4. Cost-Efficient File Exploration
Instead of:
```python
# BAD: Reading multiple large files
for file in ["ai.md", "todo.md", "README.md"]:
    content = read_file(file)
```

Do this:
```python
# GOOD: Get summaries first
summaries = mcp_tool("cost-optimizer", "summarize_files", {
    "files": ["ai.md", "todo.md", "README.md"],
    "focus": "GGUF implementation status"
})
```

## MCP Tool Shortcuts

### Context Manager
- `store_context(key, data)` - Save important info
- `get_context(key)` - Retrieve saved info
- `share_context(agent, key)` - Share with other agent
- `list_contexts()` - See what's saved

### Smart Search
- `find_function(file, name)` - Get specific function
- `find_usage(symbol)` - Find where something is used
- `get_imports(file)` - Just the imports
- `search_pattern(pattern, path)` - Regex search

### Memory
- `remember(topic, data, priority)` - Save to memory
- `recall(topic)` - Get from memory
- `forget(topic)` - Remove from memory
- `export_session()` - Export for other agent

### Cost Optimizer
- `estimate_tokens(operation)` - Before doing something
- `suggest_alternative(operation)` - Get efficient approach
- `batch_operations(ops_list)` - Combine similar ops
- `get_usage_report()` - See token usage

### Research Assistant
- `research(topic)` - Research with caching
- `get_findings(topic)` - Get research results
- `generate_summary(topic)` - Create summary
- `cite_sources(topic)` - Get references

## Best Practices

### 1. Always Check Context First
```python
# Start of session
existing_work = mcp_tool("memory", "get_session_context")
if existing_work:
    # Continue from where you left off
    pass
else:
    # Start fresh
    pass
```

### 2. Use Smart Search for Large Files
```python
# Don't load 800+ line files
# Get specific sections
relevant_code = mcp_tool("smart-search", "get_section", {
    "file": "production_main.py",
    "section": "model_routes",
    "context_lines": 5
})
```

### 3. Save Important Discoveries
```python
# When you find something important
mcp_tool("memory", "remember", {
    "topic": "performance_optimization",
    "finding": "MLX format gives 2x speedup",
    "priority": "high",
    "share": true
})
```

### 4. Batch Similar Operations
```python
# Instead of multiple searches
results = mcp_tool("cost-optimizer", "batch_search", {
    "searches": [
        {"file": "*.py", "pattern": "load_model"},
        {"file": "*.py", "pattern": "GGUF"},
        {"file": "*.py", "pattern": "streaming"}
    ]
})
```

## Session Handoff Protocol

### Claude Ending Session
```python
# 1. Summarize work
summary = mcp_tool("memory", "create_session_summary", {
    "work_done": ["Fixed import bug", "Started GGUF implementation"],
    "next_steps": ["Test GGUF loading", "Implement streaming"],
    "blockers": []
})

# 2. Export for Gemini
mcp_tool("context-manager", "export_for_agent", {
    "agent": "gemini",
    "include": ["summary", "current_file_states", "todo_status"]
})
```

### Gemini Starting Session
```python
# 1. Import Claude's work
claude_session = mcp_tool("context-manager", "import_from_agent", {
    "agent": "claude",
    "latest": true
})

# 2. Get up to speed instantly
# No need to read all files again!
```

## Token Saving Examples

### Before MCP (High Token Usage)
```
Read ai.md: 2000 tokens
Read todo.md: 500 tokens
Read memory.md: 300 tokens
Read integrated_mlx_manager.py: 1500 tokens
Total: 4300 tokens just to start!
```

### With MCP (Optimized)
```
Load context: 200 tokens
Get relevant snippets: 300 tokens
Total: 500 tokens - 88% reduction!
```

## Remember

1. **MCP tools are here to help** - Use them to avoid re-reading files
2. **Share findings** - What you discover helps other agents
3. **Think efficiency** - Always ask "Can MCP do this smarter?"
4. **Document patterns** - Save common operations for reuse

This guide ensures efficient collaboration between all AI agents working on the project.