"""
Research Tools for MCP - Web Search and Caching

Provides web search capabilities with intelligent caching
to prevent duplicate API calls and reduce costs.
"""

from .brave_search import BraveSearchManager, get_search_manager

__all__ = ['BraveSearchManager', 'get_search_manager']
