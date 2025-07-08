#!/usr/bin/env python3
"""
Puppeteer Tools for MCP - Web Automation and Screenshots

Provides web automation, screenshot capabilities, and testing tools
for AI agents using pyppeteer (Python port of Puppeteer).

Features:
- Web page automation and interaction
- Screenshot capture with automatic storage
- Form filling and testing
- Research assistance through web scraping
- Integration with workspace manager
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from pyppeteer import launch
    from pyppeteer.browser import Browser
    from pyppeteer.page import Page
    PYPPETEER_AVAILABLE = True
except ImportError:
    PYPPETEER_AVAILABLE = False
    Browser = None
    Page = None

from ..mcp.workspace_manager import get_workspace_manager, MCP_SCREENSHOTS, MCP_LOGS

# Setup logging
logger = logging.getLogger(__name__)


class PuppeteerManager:
    """
    Manages Puppeteer browser automation for AI agents.
    
    Provides web automation capabilities with automatic screenshot
    storage and integration with the workspace manager.
    """
    
    def __init__(self):
        if not PYPPETEER_AVAILABLE:
            raise ImportError("pyppeteer is required. Install with: pip install pyppeteer")
        
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.workspace = get_workspace_manager()
        self.screenshots_dir = MCP_SCREENSHOTS / self.workspace.workspace_id
        self.screenshots_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized Puppeteer manager for workspace: {self.workspace.workspace_id}")
    
    async def launch_browser(self, headless: bool = True, args: List[str] = None) -> Browser:
        """Launch a new browser instance."""
        if self.browser:
            await self.close_browser()
        
        default_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
        
        if args:
            default_args.extend(args)
        
        self.browser = await launch(
            headless=headless,
            args=default_args,
            ignoreHTTPSErrors=True,
            autoClose=False
        )
        
        self.page = await self.browser.newPage()
        await self.page.setViewport({'width': 1280, 'height': 800})
        
        logger.info("Browser launched successfully")
        return self.browser
    
    async def close_browser(self):
        """Close the browser instance."""
        if self.page:
            await self.page.close()
            self.page = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        logger.info("Browser closed")
    
    async def navigate_to(self, url: str, wait_until: str = 'networkidle2') -> Dict[str, Any]:
        """Navigate to a URL and return page information."""
        if not self.page:
            await self.launch_browser()
        
        try:
            response = await self.page.goto(url, {'waitUntil': wait_until})
            
            # Get page information
            title = await self.page.title()
            current_url = self.page.url
            
            # Take screenshot
            screenshot_path = await self.screenshot(f"navigate_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            result = {
                'success': True,
                'url': current_url,
                'title': title,
                'status': response.status if response else None,
                'screenshot': str(screenshot_path)
            }
            
            # Store in workspace memory
            self.workspace.remember(
                f"page_visit_{url}",
                json.dumps(result),
                tags=['puppeteer', 'navigation']
            )
            
            logger.info(f"Navigated to: {url}")
            return result
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    async def screenshot(self, filename: str = None, full_page: bool = True) -> Path:
        """Take a screenshot of the current page."""
        if not self.page:
            raise RuntimeError("No page available. Launch browser first.")
        
        if filename is None:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if not filename.endswith('.png'):
            filename += '.png'
        
        screenshot_path = self.screenshots_dir / filename
        
        await self.page.screenshot({
            'path': str(screenshot_path),
            'fullPage': full_page
        })
        
        logger.info(f"Screenshot saved: {screenshot_path}")
        return screenshot_path
    
    async def click_element(self, selector: str, wait_for: str = None) -> Dict[str, Any]:
        """Click an element on the page."""
        if not self.page:
            raise RuntimeError("No page available. Launch browser first.")
        
        try:
            # Wait for element to be available
            await self.page.waitForSelector(selector, {'timeout': 5000})
            
            # Click the element
            await self.page.click(selector)
            
            # Wait for specified condition if provided
            if wait_for:
                await self.page.waitForSelector(wait_for, {'timeout': 10000})
            
            # Take screenshot after click
            screenshot_path = await self.screenshot(f"click_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            result = {
                'success': True,
                'selector': selector,
                'screenshot': str(screenshot_path)
            }
            
            logger.info(f"Clicked element: {selector}")
            return result
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'selector': selector
            }
    
    async def fill_form(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Fill form fields with provided data."""
        if not self.page:
            raise RuntimeError("No page available. Launch browser first.")
        
        results = []
        
        for selector, value in form_data.items():
            try:
                await self.page.waitForSelector(selector, {'timeout': 5000})
                await self.page.type(selector, value)
                results.append({'selector': selector, 'success': True})
                logger.info(f"Filled field: {selector}")
            except Exception as e:
                results.append({'selector': selector, 'success': False, 'error': str(e)})
                logger.error(f"Failed to fill field {selector}: {e}")
        
        # Take screenshot after filling form
        screenshot_path = await self.screenshot(f"form_filled_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        return {
            'results': results,
            'screenshot': str(screenshot_path)
        }
    
    async def extract_text(self, selector: str = None) -> Dict[str, Any]:
        """Extract text content from the page or specific element."""
        if not self.page:
            raise RuntimeError("No page available. Launch browser first.")
        
        try:
            if selector:
                await self.page.waitForSelector(selector, {'timeout': 5000})
                text = await self.page.evaluate(f'document.querySelector("{selector}").textContent')
            else:
                text = await self.page.evaluate('document.body.textContent')
            
            result = {
                'success': True,
                'text': text.strip() if text else '',
                'selector': selector,
                'length': len(text.strip()) if text else 0
            }
            
            logger.info(f"Extracted text from: {selector or 'body'}")
            return result
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'selector': selector
            }
    
    async def wait_for_element(self, selector: str, timeout: int = 10000) -> Dict[str, Any]:
        """Wait for an element to appear on the page."""
        if not self.page:
            raise RuntimeError("No page available. Launch browser first.")
        
        try:
            await self.page.waitForSelector(selector, {'timeout': timeout})
            
            result = {
                'success': True,
                'selector': selector,
                'found': True
            }
            
            logger.info(f"Element found: {selector}")
            return result
            
        except Exception as e:
            logger.error(f"Element wait failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'selector': selector,
                'found': False
            }
    
    async def evaluate_javascript(self, js_code: str) -> Dict[str, Any]:
        """Execute JavaScript code on the page."""
        if not self.page:
            raise RuntimeError("No page available. Launch browser first.")
        
        try:
            result = await self.page.evaluate(js_code)
            
            response = {
                'success': True,
                'result': result,
                'code': js_code
            }
            
            logger.info("JavaScript executed successfully")
            return response
            
        except Exception as e:
            logger.error(f"JavaScript execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'code': js_code
            }
    
    async def research_page(self, url: str, extract_selectors: Dict[str, str] = None) -> Dict[str, Any]:
        """Research a web page by navigating and extracting information."""
        nav_result = await self.navigate_to(url)
        
        if not nav_result['success']:
            return nav_result
        
        research_data = {
            'url': url,
            'title': nav_result['title'],
            'navigation': nav_result,
            'extracted_data': {}
        }
        
        # Extract data using provided selectors
        if extract_selectors:
            for key, selector in extract_selectors.items():
                extraction_result = await self.extract_text(selector)
                research_data['extracted_data'][key] = extraction_result
        
        # Extract common elements
        common_extractions = {
            'page_title': 'title',
            'meta_description': 'meta[name="description"]',
            'headings': 'h1, h2, h3',
            'links': 'a[href]'
        }
        
        for key, selector in common_extractions.items():
            if key not in research_data['extracted_data']:
                extraction_result = await self.extract_text(selector)
                research_data['extracted_data'][key] = extraction_result
        
        # Store research results
        self.workspace.store_research(
            query=f"web_research_{url}",
            results=research_data,
            source="puppeteer"
        )
        
        logger.info(f"Research completed for: {url}")
        return research_data
    
    async def test_website(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run automated tests on a website."""
        test_results = {
            'config': test_config,
            'results': [],
            'success_count': 0,
            'failure_count': 0,
            'start_time': datetime.now().isoformat()
        }
        
        url = test_config.get('url')
        tests = test_config.get('tests', [])
        
        if not url:
            return {'error': 'No URL provided in test config'}
        
        # Navigate to the test URL
        nav_result = await self.navigate_to(url)
        test_results['navigation'] = nav_result
        
        if not nav_result['success']:
            return test_results
        
        # Run tests
        for test in tests:
            test_type = test.get('type')
            test_name = test.get('name', f"test_{len(test_results['results'])}")
            
            try:
                if test_type == 'click':
                    result = await self.click_element(test['selector'], test.get('wait_for'))
                elif test_type == 'fill_form':
                    result = await self.fill_form(test['form_data'])
                elif test_type == 'extract_text':
                    result = await self.extract_text(test['selector'])
                elif test_type == 'wait_for_element':
                    result = await self.wait_for_element(test['selector'], test.get('timeout', 10000))
                elif test_type == 'javascript':
                    result = await self.evaluate_javascript(test['code'])
                else:
                    result = {'success': False, 'error': f"Unknown test type: {test_type}"}
                
                result['test_name'] = test_name
                result['test_type'] = test_type
                test_results['results'].append(result)
                
                if result.get('success'):
                    test_results['success_count'] += 1
                else:
                    test_results['failure_count'] += 1
                    
            except Exception as e:
                error_result = {
                    'test_name': test_name,
                    'test_type': test_type,
                    'success': False,
                    'error': str(e)
                }
                test_results['results'].append(error_result)
                test_results['failure_count'] += 1
        
        test_results['end_time'] = datetime.now().isoformat()
        test_results['total_tests'] = len(tests)
        
        # Store test results
        self.workspace.remember(
            f"test_results_{url}",
            json.dumps(test_results),
            tags=['puppeteer', 'testing', 'automation']
        )
        
        logger.info(f"Testing completed: {test_results['success_count']}/{test_results['total_tests']} passed")
        return test_results
    
    def get_screenshot_history(self) -> List[Dict[str, Any]]:
        """Get list of all screenshots taken in this workspace."""
        screenshots = []
        
        for screenshot_file in self.screenshots_dir.glob("*.png"):
            screenshots.append({
                'filename': screenshot_file.name,
                'path': str(screenshot_file),
                'size': screenshot_file.stat().st_size,
                'created': datetime.fromtimestamp(screenshot_file.stat().st_ctime).isoformat()
            })
        
        return sorted(screenshots, key=lambda x: x['created'], reverse=True)


# Global puppeteer manager instance
_puppeteer_manager = None


def get_puppeteer_manager() -> PuppeteerManager:
    """Get or create the global Puppeteer manager instance."""
    global _puppeteer_manager
    
    if _puppeteer_manager is None:
        _puppeteer_manager = PuppeteerManager()
    
    return _puppeteer_manager


# Utility functions for common operations
async def quick_screenshot(url: str, filename: str = None) -> str:
    """Take a quick screenshot of a URL."""
    manager = get_puppeteer_manager()
    
    try:
        await manager.launch_browser()
        await manager.navigate_to(url)
        screenshot_path = await manager.screenshot(filename)
        return str(screenshot_path)
    finally:
        await manager.close_browser()


async def quick_research(url: str, selectors: Dict[str, str] = None) -> Dict[str, Any]:
    """Quickly research a web page."""
    manager = get_puppeteer_manager()
    
    try:
        await manager.launch_browser()
        return await manager.research_page(url, selectors)
    finally:
        await manager.close_browser()
