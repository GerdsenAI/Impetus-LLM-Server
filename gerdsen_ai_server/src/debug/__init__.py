"""
Debug Tools for MCP - Web Automation and Testing

Provides Puppeteer-based automation, screenshot capabilities,
and testing tools for AI agents.
"""

from .puppeteer_tools import PuppeteerManager, get_puppeteer_manager

__all__ = ['PuppeteerManager', 'get_puppeteer_manager']
