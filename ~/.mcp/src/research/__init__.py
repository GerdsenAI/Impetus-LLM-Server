"""
Research Tools for Impetus LLM Server
Brave Search API integration with caching for efficient research capabilities
"""

from .brave_search import get_brave_search_manager, BraveSearchManager

__all__ = ['get_brave_search_manager', 'BraveSearchManager']
