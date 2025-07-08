#!/usr/bin/env python3
"""
MCP Setup Validation Script

Tests all MCP (Model Context Protocol) components to ensure proper setup
and functionality across workspace isolation, Puppeteer tools, and research capabilities.

Run this script to validate MCP setup after installation.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test results storage
test_results = []

def test_result(test_name: str, success: bool, details: str = "", data: Dict[str, Any] = None):
    """Record a test result."""
    result = {
        'test': test_name,
        'success': success,
        'details': details,
        'data': data or {}
    }
    test_results.append(result)
    
    status = "✅" if success else "❌"
    print(f"{status} {test_name}: {details}")
    
    if not success:
        logger.error(f"Test failed: {test_name} - {details}")


def test_dependencies():
    """Test that all required dependencies are available."""
    print("\n🔧 Testing Dependencies...")
    
    # Test GitPython
    try:
        import git
        test_result("GitPython", True, "Available for git repository detection")
    except ImportError:
        test_result("GitPython", False, "Missing - install with: pip install GitPython")
    
    # Test pyppeteer
    try:
        import pyppeteer
        test_result("pyppeteer", True, "Available for web automation")
    except ImportError:
        test_result("pyppeteer", False, "Missing - install with: pip install pyppeteer")
    
    # Test requests
    try:
        import requests
        test_result("requests", True, "Available for web search")
    except ImportError:
        test_result("requests", False, "Missing - install with: pip install requests")
    
    # Test beautifulsoup4
    try:
        from bs4 import BeautifulSoup
        test_result("beautifulsoup4", True, "Available for web scraping")
    except ImportError:
        test_result("beautifulsoup4", False, "Missing - install with: pip install beautifulsoup4")


def test_mcp_directories():
    """Test that MCP directories are created and accessible."""
    print("\n📁 Testing MCP Directories...")
    
    mcp_home = Path.home() / ".mcp"
    required_dirs = [
        mcp_home,
        mcp_home / "databases",
        mcp_home / "screenshots", 
        mcp_home / "research_cache",
        mcp_home / "file_storage",
        mcp_home / "logs"
    ]
    
    for directory in required_dirs:
        if directory.exists() and directory.is_dir():
            test_result(f"Directory {directory.name}", True, f"Created at {directory}")
        else:
            test_result(f"Directory {directory.name}", False, f"Missing at {directory}")


def test_workspace_manager():
    """Test workspace manager functionality."""
    print("\n🏗️ Testing Workspace Manager...")
    
    try:
        # Import and initialize
        from gerdsen_ai_server.src.mcp.workspace_manager import get_workspace_manager
        
        workspace = get_workspace_manager()
        test_result("Workspace Initialization", True, f"Workspace ID: {workspace.workspace_id}")
        
        # Test workspace info
        info = workspace.get_workspace_info()
        test_result("Workspace Info", True, f"Project type: {info['project_type']}")
        
        # Test memory operations
        test_topic = "mcp_test"
        test_content = "This is a test of MCP memory functionality"
        
        workspace.remember(test_topic, test_content, "test_agent")
        test_result("Memory Store", True, f"Stored: {test_topic}")
        
        recalled = workspace.recall(test_topic, "test_agent")
        if recalled == test_content:
            test_result("Memory Recall", True, "Successfully recalled stored content")
        else:
            test_result("Memory Recall", False, f"Expected '{test_content}', got '{recalled}'")
        
        # Test context operations
        workspace.store_context("test_key", "test_value", "test_agent")
        context_value = workspace.get_context("test_key", "test_agent")
        
        if context_value == "test_value":
            test_result("Context Storage", True, "Context stored and retrieved successfully")
        else:
            test_result("Context Storage", False, f"Expected 'test_value', got '{context_value}'")
            
    except Exception as e:
        test_result("Workspace Manager", False, f"Error: {str(e)}")


def test_puppeteer_tools():
    """Test Puppeteer automation tools."""
    print("\n🌐 Testing Puppeteer Tools...")
    
    try:
        from gerdsen_ai_server.src.debug.puppeteer_tools import get_puppeteer_manager, PYPPETEER_AVAILABLE
        
        if not PYPPETEER_AVAILABLE:
            test_result("Puppeteer Availability", False, "pyppeteer not installed")
            return
        
        test_result("Puppeteer Availability", True, "pyppeteer installed and available")
        
        manager = get_puppeteer_manager()
        test_result("Puppeteer Manager", True, f"Initialized for workspace: {manager.workspace.workspace_id}")
        
        # Test screenshot history (doesn't require browser)
        history = manager.get_screenshot_history()
        test_result("Screenshot History", True, f"Retrieved history with {len(history)} items")
        
        # Test async browser operations (basic test)
        async def test_browser():
            try:
                await manager.launch_browser()
                test_result("Browser Launch", True, "Browser launched successfully")
                
                await manager.close_browser()
                test_result("Browser Close", True, "Browser closed successfully")
                return True
            except Exception as e:
                test_result("Browser Operations", False, f"Browser error: {str(e)}")
                return False
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(test_browser())
        loop.close()
        
    except Exception as e:
        test_result("Puppeteer Tools", False, f"Error: {str(e)}")


def test_research_tools():
    """Test research and search tools."""
    print("\n🔍 Testing Research Tools...")
    
    try:
        from gerdsen_ai_server.src.research.brave_search import get_search_manager, REQUESTS_AVAILABLE
        
        if not REQUESTS_AVAILABLE:
            test_result("Research Availability", False, "requests not installed")
            return
        
        test_result("Research Availability", True, "requests installed and available")
        
        manager = get_search_manager()
        test_result("Research Manager", True, f"Initialized for workspace: {manager.workspace.workspace_id}")
        
        # Test cache operations
        history = manager.get_research_history()
        test_result("Research History", True, f"Retrieved history with {len(history)} items")
        
        # Test cached search
        cached_results = manager.search_cached("test")
        test_result("Cached Search", True, f"Found {len(cached_results)} cached results")
        
        # Test rate limiting
        can_request = manager._can_make_request()
        test_result("Rate Limiting", True, f"Can make requests: {can_request}")
        
    except Exception as e:
        test_result("Research Tools", False, f"Error: {str(e)}")


def test_flask_integration():
    """Test Flask route integration."""
    print("\n🌐 Testing Flask Integration...")
    
    try:
        from gerdsen_ai_server.src.routes.mcp_routes import mcp_bp
        test_result("MCP Blueprint", True, "Flask blueprint imported successfully")
        
        # Test that blueprint has expected routes
        expected_routes = [
            '/mcp/tools',
            '/mcp/use', 
            '/mcp/workspace/info',
            '/mcp/status'
        ]
        
        # Get blueprint rules
        rules = [rule.rule for rule in mcp_bp.url_map.iter_rules()]
        
        for route in expected_routes:
            if any(route in rule for rule in rules):
                test_result(f"Route {route}", True, "Route registered in blueprint")
            else:
                test_result(f"Route {route}", False, "Route not found in blueprint")
                
    except Exception as e:
        test_result("Flask Integration", False, f"Error: {str(e)}")


def test_production_server_integration():
    """Test integration with production server."""
    print("\n🚀 Testing Production Server Integration...")
    
    try:
        # Check if we can import the main server module
        from gerdsen_ai_server.src.production_main import app
        test_result("Production Server Import", True, "Successfully imported Flask app")
        
        # Check if MCP blueprint is registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        
        if 'mcp' in blueprint_names:
            test_result("MCP Blueprint Registration", True, "MCP blueprint registered with Flask app")
        else:
            test_result("MCP Blueprint Registration", False, "MCP blueprint not registered - need to add to production_main.py")
        
    except Exception as e:
        test_result("Production Server Integration", False, f"Error: {str(e)}")


def generate_test_report():
    """Generate and display test report."""
    print("\n" + "="*60)
    print("🧪 MCP SETUP TEST REPORT")
    print("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result['success'])
    failed_tests = total_tests - passed_tests
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FAILED TESTS:")
        for result in test_results:
            if not result['success']:
                print(f"  • {result['test']}: {result['details']}")
    
    print("\n📊 TEST CATEGORIES:")
    categories = {}
    for result in test_results:
        category = result['test'].split()[0]
        if category not in categories:
            categories[category] = {'passed': 0, 'failed': 0}
        
        if result['success']:
            categories[category]['passed'] += 1
        else:
            categories[category]['failed'] += 1
    
    for category, stats in categories.items():
        total = stats['passed'] + stats['failed']
        success_rate = (stats['passed'] / total) * 100 if total > 0 else 0
        print(f"  {category}: {stats['passed']}/{total} ({success_rate:.1f}%)")
    
    # Installation instructions for failed dependencies
    if failed_tests > 0:
        print("\n💡 INSTALLATION HELP:")
        print("If dependencies are missing, install them with:")
        print("pip install --user GitPython pyppeteer requests beautifulsoup4")
        print("\nFor global installation:")
        print("pip install GitPython pyppeteer requests beautifulsoup4")
    
    return passed_tests == total_tests


def main():
    """Run all MCP setup tests."""
    print("🚀 Starting MCP Setup Validation")
    print("="*50)
    
    # Run all tests
    test_dependencies()
    test_mcp_directories()
    test_workspace_manager()
    test_puppeteer_tools()
    test_research_tools()
    test_flask_integration()
    test_production_server_integration()
    
    # Generate report
    success = generate_test_report()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! MCP setup is complete and functional.")
        print("\nNext steps:")
        print("1. Start your Flask server")
        print("2. Test MCP endpoints at http://localhost:8080/mcp/status")
        print("3. Begin using MCP tools in your AI agent workflows")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above and install missing dependencies.")
        sys.exit(1)


if __name__ == "__main__":
    main()
