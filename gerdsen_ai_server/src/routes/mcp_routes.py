#!/usr/bin/env python3
"""
MCP Routes for Flask Integration

Provides REST API endpoints for MCP (Model Context Protocol) tools
including workspace management, Puppeteer automation, and research capabilities.

Routes:
- GET /mcp/tools - List available MCP tools
- POST /mcp/use - Use an MCP tool  
- GET /mcp/workspace/info - Get workspace information
- POST /mcp/workspace/remember - Store memory
- GET /mcp/workspace/recall - Retrieve memory
- POST /mcp/puppeteer/screenshot - Take screenshot
- POST /mcp/puppeteer/navigate - Navigate to URL
- POST /mcp/research/search - Search with caching
- GET /mcp/research/history - Get research history
"""

import asyncio
import json
import logging
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, Optional

# Import MCP components
from ..mcp.workspace_manager import get_workspace_manager
from ..debug.puppeteer_tools import get_puppeteer_manager, PYPPETEER_AVAILABLE
from ..research.brave_search import get_search_manager, REQUESTS_AVAILABLE

# Setup logging
logger = logging.getLogger(__name__)

# Create Blueprint
mcp_bp = Blueprint('mcp', __name__, url_prefix='/mcp')


def handle_async(coro):
    """Helper to run async functions in sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


@mcp_bp.route('/tools', methods=['GET'])
def list_mcp_tools():
    """List all available MCP tools and their status."""
    tools = {
        'workspace_manager': {
            'available': True,
            'description': 'Workspace isolation and memory management',
            'capabilities': ['remember', 'recall', 'context_storage', 'project_detection']
        },
        'puppeteer_tools': {
            'available': PYPPETEER_AVAILABLE,
            'description': 'Web automation and screenshot capabilities',
            'capabilities': ['screenshot', 'navigation', 'form_filling', 'testing'] if PYPPETEER_AVAILABLE else [],
            'requirements': 'pip install pyppeteer' if not PYPPETEER_AVAILABLE else None
        },
        'research_tools': {
            'available': REQUESTS_AVAILABLE,
            'description': 'Web search with intelligent caching',
            'capabilities': ['brave_search', 'fallback_search', 'cache_management'] if REQUESTS_AVAILABLE else [],
            'requirements': 'pip install requests beautifulsoup4' if not REQUESTS_AVAILABLE else None
        }
    }
    
    return jsonify({
        'success': True,
        'tools': tools,
        'workspace_id': get_workspace_manager().workspace_id
    })


@mcp_bp.route('/use', methods=['POST'])
def use_mcp_tool():
    """Use an MCP tool with specified parameters."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        tool_name = data.get('tool')
        action = data.get('action')
        params = data.get('params', {})
        
        if not tool_name or not action:
            return jsonify({'success': False, 'error': 'tool and action are required'}), 400
        
        # Route to appropriate tool handler
        if tool_name == 'workspace_manager':
            return handle_workspace_action(action, params)
        elif tool_name == 'puppeteer_tools':
            return handle_puppeteer_action(action, params)
        elif tool_name == 'research_tools':
            return handle_research_action(action, params)
        else:
            return jsonify({'success': False, 'error': f'Unknown tool: {tool_name}'}), 400
            
    except Exception as e:
        logger.error(f"MCP tool use error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def handle_workspace_action(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle workspace manager actions."""
    workspace = get_workspace_manager()
    
    try:
        if action == 'remember':
            topic = params.get('topic')
            content = params.get('content')
            agent = params.get('agent', 'claude')
            priority = params.get('priority', 'normal')
            tags = params.get('tags', [])
            
            if not topic or not content:
                return jsonify({'success': False, 'error': 'topic and content are required'}), 400
            
            workspace.remember(topic, content, agent, priority, tags)
            return jsonify({'success': True, 'action': 'remember', 'topic': topic})
            
        elif action == 'recall':
            topic = params.get('topic')
            agent = params.get('agent', 'claude')
            
            if not topic:
                return jsonify({'success': False, 'error': 'topic is required'}), 400
            
            content = workspace.recall(topic, agent)
            return jsonify({
                'success': True, 
                'action': 'recall', 
                'topic': topic,
                'content': content,
                'found': content is not None
            })
            
        elif action == 'recall_all':
            agent = params.get('agent', 'claude')
            priority = params.get('priority')
            
            memories = workspace.recall_all(agent, priority)
            return jsonify({
                'success': True,
                'action': 'recall_all',
                'agent': agent,
                'memories': memories,
                'count': len(memories)
            })
            
        elif action == 'get_info':
            info = workspace.get_workspace_info()
            return jsonify({'success': True, 'action': 'get_info', 'workspace_info': info})
            
        elif action == 'store_context':
            key = params.get('key')
            value = params.get('value')
            agent = params.get('agent', 'claude')
            shared = params.get('shared', False)
            
            if not key or not value:
                return jsonify({'success': False, 'error': 'key and value are required'}), 400
            
            workspace.store_context(key, value, agent, shared)
            return jsonify({'success': True, 'action': 'store_context', 'key': key})
            
        elif action == 'get_context':
            key = params.get('key')
            agent = params.get('agent', 'claude')
            
            if not key:
                return jsonify({'success': False, 'error': 'key is required'}), 400
            
            value = workspace.get_context(key, agent)
            return jsonify({
                'success': True,
                'action': 'get_context',
                'key': key,
                'value': value,
                'found': value is not None
            })
            
        else:
            return jsonify({'success': False, 'error': f'Unknown workspace action: {action}'}), 400
            
    except Exception as e:
        logger.error(f"Workspace action error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def handle_puppeteer_action(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Puppeteer automation actions."""
    if not PYPPETEER_AVAILABLE:
        return jsonify({
            'success': False, 
            'error': 'Puppeteer not available. Install with: pip install pyppeteer'
        }), 500
    
    try:
        manager = get_puppeteer_manager()
        
        if action == 'screenshot':
            url = params.get('url')
            filename = params.get('filename')
            
            if url:
                # Navigate and screenshot
                async def screenshot_url():
                    await manager.launch_browser()
                    try:
                        nav_result = await manager.navigate_to(url)
                        if nav_result['success']:
                            screenshot_path = await manager.screenshot(filename)
                            return {
                                'success': True,
                                'action': 'screenshot',
                                'url': url,
                                'screenshot_path': str(screenshot_path),
                                'navigation': nav_result
                            }
                        else:
                            return {'success': False, 'error': nav_result.get('error', 'Navigation failed')}
                    finally:
                        await manager.close_browser()
                
                result = handle_async(screenshot_url())
                return jsonify(result)
            else:
                return jsonify({'success': False, 'error': 'url is required for screenshot'}), 400
                
        elif action == 'navigate':
            url = params.get('url')
            wait_until = params.get('wait_until', 'networkidle2')
            
            if not url:
                return jsonify({'success': False, 'error': 'url is required'}), 400
            
            async def navigate():
                await manager.launch_browser()
                try:
                    result = await manager.navigate_to(url, wait_until)
                    return result
                finally:
                    await manager.close_browser()
            
            result = handle_async(navigate())
            return jsonify({'success': True, 'action': 'navigate', **result})
            
        elif action == 'research_page':
            url = params.get('url')
            selectors = params.get('selectors', {})
            
            if not url:
                return jsonify({'success': False, 'error': 'url is required'}), 400
            
            async def research():
                await manager.launch_browser()
                try:
                    result = await manager.research_page(url, selectors)
                    return result
                finally:
                    await manager.close_browser()
            
            result = handle_async(research())
            return jsonify({'success': True, 'action': 'research_page', **result})
            
        elif action == 'get_screenshot_history':
            history = manager.get_screenshot_history()
            return jsonify({
                'success': True,
                'action': 'get_screenshot_history',
                'screenshots': history,
                'count': len(history)
            })
            
        else:
            return jsonify({'success': False, 'error': f'Unknown puppeteer action: {action}'}), 400
            
    except Exception as e:
        logger.error(f"Puppeteer action error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def handle_research_action(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle research tool actions."""
    if not REQUESTS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Research tools not available. Install with: pip install requests beautifulsoup4'
        }), 500
    
    try:
        manager = get_search_manager()
        
        if action == 'search':
            query = params.get('query')
            count = params.get('count', 10)
            safe_search = params.get('safe_search', 'moderate')
            
            if not query:
                return jsonify({'success': False, 'error': 'query is required'}), 400
            
            result = manager.search(query, count, safe_search)
            return jsonify({'success': True, 'action': 'search', **result})
            
        elif action == 'search_cached':
            query_fragment = params.get('query_fragment')
            
            if not query_fragment:
                return jsonify({'success': False, 'error': 'query_fragment is required'}), 400
            
            results = manager.search_cached(query_fragment)
            return jsonify({
                'success': True,
                'action': 'search_cached',
                'query_fragment': query_fragment,
                'results': results,
                'count': len(results)
            })
            
        elif action == 'get_history':
            workspace_id = params.get('workspace_id')
            history = manager.get_research_history(workspace_id)
            return jsonify({
                'success': True,
                'action': 'get_history',
                'history': history,
                'count': len(history)
            })
            
        elif action == 'clear_cache':
            older_than_days = params.get('older_than_days', 7)
            cleared_count = manager.clear_cache(older_than_days)
            return jsonify({
                'success': True,
                'action': 'clear_cache',
                'cleared_count': cleared_count,
                'older_than_days': older_than_days
            })
            
        else:
            return jsonify({'success': False, 'error': f'Unknown research action: {action}'}), 400
            
    except Exception as e:
        logger.error(f"Research action error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Convenience endpoints for common operations
@mcp_bp.route('/workspace/info', methods=['GET'])
def get_workspace_info():
    """Get current workspace information."""
    try:
        workspace = get_workspace_manager()
        info = workspace.get_workspace_info()
        return jsonify({'success': True, 'workspace_info': info})
    except Exception as e:
        logger.error(f"Workspace info error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/workspace/remember', methods=['POST'])
def remember_in_workspace():
    """Store information in workspace memory."""
    try:
        data = request.get_json()
        workspace = get_workspace_manager()
        
        topic = data.get('topic')
        content = data.get('content')
        agent = data.get('agent', 'claude')
        priority = data.get('priority', 'normal')
        tags = data.get('tags', [])
        
        if not topic or not content:
            return jsonify({'success': False, 'error': 'topic and content are required'}), 400
        
        workspace.remember(topic, content, agent, priority, tags)
        return jsonify({'success': True, 'topic': topic, 'agent': agent})
        
    except Exception as e:
        logger.error(f"Remember error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/workspace/recall', methods=['GET'])
def recall_from_workspace():
    """Retrieve information from workspace memory."""
    try:
        workspace = get_workspace_manager()
        
        topic = request.args.get('topic')
        agent = request.args.get('agent', 'claude')
        
        if not topic:
            return jsonify({'success': False, 'error': 'topic parameter is required'}), 400
        
        content = workspace.recall(topic, agent)
        return jsonify({
            'success': True,
            'topic': topic,
            'content': content,
            'found': content is not None
        })
        
    except Exception as e:
        logger.error(f"Recall error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/puppeteer/screenshot', methods=['POST'])
def take_screenshot():
    """Take a screenshot of a URL."""
    if not PYPPETEER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Puppeteer not available. Install with: pip install pyppeteer'
        }), 500
    
    try:
        data = request.get_json()
        url = data.get('url')
        filename = data.get('filename')
        
        if not url:
            return jsonify({'success': False, 'error': 'url is required'}), 400
        
        manager = get_puppeteer_manager()
        
        async def take_screenshot_async():
            await manager.launch_browser()
            try:
                nav_result = await manager.navigate_to(url)
                if nav_result['success']:
                    screenshot_path = await manager.screenshot(filename)
                    return {
                        'success': True,
                        'url': url,
                        'screenshot_path': str(screenshot_path),
                        'navigation': nav_result
                    }
                else:
                    return {'success': False, 'error': nav_result.get('error', 'Navigation failed')}
            finally:
                await manager.close_browser()
        
        result = handle_async(take_screenshot_async())
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/research/search', methods=['POST'])
def search_web():
    """Search the web with caching."""
    if not REQUESTS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Research tools not available. Install with: pip install requests beautifulsoup4'
        }), 500
    
    try:
        data = request.get_json()
        query = data.get('query')
        count = data.get('count', 10)
        safe_search = data.get('safe_search', 'moderate')
        
        if not query:
            return jsonify({'success': False, 'error': 'query is required'}), 400
        
        manager = get_search_manager()
        result = manager.search(query, count, safe_search)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/research/history', methods=['GET'])
def get_research_history():
    """Get research history."""
    if not REQUESTS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Research tools not available'
        }), 500
    
    try:
        workspace_id = request.args.get('workspace_id')
        manager = get_search_manager()
        history = manager.get_research_history(workspace_id)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history),
            'workspace_id': workspace_id or manager.workspace.workspace_id
        })
        
    except Exception as e:
        logger.error(f"Research history error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/status', methods=['GET'])
def mcp_status():
    """Get overall MCP system status."""
    try:
        workspace = get_workspace_manager()
        
        status = {
            'mcp_system': 'operational',
            'workspace_manager': {
                'active': True,
                'workspace_id': workspace.workspace_id,
                'project_type': workspace._detect_project_type(),
                'memory_count': workspace._get_memory_count(),
                'context_count': workspace._get_context_count()
            },
            'puppeteer_tools': {
                'available': PYPPETEER_AVAILABLE,
                'status': 'ready' if PYPPETEER_AVAILABLE else 'not_installed'
            },
            'research_tools': {
                'available': REQUESTS_AVAILABLE,
                'status': 'ready' if REQUESTS_AVAILABLE else 'not_installed'
            }
        }
        
        return jsonify({'success': True, 'status': status})
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Error handlers
@mcp_bp.errorhandler(404)
def mcp_not_found(error):
    return jsonify({
        'success': False,
        'error': 'MCP endpoint not found',
        'available_endpoints': [
            '/mcp/tools',
            '/mcp/use',
            '/mcp/workspace/info',
            '/mcp/workspace/remember',
            '/mcp/workspace/recall',
            '/mcp/puppeteer/screenshot',
            '/mcp/research/search',
            '/mcp/research/history',
            '/mcp/status'
        ]
    }), 404


@mcp_bp.errorhandler(500)
def mcp_internal_error(error):
    logger.error(f"MCP internal error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal MCP error',
        'message': str(error)
    }), 500
