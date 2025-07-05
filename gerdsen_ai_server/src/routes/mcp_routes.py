"""
MCP (Model Context Protocol) Routes for AI Agent Efficiency
Enables context sharing, smart search, and memory persistence
"""

import os
import json
import time
from flask import Blueprint, request, jsonify
from pathlib import Path
from typing import Dict, Any, List, Optional
import hashlib
import re

mcp_bp = Blueprint('mcp', __name__, url_prefix='/mcp')

# MCP storage paths
MCP_BASE_PATH = Path(".clinerules")
MCP_CONTEXT_PATH = MCP_BASE_PATH / "mcp_context"
MCP_MEMORY_PATH = MCP_BASE_PATH / "agent_memory"
MCP_INDEX_PATH = MCP_BASE_PATH / "search_index"

# Ensure directories exist
for path in [MCP_CONTEXT_PATH, MCP_MEMORY_PATH, MCP_INDEX_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# In-memory caches for performance
context_cache = {}
memory_cache = {}
search_index = {}

@mcp_bp.route('/tools', methods=['GET'])
def list_mcp_tools():
    """List available MCP tools and their capabilities"""
    return jsonify({
        "tools": {
            "context-manager": {
                "description": "Manages context across agent sessions",
                "actions": ["store", "retrieve", "share", "list"]
            },
            "smart-search": {
                "description": "Intelligent code search with snippets",
                "actions": ["search_code", "find_function", "get_imports", "extract_snippets"]
            },
            "memory": {
                "description": "Persistent memory across sessions",
                "actions": ["remember", "recall", "summarize", "export"]
            },
            "cost-optimizer": {
                "description": "Optimize token usage and costs",
                "actions": ["estimate", "suggest", "batch", "report"]
            },
            "research": {
                "description": "Research assistant with caching",
                "actions": ["research", "findings", "summary", "sources"]
            }
        }
    })

@mcp_bp.route('/use', methods=['POST'])
def use_mcp_tool():
    """Main endpoint for using MCP tools"""
    data = request.json
    tool = data.get('tool')
    action = data.get('action')
    params = data.get('params', {})
    
    # Route to appropriate handler
    handlers = {
        'context-manager': handle_context_manager,
        'smart-search': handle_smart_search,
        'memory': handle_memory,
        'cost-optimizer': handle_cost_optimizer,
        'research': handle_research
    }
    
    handler = handlers.get(tool)
    if not handler:
        return jsonify({"error": f"Unknown tool: {tool}"}), 400
    
    try:
        result = handler(action, params)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def handle_context_manager(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle context manager operations"""
    if action == "store":
        key = params.get('key')
        data = params.get('data')
        agent = params.get('agent', 'claude')
        
        # Store in file and cache
        context_file = MCP_CONTEXT_PATH / f"{agent}_{key}.json"
        with open(context_file, 'w') as f:
            json.dump({
                'data': data,
                'timestamp': time.time(),
                'agent': agent
            }, f)
        
        context_cache[f"{agent}:{key}"] = data
        return {"status": "stored", "key": key}
    
    elif action == "retrieve":
        key = params.get('key')
        agent = params.get('agent', 'claude')
        
        # Check cache first
        cache_key = f"{agent}:{key}"
        if cache_key in context_cache:
            return {"data": context_cache[cache_key]}
        
        # Load from file
        context_file = MCP_CONTEXT_PATH / f"{agent}_{key}.json"
        if context_file.exists():
            with open(context_file) as f:
                context = json.load(f)
                context_cache[cache_key] = context['data']
                return {"data": context['data']}
        
        return {"data": None}
    
    elif action == "share":
        key = params.get('key')
        from_agent = params.get('from_agent', 'claude')
        to_agent = params.get('to_agent', 'gemini')
        
        # Copy context between agents
        source_file = MCP_CONTEXT_PATH / f"{from_agent}_{key}.json"
        if source_file.exists():
            dest_file = MCP_CONTEXT_PATH / f"{to_agent}_{key}.json"
            with open(source_file) as f:
                data = json.load(f)
            data['shared_from'] = from_agent
            data['shared_at'] = time.time()
            with open(dest_file, 'w') as f:
                json.dump(data, f)
            return {"status": "shared", "to": to_agent}
        
        return {"error": "Context not found"}
    
    elif action == "list":
        agent = params.get('agent', 'claude')
        contexts = []
        for file in MCP_CONTEXT_PATH.glob(f"{agent}_*.json"):
            key = file.stem.replace(f"{agent}_", "")
            contexts.append(key)
        return {"contexts": contexts}
    
    elif action == "get_critical_issues":
        # Special action to get current critical issues
        issues = []
        
        # Check for known critical bug
        if not check_import_bug_fixed():
            issues.append({
                "type": "bug",
                "severity": "critical",
                "file": "integrated_mlx_manager.py",
                "line": 106,
                "description": "Import bug - must be fixed first"
            })
        
        return {"issues": issues}

def handle_smart_search(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle smart search operations"""
    if action == "search_code":
        query = params.get('query')
        context = params.get('context', '')
        path = params.get('path', '.')
        
        # Simple implementation - in production, use proper indexing
        results = []
        for file_path in Path(path).rglob('*.py'):
            try:
                with open(file_path) as f:
                    content = f.read()
                    if query.lower() in content.lower():
                        # Extract relevant snippet
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if query.lower() in line.lower():
                                snippet = '\n'.join(lines[max(0, i-2):i+3])
                                results.append({
                                    'file': str(file_path),
                                    'line': i + 1,
                                    'snippet': snippet
                                })
                                if len(results) >= 5:  # Limit results
                                    break
            except:
                pass
        
        return {"results": results}
    
    elif action == "find_function":
        file_name = params.get('file')
        function_name = params.get('name')
        
        # Find specific function in file
        try:
            with open(file_name) as f:
                content = f.read()
            
            # Simple regex to find function
            pattern = rf"def {function_name}\s*\([^)]*\):"
            match = re.search(pattern, content, re.MULTILINE)
            
            if match:
                start = match.start()
                lines = content[:start].count('\n') + 1
                
                # Extract function body
                func_lines = content[start:].split('\n')
                func_body = []
                indent_level = None
                
                for line in func_lines:
                    if line.strip() and indent_level is None:
                        indent_level = len(line) - len(line.lstrip())
                    
                    if line.strip() and len(line) - len(line.lstrip()) <= indent_level and len(func_body) > 1:
                        break
                    
                    func_body.append(line)
                
                return {
                    "found": True,
                    "file": file_name,
                    "line": lines,
                    "code": '\n'.join(func_body[:50])  # Limit to 50 lines
                }
        except:
            pass
        
        return {"found": False}
    
    elif action == "get_imports":
        file_name = params.get('file')
        
        try:
            with open(file_name) as f:
                lines = f.readlines()
            
            imports = []
            for line in lines:
                if line.strip().startswith(('import ', 'from ')):
                    imports.append(line.strip())
                elif not line.strip().startswith('#') and line.strip() and not line.strip().startswith(('import ', 'from ')):
                    break  # Stop at first non-import line
            
            return {"imports": imports}
        except:
            return {"imports": []}
    
    elif action == "extract_snippets":
        file_name = params.get('file')
        topic = params.get('topic')
        
        # Extract relevant snippets about a topic
        # This is a simplified implementation
        return {
            "snippets": [
                f"# Snippet about {topic} from {file_name}",
                "# Actual implementation would extract relevant code"
            ]
        }

def handle_memory(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle memory operations"""
    agent = params.get('agent', 'claude')
    memory_file = MCP_MEMORY_PATH / f"{agent}_memory.json"
    
    if action == "remember":
        topic = params.get('topic')
        data = params.get('data')
        priority = params.get('priority', 'normal')
        
        # Load existing memory
        memory = {}
        if memory_file.exists():
            with open(memory_file) as f:
                memory = json.load(f)
        
        # Add new memory
        memory[topic] = {
            'data': data,
            'priority': priority,
            'timestamp': time.time()
        }
        
        # Save
        with open(memory_file, 'w') as f:
            json.dump(memory, f, indent=2)
        
        memory_cache[f"{agent}:{topic}"] = data
        return {"status": "remembered", "topic": topic}
    
    elif action == "recall":
        topic = params.get('topic')
        
        # Check cache
        cache_key = f"{agent}:{topic}"
        if cache_key in memory_cache:
            return {"data": memory_cache[cache_key]}
        
        # Load from file
        if memory_file.exists():
            with open(memory_file) as f:
                memory = json.load(f)
                if topic in memory:
                    data = memory[topic]['data']
                    memory_cache[cache_key] = data
                    return {"data": data}
        
        return {"data": None}
    
    elif action == "recall_session_summary":
        # Get summary of previous session
        if memory_file.exists():
            with open(memory_file) as f:
                memory = json.load(f)
            
            # Get high priority items and recent items
            summary = {
                'high_priority': [],
                'recent_work': [],
                'total_items': len(memory)
            }
            
            for topic, item in memory.items():
                if item.get('priority') == 'high':
                    summary['high_priority'].append({
                        'topic': topic,
                        'data': item['data']
                    })
                
                # Items from last 24 hours
                if time.time() - item.get('timestamp', 0) < 86400:
                    summary['recent_work'].append({
                        'topic': topic,
                        'data': item['data']
                    })
            
            return summary
        
        return {"high_priority": [], "recent_work": [], "total_items": 0}
    
    elif action == "get_todo_status":
        # Special action to get todo status without reading file
        # In production, this would track todos properly
        return {
            "in_progress": [
                "Implement GGUF model loading",
                "Fix import bug (if not done)"
            ],
            "completed": [
                "Documentation reorganization",
                "Dynamic optimization updates"
            ],
            "next": [
                "Test with Cline",
                "Implement streaming"
            ]
        }

def handle_cost_optimizer(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle cost optimization operations"""
    if action == "estimate":
        operation = params.get('operation')
        
        # Estimate tokens for operation
        estimates = {
            'read_file': 500,  # Average file
            'search_code': 100,  # Search results
            'mcp_recall': 50,   # MCP memory recall
        }
        
        estimated_tokens = estimates.get(operation, 200)
        return {
            "operation": operation,
            "estimated_tokens": estimated_tokens,
            "cost_usd": estimated_tokens * 0.00002  # Rough estimate
        }
    
    elif action == "suggest":
        operation = params.get('operation')
        
        suggestions = {
            'read_large_file': "Use smart-search to get specific functions instead",
            'read_multiple_files': "Use batch operations or summaries",
            'repeated_searches': "Cache results with memory tool"
        }
        
        return {"suggestion": suggestions.get(operation, "Consider using MCP tools")}
    
    elif action == "report":
        # In production, this would track actual usage
        return {
            "session_tokens": 1500,
            "saved_tokens": 3500,
            "efficiency": "70% reduction",
            "suggestions": [
                "Use memory tool more for repeated lookups",
                "Batch similar operations"
            ]
        }

def handle_research(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle research assistant operations"""
    if action == "research":
        topic = params.get('topic')
        
        # Check cache
        cache_file = MCP_INDEX_PATH / f"research_{hashlib.md5(topic.encode()).hexdigest()}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        
        # Simulate research (in production, would actually search)
        results = {
            "topic": topic,
            "findings": [
                f"Finding 1 about {topic}",
                f"Finding 2 about {topic}"
            ],
            "sources": ["ai.md", "documentation"],
            "timestamp": time.time()
        }
        
        # Cache results
        with open(cache_file, 'w') as f:
            json.dump(results, f)
        
        return results

def check_import_bug_fixed() -> bool:
    """Check if the critical import bug is fixed"""
    try:
        mlx_manager_file = Path("gerdsen_ai_server/src/integrated_mlx_manager.py")
        if mlx_manager_file.exists():
            with open(mlx_manager_file) as f:
                content = f.read()
                # Check if bug is fixed
                return "EnhancedAppleFrameworksIntegration" in content and "AppleFrameworksIntegration()" not in content
    except:
        pass
    return False