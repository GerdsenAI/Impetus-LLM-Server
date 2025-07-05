# MCP (Model Context Protocol) Configuration

This document outlines the MCP tools configuration for efficient AI agent collaboration, context management, and cost optimization.

## Overview

MCP tools enable AI agents (Claude, Gemini, etc.) to:
- Efficiently search and access information without loading entire files
- Maintain persistent memory across sessions
- Share context between different AI agents
- Reduce token usage and costs
- Improve research capabilities

## Core MCP Tools Configuration

### 1. **Context Manager** (`mcp-context-manager`)
Manages context across agent sessions and reduces redundant information loading.

```json
{
  "tool": "mcp-context-manager",
  "config": {
    "storage_path": ".clinerules/mcp_context/",
    "max_context_size": 8192,
    "compression": true,
    "shared_between_agents": true
  },
  "capabilities": [
    "store_context",
    "retrieve_context",
    "summarize_context",
    "share_context"
  ]
}
```

**Usage**:
- Store important findings: `store_context(key="bug_fixes", data="...")`
- Retrieve for new session: `retrieve_context(key="bug_fixes")`
- Share with Gemini: `share_context(agent="gemini", key="bug_fixes")`

### 2. **Smart Search** (`mcp-smart-search`)
Intelligent code search that understands context and returns only relevant snippets.

```json
{
  "tool": "mcp-smart-search",
  "config": {
    "index_path": ".clinerules/search_index/",
    "snippet_size": 50,
    "context_aware": true,
    "semantic_search": true
  },
  "capabilities": [
    "search_code",
    "search_docs",
    "find_references",
    "extract_snippets"
  ]
}
```

**Usage**:
- Find specific implementations: `search_code(query="GGUF loader", context="model loading")`
- Get only relevant lines: `extract_snippets(file="integrated_mlx_manager.py", topic="initialization")`

### 3. **Memory Persistence** (`mcp-memory`)
Maintains agent memory across sessions with intelligent summarization.

```json
{
  "tool": "mcp-memory",
  "config": {
    "memory_path": ".clinerules/agent_memory/",
    "auto_summarize": true,
    "max_memory_items": 1000,
    "priority_based": true
  },
  "capabilities": [
    "remember",
    "recall",
    "summarize_session",
    "export_memory"
  ]
}
```

**Usage**:
- Save important info: `remember(topic="critical_bugs", data="import bug at line 106", priority="high")`
- Recall in new session: `recall(topic="critical_bugs")`
- Export for Gemini: `export_memory(format="markdown", agent="gemini")`

### 4. **Cost Optimizer** (`mcp-cost-optimizer`)
Monitors token usage and suggests optimizations.

```json
{
  "tool": "mcp-cost-optimizer",
  "config": {
    "track_tokens": true,
    "suggest_alternatives": true,
    "batch_operations": true
  },
  "capabilities": [
    "track_usage",
    "suggest_summary",
    "batch_similar_operations",
    "estimate_cost"
  ]
}
```

**Usage**:
- Check token usage: `track_usage(session_id="current")`
- Get cost-saving suggestions: `suggest_summary(files=["ai.md", "todo.md"])`

### 5. **Research Assistant** (`mcp-research`)
Helps with efficient research and documentation access.

```json
{
  "tool": "mcp-research",
  "config": {
    "cache_results": true,
    "auto_summarize": true,
    "track_sources": true
  },
  "capabilities": [
    "research_topic",
    "find_documentation",
    "track_findings",
    "generate_report"
  ]
}
```

**Usage**:
- Research implementation: `research_topic("GGUF format implementation")`
- Generate summary: `generate_report(topic="model_formats", include_code=true)`

## Integration with Impetus-LLM-Server

### MCP Server Endpoints
Add these endpoints to the Flask server:

```python
# In production_main.py or new mcp_routes.py

@app.route('/mcp/tools', methods=['GET'])
def list_mcp_tools():
    """List available MCP tools"""
    return jsonify({
        "tools": [
            "mcp-context-manager",
            "mcp-smart-search",
            "mcp-memory",
            "mcp-cost-optimizer",
            "mcp-research"
        ]
    })

@app.route('/mcp/use', methods=['POST'])
def use_mcp_tool():
    """Use an MCP tool"""
    data = request.json
    tool_name = data.get('tool')
    action = data.get('action')
    params = data.get('params', {})
    
    # Route to appropriate tool handler
    result = mcp_tool_router(tool_name, action, params)
    return jsonify(result)

@app.route('/mcp/context/share', methods=['POST'])
def share_context():
    """Share context between agents"""
    data = request.json
    return jsonify({"status": "shared", "agent": data.get('target_agent')})
```

## Usage Guidelines for All AI Agents

### Starting a Session (Claude, Gemini, or any agent)
1. **Load previous context**:
   ```
   context = use_mcp_tool("mcp-memory", "recall", {"topic": "session_summary"})
   ```

2. **Check current tasks**:
   ```
   tasks = use_mcp_tool("mcp-memory", "recall", {"topic": "current_tasks"})
   ```

3. **Get critical issues**:
   ```
   issues = use_mcp_tool("mcp-context-manager", "get_critical_issues")
   ```

### During Development (All agents)
1. **Before reading large files**:
   ```
   snippets = use_mcp_tool("mcp-smart-search", "extract_snippets", {
       "file": "large_file.py",
       "topic": "specific_function"
   })
   ```

2. **Search for implementations**:
   ```
   results = use_mcp_tool("mcp-smart-search", "search_code", {
       "query": "GGUF loader",
       "context": "model loading"
   })
   ```

3. **Track important findings**:
   ```
   use_mcp_tool("mcp-memory", "remember", {
       "topic": "implementation_notes",
       "data": "Found critical function at...",
       "priority": "high"
   })
   ```

### Before Committing (All agents)
1. **Update task status in memory**:
   ```
   use_mcp_tool("mcp-memory", "remember", {
       "topic": "completed_tasks",
       "data": "Completed GGUF loader implementation"
   })
   ```

2. **Share context for next agent**:
   ```
   use_mcp_tool("mcp-context-manager", "store_context", {
       "key": "current_progress",
       "data": "Implemented X, next task is Y",
       "shared": true
   })
   ```

### Ending a Session (Optional, for handoff)
1. **Summarize progress**:
   ```
   use_mcp_tool("mcp-memory", "summarize_session", {
       "export_for": "all_agents"
   })
   ```

2. **Update shared context**:
   ```
   use_mcp_tool("mcp-context-manager", "share_context", {
       "agent": "next_agent",
       "key": "session_summary"
   })
   ```

### Agent-Agnostic Examples

**For any agent continuing work**:
```python
# Load shared context from previous agent
context = use_mcp_tool("mcp-context-manager", "retrieve_context", {
    "from_agent": "previous"  # Works for any previous agent
})

# Get memory from any previous session
memory = use_mcp_tool("mcp-memory", "recall", {
    "agent": "any"  # Retrieves from any agent's memory
})
```

**Universal search pattern**:
```python
# Works identically for Claude, Gemini, or any other agent
code = use_mcp_tool("mcp-smart-search", "search_code", {
    "query": "model loading",
    "include_context": true
})
```

## Benefits

### 1. **Reduced Context Usage**
- Load only relevant code snippets instead of entire files
- Automatic summarization of previous sessions
- Shared context prevents re-reading

### 2. **Cost Optimization**
- Track token usage per session
- Get suggestions for more efficient operations
- Batch similar requests

### 3. **Better Collaboration**
- Seamless handoff between Claude and Gemini
- Shared memory and findings
- Consistent understanding of project state

### 4. **Improved Research**
- Cache research results
- Track sources and findings
- Generate comprehensive reports

## Implementation Priority

1. **Phase 1**: Context Manager & Memory (Critical for continuity)
2. **Phase 2**: Smart Search (Reduce token usage)
3. **Phase 3**: Cost Optimizer (Track and optimize)
4. **Phase 4**: Research Assistant (Enhanced capabilities)

## Directory Structure

```
.clinerules/
├── mcp_configuration.md (this file)
├── mcp_context/
│   ├── shared/
│   ├── claude/
│   └── gemini/
├── agent_memory/
│   ├── claude/
│   └── gemini/
└── search_index/
    └── code_index.json
```

## Next Steps

1. Implement MCP server endpoints in Flask app
2. Create MCP tool handlers
3. Set up persistent storage directories
4. Test context sharing between agents
5. Document specific tool usage patterns

This configuration ensures both Claude and Gemini can work efficiently on the Impetus-LLM-Server project with minimal context loading and maximum collaboration.