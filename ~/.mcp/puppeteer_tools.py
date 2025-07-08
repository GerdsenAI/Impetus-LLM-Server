"""
Puppeteer Tools for Web Interface Testing and Debugging
Provides web automation, testing, and debugging capabilities
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import base64

try:
    from pyppeteer import launch
    PUPPETEER_AVAILABLE = True
except ImportError:
    PUPPETEER_AVAILABLE = False

logger = logging.getLogger(__name__)

class PuppeteerManager:
    """Manages Puppeteer browser instances for testing and debugging"""
    
    def __init__(self):
        self.browser = None
        self.pages = {}  # Track active pages
        self.default_viewport = {'width': 1280, 'height': 720}
        self.screenshots_dir = Path.home() / ".mcp" / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        if not PUPPETEER_AVAILABLE:
            logger.warning("Puppeteer not available. Install with: pip install pyppeteer")
    
    async def _ensure_browser(self):
        """Ensure browser is launched and ready"""
        if not PUPPETEER_AVAILABLE:
            raise RuntimeError("Puppeteer not available")
        
        if self.browser is None:
            logger.info("Launching Puppeteer browser...")
            self.browser = await launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            logger.info("Browser launched successfully")
    
    async def close_browser(self):
        """Close the browser and clean up"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.pages.clear()
            logger.info("Browser closed")
    
    async def create_page(self, page_id: str = None) -> str:
        """Create a new page and return its ID"""
        await self._ensure_browser()
        
        page = await self.browser.newPage()
        await page.setViewport(self.default_viewport)
        
        if page_id is None:
            page_id = f"page_{int(time.time())}"
        
        self.pages[page_id] = page
        logger.info(f"Created page: {page_id}")
        return page_id
    
    async def close_page(self, page_id: str):
        """Close a specific page"""
        if page_id in self.pages:
            await self.pages[page_id].close()
            del self.pages[page_id]
            logger.info(f"Closed page: {page_id}")
    
    async def navigate_to(self, url: str, page_id: str = None) -> Dict[str, Any]:
        """Navigate to a URL and return page info"""
        if page_id is None:
            page_id = await self.create_page()
        
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        try:
            response = await page.goto(url, waitUntil='networkidle2', timeout=30000)
            
            # Get basic page info
            title = await page.title()
            url_result = page.url
            
            return {
                "page_id": page_id,
                "url": url_result,
                "title": title,
                "status": response.status if response else "unknown",
                "success": True
            }
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return {
                "page_id": page_id,
                "error": str(e),
                "success": False
            }
    
    async def take_screenshot(self, page_id: str, filename: str = None) -> Dict[str, Any]:
        """Take a screenshot of the page"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        if filename is None:
            timestamp = int(time.time())
            filename = f"screenshot_{page_id}_{timestamp}.png"
        
        screenshot_path = self.screenshots_dir / filename
        
        try:
            await page.screenshot({'path': str(screenshot_path), 'fullPage': True})
            
            # Also return base64 for immediate use
            screenshot_buffer = await page.screenshot({'fullPage': True})
            screenshot_b64 = base64.b64encode(screenshot_buffer).decode()
            
            return {
                "success": True,
                "filename": filename,
                "path": str(screenshot_path),
                "base64": screenshot_b64
            }
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def click_element(self, page_id: str, selector: str) -> Dict[str, Any]:
        """Click an element on the page"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        try:
            await page.waitForSelector(selector, timeout=10000)
            await page.click(selector)
            
            return {
                "success": True,
                "selector": selector,
                "action": "clicked"
            }
        except Exception as e:
            logger.error(f"Click error: {e}")
            return {
                "success": False,
                "error": str(e),
                "selector": selector
            }
    
    async def type_text(self, page_id: str, selector: str, text: str) -> Dict[str, Any]:
        """Type text into an element"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        try:
            await page.waitForSelector(selector, timeout=10000)
            await page.type(selector, text)
            
            return {
                "success": True,
                "selector": selector,
                "text": text,
                "action": "typed"
            }
        except Exception as e:
            logger.error(f"Type error: {e}")
            return {
                "success": False,
                "error": str(e),
                "selector": selector
            }
    
    async def evaluate_javascript(self, page_id: str, script: str) -> Dict[str, Any]:
        """Execute JavaScript on the page"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        try:
            result = await page.evaluate(script)
            
            return {
                "success": True,
                "result": result,
                "script": script
            }
        except Exception as e:
            logger.error(f"JavaScript execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "script": script
            }
    
    async def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """Get page HTML content"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        try:
            content = await page.content()
            
            return {
                "success": True,
                "content": content,
                "length": len(content)
            }
        except Exception as e:
            logger.error(f"Content retrieval error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def wait_for_element(self, page_id: str, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        """Wait for an element to appear"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        try:
            await page.waitForSelector(selector, timeout=timeout)
            
            return {
                "success": True,
                "selector": selector,
                "found": True
            }
        except Exception as e:
            logger.error(f"Wait for element error: {e}")
            return {
                "success": False,
                "error": str(e),
                "selector": selector
            }
    
    async def test_impetus_ui(self, base_url: str = "http://localhost:8080") -> Dict[str, Any]:
        """Run automated tests on IMPETUS UI"""
        test_results = []
        
        try:
            # Test 1: Main page loads
            page_id = await self.create_page()
            nav_result = await self.navigate_to(base_url, page_id)
            test_results.append({
                "test": "main_page_load",
                "success": nav_result.get("success", False),
                "details": nav_result
            })
            
            if nav_result.get("success"):
                # Take screenshot of main page
                screenshot_result = await self.take_screenshot(page_id, "main_page.png")
                test_results.append({
                    "test": "main_page_screenshot",
                    "success": screenshot_result.get("success", False),
                    "details": screenshot_result
                })
                
                # Test 2: API endpoints page
                api_nav = await self.navigate_to(f"{base_url}/v1/models", page_id)
                test_results.append({
                    "test": "api_models_endpoint",
                    "success": api_nav.get("success", False),
                    "details": api_nav
                })
                
                # Test 3: Check for common UI elements
                ui_checks = [
                    ("#models", "models_section"),
                    (".model-card", "model_cards"),
                    ("button", "buttons_present")
                ]
                
                # Navigate back to main page for UI tests
                await self.navigate_to(base_url, page_id)
                
                for selector, test_name in ui_checks:
                    wait_result = await self.wait_for_element(page_id, selector, timeout=5000)
                    test_results.append({
                        "test": test_name,
                        "success": wait_result.get("success", False),
                        "details": wait_result
                    })
            
            await self.close_page(page_id)
            
        except Exception as e:
            logger.error(f"UI test error: {e}")
            test_results.append({
                "test": "ui_test_error",
                "success": False,
                "error": str(e)
            })
        
        # Calculate overall success
        successful_tests = sum(1 for result in test_results if result.get("success"))
        total_tests = len(test_results)
        
        return {
            "overall_success": successful_tests == total_tests,
            "successful_tests": successful_tests,
            "total_tests": total_tests,
            "test_results": test_results
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of Puppeteer manager"""
        return {
            "puppeteer_available": PUPPETEER_AVAILABLE,
            "browser_active": self.browser is not None,
            "active_pages": list(self.pages.keys()),
            "screenshots_dir": str(self.screenshots_dir)
        }


# Global instance
_puppeteer_manager = None

def get_puppeteer_manager() -> PuppeteerManager:
    """Get the global Puppeteer manager instance"""
    global _puppeteer_manager
    if _puppeteer_manager is None:
        _puppeteer_manager = PuppeteerManager()
    return _puppeteer_manager

async def run_async_puppeteer_operation(operation, *args, **kwargs):
    """Run a Puppeteer operation asynchronously"""
    manager = get_puppeteer_manager()
    return await getattr(manager, operation)(*args, **kwargs)
