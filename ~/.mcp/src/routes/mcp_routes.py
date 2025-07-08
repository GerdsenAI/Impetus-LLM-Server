"""
MCP (Model Context Protocol) Routes for AI Agent Efficiency
Enables context sharing, smart search, and memory persistence with workspace isolation
"""

import os
import json
import time
import asyncio
import logging
from flask import Blueprint, request, jsonify
from pathlib import Path
from typing import Dict, Any, List, Optional
import hashlib
import re

# Import the new managers
from ..mcp.workspace_manager import get_workspace_manager
from ..debug.puppeteer_tools import get_puppeteer_manager, run_async_puppeteer_operation
from ..research.brave_search import get_brave_search_manager

logger = logging.getLogger(__name__)

mcp_bp = Blueprint('mcp', __name__, url_prefix='/mcp')

# Get workspace manager instance
workspace_manager = get_workspace_manager()

# Legacy support - ensure old directories exist for migration
MCP_BASE_PATH = Path(".clinerules")
MCP_CONTEXT_PATH = MCP_BASE_PATH / "mcp_context"
MCP_MEMORY_PATH = MCP_BASE_PATH / "agent_memory"
MCP_INDEX_PATH = MCP_BASE_PATH / "search_index"

for path in [MCP_CONTEXT_PATH, MCP_MEMORY_PATH, MCP_INDEX_PATH]:
    path.mkdir(parents=True, exist_ok=True)

@mcp_bp.route('/tools', methods=['GET'])
def list_mcp_tools():
    """List available MCP tools and their capabilities"""
    puppeteer_manager = get_puppeteer_manager()
    brave_search_manager = get_brave_search_manager()
    
    return jsonify({
        "tools": {
            "context-manager": {
                "description": "Manages context across agent sessions with workspace isolation",
                "actions": ["store", "retrieve", "share", "list", "migrate"]
            },
            "smart-search": {
                "description": "Intelligent code search with snippets",
                "actions": ["search_code", "find_function", "get_imports", "extract_snippets"]
            },
            "memory": {
                "description": "Persistent memory across sessions with workspace isolation",
                "actions": ["remember", "recall", "summarize", "export", "migrate"]
            },
            "cost-optimizer": {
                "description": "Optimize token usage and costs",
                "actions": ["estimate", "suggest", "batch", "report"]
            },
            "research": {
                "description": "Research assistant with Brave Search API and caching",
                "actions": ["research", "search_web", "search_news", "cache_stats", "clear_cache"]
            },
            "puppeteer": {
                "description": "Web testing and debugging with Puppeteer",
                "actions": ["navigate", "screenshot", "click", "type", "test_ui", "status"]
            },
            "workspace": {
                "description": "Workspace management and information",
                "actions": ["info", "list", "migrate_legacy"]
            }
        },
        "workspace_info": workspace_manager.get_workspace_info(),
        "status": {
            "puppeteer_available": puppeteer_manager.get_status()["puppeteer_available"],
            "brave_search_configured": brave_search_manager.get_cache_stats()["api_key_configured"]
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
        'research': handle_research,
        'puppeteer': handle_puppeteer,
        'workspace': handle_workspace
    }
    
    handler = handlers.get(tool)
    if not handler:
        return jsonify({"error": f"Unknown tool: {tool}"}), 400
    
    try:
        result = handler(action, params)
        return jsonify(result)
    except Exception as e:
        logger.error(f"MCP tool error: {tool}.{action} - {e}")
        return jsonify({"error": str(e)}), 500

# Removed duplicate handler - using updated version below

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

# Removed legacy handler - using workspace-aware version below

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
    """Handle research assistant operations with Brave Search API"""
    # Get API key from environment
    api_key = os.getenv('BRAVE_SEARCH_API_KEY')
    brave_search = get_brave_search_manager(api_key)
    
    if action == "research":
        topic = params.get('topic')
        include_news = params.get('include_news', True)
        
        result = brave_search.research_topic(topic, include_news)
        return {
            "success": result.get('success', False),
            "topic": topic,
            "data": result,
            "timestamp": time.time()
        }
    
    elif action == "search_web":
        query = params.get('query')
        count = params.get('count', 10)
        
        result = brave_search.search_web(query, count)
        return result
    
    elif action == "search_news":
        query = params.get('query')
        count = params.get('count', 10)
        
        result = brave_search.search_news(query, count)
        return result
    
    elif action == "cache_stats":
        return brave_search.get_cache_stats()
    
    elif action == "clear_cache":
        days = params.get('older_than_days', 30)
        return brave_search.clear_cache(days)
    
    return {"error": f"Unknown research action: {action}"}

def handle_puppeteer(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Puppeteer web testing operations"""
    puppeteer_manager = get_puppeteer_manager()
    
    if action == "status":
        return puppeteer_manager.get_status()
    
    elif action == "navigate":
        url = params.get('url')
        page_id = params.get('page_id')
        
        # Run async operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                puppeteer_manager.navigate_to(url, page_id)
            )
            return result
        finally:
            loop.close()
    
    elif action == "screenshot":
        page_id = params.get('page_id')
        filename = params.get('filename')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                puppeteer_manager.take_screenshot(page_id, filename)
            )
            return result
        finally:
            loop.close()
    
    elif action == "click":
        page_id = params.get('page_id')
        selector = params.get('selector')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                puppeteer_manager.click_element(page_id, selector)
            )
            return result
        finally:
            loop.close()
    
    elif action == "type":
        page_id = params.get('page_id')
        selector = params.get('selector')
        text = params.get('text')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                puppeteer_manager.type_text(page_id, selector, text)
            )
            return result
        finally:
            loop.close()
    
    elif action == "test_ui":
        base_url = params.get('base_url', 'http://localhost:8080')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                puppeteer_manager.test_impetus_ui(base_url)
            )
            return result
        finally:
            loop.close()
    
    return {"error": f"Unknown puppeteer action: {action}"}

def handle_workspace(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle workspace management operations"""
    if action == "info":
        return workspace_manager.get_workspace_info()
    
    elif action == "list":
        return workspace_manager.list_workspaces()
    
    elif action == "migrate_legacy":
        legacy_path = params.get('legacy_path', '.clinerules')
        success = workspace_manager.migrate_legacy_data(legacy_path)
        return {
            "success": success,
            "message": "Legacy data migrated to workspace database" if success else "Migration failed"
        }
    
    return {"error": f"Unknown workspace action: {action}"}

# Updated context and memory handlers to use workspace manager
def handle_context_manager(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle context manager operations with workspace isolation"""
    if action == "store":
        key = params.get('key')
        data = params.get('data')
        agent = params.get('agent', 'claude')
        shared = params.get('shared', False)
        
        success = workspace_manager.store_context(key, data, agent, shared)
        return {"success": success, "key": key, "agent": agent}
    
    elif action == "retrieve":
        key = params.get('key')
        agent = params.get('agent', 'claude')
        
        data = workspace_manager.retrieve_context(key, agent)
        return {"data": data, "found": data is not None}
    
    elif action == "share":
        # For cross-agent sharing within the same workspace
        key = params.get('key')
        from_agent = params.get('from_agent', 'claude')
        to_agent = params.get('to_agent', 'gemini')
        
        # Retrieve from source agent and store for target agent
        data = workspace_manager.retrieve_context(key, from_agent)
        if data:
            success = workspace_manager.store_context(key, data, to_agent, True)
            return {"success": success, "shared_to": to_agent}
        
        return {"success": False, "error": "Context not found"}
    
    elif action == "list":
        # List contexts for current workspace
        workspaces = workspace_manager.list_workspaces()
        current_workspace = workspace_manager.get_workspace_info()
        return {
            "current_workspace": current_workspace,
            "all_workspaces": workspaces
        }
    
    elif action == "migrate":
        # Migrate legacy context data
        success = workspace_manager.migrate_legacy_data()
        return {"success": success}
    
    return {"error": f"Unknown context action: {action}"}

def handle_memory(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle memory operations with workspace isolation"""
    agent = params.get('agent', 'claude')
    
    if action == "remember":
        topic = params.get('topic')
        data = params.get('data')
        priority = params.get('priority', 'normal')
        
        success = workspace_manager.remember(topic, data, agent, priority)
        return {"success": success, "topic": topic, "agent": agent}
    
    elif action == "recall":
        topic = params.get('topic')
        
        data = workspace_manager.recall(topic, agent)
        return {"data": data, "found": data is not None}
    
    elif action == "recall_session_summary":
        # Get summary from workspace database
        try:
            with workspace_manager.get_workspace_connection() as conn:
                cursor = conn.execute(
                    """SELECT topic, data, priority, timestamp FROM mcp_memory 
                       WHERE agent = ? ORDER BY timestamp DESC LIMIT 20""",
                    (agent,)
                )
                recent_items = cursor.fetchall()
                
                high_priority = []
                recent_work = []
                
                for topic, data, priority, timestamp in recent_items:
                    item = {"topic": topic, "data": data}
                    
                    if priority == 'high':
                        high_priority.append(item)
                    
                    # Items from last 24 hours
                    if time.time() - timestamp < 86400:
                        recent_work.append(item)
                
                return {
                    "high_priority": high_priority[:5],
                    "recent_work": recent_work[:10],
                    "total_items": len(recent_items)
                }
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
            return {"high_priority": [], "recent_work": [], "total_items": 0}
    
    elif action == "get_todo_status":
        # In production, this would integrate with actual TODO tracking
        return {
            "workspace_id": workspace_manager.workspace_id,
            "status": "Use TODO.md for current status",
            "suggestion": "Consider using memory to track specific progress"
        }
    
    elif action == "migrate":
        # Migrate legacy memory data
        success = workspace_manager.migrate_legacy_data()
        return {"success": success}
    
    return {"error": f"Unknown memory action: {action}"}

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
