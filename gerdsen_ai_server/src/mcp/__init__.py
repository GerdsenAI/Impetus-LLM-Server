"""
MCP (Model Context Protocol) Tools for Cross-Project AI Collaboration

This module provides workspace isolation, context management, and cross-project
sharing capabilities for AI agents working across multiple projects.
"""

from .workspace_manager import get_workspace_manager, WorkspaceManager

__all__ = ['get_workspace_manager', 'WorkspaceManager']
