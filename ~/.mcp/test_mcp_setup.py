#!/usr/bin/env python3
"""
Test MCP (Model Context Protocol) Setup
Verifies that all MCP tools are working correctly with workspace isolation
"""

import os
import sys
import json
import time
import asyncio
import logging
from pathlib import Path

# Add the project to Python path
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_workspace_manager():
    """Test workspace manager functionality"""
    try:
        from gerdsen_ai_server.src.mcp.workspace_manager import get_workspace_manager
        
        logger.info("Testing Workspace Manager...")
        workspace_manager = get_workspace_manager()
        
        # Test workspace detection
        workspace_info = workspace_manager.get_workspace_info()
        logger.info(f"✅ Workspace detected: {workspace_info['workspace_id']}")
        logger.info(f"   Project type: {workspace_info['project_type']}")
        logger.info(f"   Root path: {workspace_info['root_path']}")
        
        # Test memory operations
        success = workspace_manager.remember("test_topic", "test_data", "claude", "high")
        if success:
            logger.info("✅ Memory storage working")
        else:
            logger.error("❌ Memory storage failed")
            return False
        
        # Test memory retrieval
        data = workspace_manager.recall("test_topic", "claude")
        if data == "test_data":
            logger.info("✅ Memory retrieval working")
        else:
            logger.error("❌ Memory retrieval failed")
            return False
        
        # Test context operations
        success = workspace_manager.store_context("test_context", '{"test": "value"}', "claude", False)
        if success:
            logger.info("✅ Context storage working")
        else:
            logger.error("❌ Context storage failed")
            return False
        
        retrieved_context = workspace_manager.retrieve_context("test_context", "claude")
        if retrieved_context and '"test": "value"' in retrieved_context:
            logger.info("✅ Context retrieval working")
        else:
            logger.error("❌ Context retrieval failed")
            return False
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Workspace manager test failed: {e}")
        return False

def test_puppeteer_tools():
    """Test Puppeteer tools functionality"""
    try:
        from gerdsen_ai_server.src.debug.puppeteer_tools import get_puppeteer_manager
        
        logger.info("Testing Puppeteer Tools...")
        puppeteer_manager = get_puppeteer_manager()
        
        # Test status
        status = puppeteer_manager.get_status()
        logger.info(f"Puppeteer status: {status}")
        
        if status.get("puppeteer_available"):
            logger.info("✅ Puppeteer is available")
        else:
            logger.warning("⚠️ Puppeteer not available (may need installation)")
            logger.info("   To install: pip install --user pyppeteer")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Puppeteer test failed: {e}")
        return False

def test_brave_search():
    """Test Brave Search functionality"""
    try:
        from gerdsen_ai_server.src.research.brave_search import get_brave_search_manager
        
        logger.info("Testing Brave Search...")
        brave_search = get_brave_search_manager()
        
        # Test cache stats
        cache_stats = brave_search.get_cache_stats()
        logger.info(f"Cache directory: {cache_stats['cache_directory']}")
        logger.info(f"API key configured: {cache_stats['api_key_configured']}")
        
        if cache_stats['api_key_configured']:
            logger.info("✅ Brave Search API key configured")
        else:
            logger.warning("⚠️ Brave Search API key not configured")
            logger.info("   Set BRAVE_SEARCH_API_KEY environment variable")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Brave Search test failed: {e}")
        return False

def test_mcp_routes():
    """Test MCP routes integration"""
    try:
        from gerdsen_ai_server.src.routes.mcp_routes import mcp_bp
        
        logger.info("Testing MCP Routes...")
        
        # Check if blueprint is properly configured
        if mcp_bp.url_prefix == '/mcp':
            logger.info("✅ MCP blueprint configured correctly")
        else:
            logger.error("❌ MCP blueprint configuration error")
            return False
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ MCP routes test failed: {e}")
        return False

def test_shared_config():
    """Test shared MCP configuration"""
    try:
        config_path = Path.home() / ".mcp" / "config.json"
        
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            
            logger.info("✅ Shared MCP configuration found")
            logger.info(f"   Version: {config.get('version')}")
            logger.info(f"   Workspace isolation: {config['global_settings']['workspace_isolation']}")
            
            # Create directories if they don't exist
            base_path = Path(config['database']['base_path'].replace('~', str(Path.home())))
            base_path.mkdir(parents=True, exist_ok=True)
            
            cache_path = Path(config['database']['shared_cache_path'].replace('~', str(Path.home())))
            cache_path.mkdir(parents=True, exist_ok=True)
            
            logger.info("✅ MCP directories created")
            return True
        else:
            logger.error("❌ Shared MCP configuration not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Shared config test failed: {e}")
        return False

def test_server_integration():
    """Test integration with main server"""
    try:
        logger.info("Testing Server Integration...")
        
        # Check if MCP routes are registered in production server
        from gerdsen_ai_server.src.production_main import ProductionFlaskServer
        from gerdsen_ai_server.src.production_gerdsen_ai import ProductionConfig
        
        config = ProductionConfig()
        server = ProductionFlaskServer(config)
        
        # Check if MCP blueprint is registered
        blueprints = [bp.name for bp in server.app.blueprints.values()]
        if 'mcp' in blueprints:
            logger.info("✅ MCP blueprint registered in production server")
        else:
            logger.error("❌ MCP blueprint not registered")
            return False
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Server integration test failed: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are available"""
    logger.info("Checking Dependencies...")
    
    dependencies = {
        'sqlite3': 'Built-in SQLite support',
        'GitPython': 'Git repository detection',
        'pyppeteer': 'Puppeteer web automation',
        'requests': 'HTTP requests for Brave Search',
        'beautifulsoup4': 'HTML parsing (optional)'
    }
    
    missing_deps = []
    
    for dep, description in dependencies.items():
        try:
            if dep == 'sqlite3':
                import sqlite3
            elif dep == 'GitPython':
                import git
            elif dep == 'pyppeteer':
                import pyppeteer
            elif dep == 'requests':
                import requests
            elif dep == 'beautifulsoup4':
                import bs4
            
            logger.info(f"✅ {dep}: {description}")
        except ImportError:
            logger.warning(f"⚠️ {dep}: {description} - NOT INSTALLED")
            missing_deps.append(dep)
    
    if missing_deps:
        logger.info("\nTo install missing dependencies:")
        logger.info("pip install --user " + " ".join(missing_deps))
        return False
    
    return True

def main():
    """Run all MCP tests"""
    logger.info("=" * 50)
    logger.info("IMPETUS MCP SETUP TEST")
    logger.info("=" * 50)
    
    tests = [
        ("Dependencies", check_dependencies),
        ("Shared Config", test_shared_config),
        ("Workspace Manager", test_workspace_manager),
        ("Puppeteer Tools", test_puppeteer_tools),
        ("Brave Search", test_brave_search),
        ("MCP Routes", test_mcp_routes),
        ("Server Integration", test_server_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:20}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All MCP tests passed! Setup is complete.")
        logger.info("\nTo use MCP tools:")
        logger.info("1. Start the server: python gerdsen_ai_server/src/production_main.py")
        logger.info("2. Access MCP endpoints: http://localhost:8080/mcp/tools")
        logger.info("3. Use MCP in code: from gerdsen_ai_server.src.mcp import get_workspace_manager")
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Check the errors above.")
        
        if any("pyppeteer" in str(e) for _, e in results if not e):
            logger.info("\nQuick fix for missing dependencies:")
            logger.info("pip install --user pyppeteer GitPython beautifulsoup4")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
