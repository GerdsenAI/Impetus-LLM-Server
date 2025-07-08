#!/usr/bin/env python3
"""
Brave Search API Integration for MCP Tools

Provides web search capabilities with intelligent caching and rate limiting.
Integrates with workspace manager for cross-project research sharing.

Features:
- Cached search results to prevent duplicate API calls
- Rate limiting and quota management
- Cross-project research sharing
- Integration with workspace isolation
"""

import os
import json
import time
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from ..mcp.workspace_manager import get_workspace_manager, MCP_RESEARCH_CACHE

# Setup logging
logger = logging.getLogger(__name__)

# Brave Search API configuration
BRAVE_SEARCH_API_URL = "https://api.search.brave.com/res/v1/web/search"
DEFAULT_RATE_LIMIT = 100  # requests per hour


class BraveSearchManager:
    """
    Manages Brave Search API integration with intelligent caching.
    
    Features:
    - Automatic caching of search results
    - Rate limiting and quota management
    - Cross-workspace research sharing
    - Fallback to web scraping when API is unavailable
    """
    
    def __init__(self, api_key: str = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests is required. Install with: pip install requests")
        
        self.api_key = api_key or os.getenv('BRAVE_SEARCH_API_KEY')
        self.workspace = get_workspace_manager()
        self.cache_dir = MCP_RESEARCH_CACHE
        self.rate_limit_file = self.cache_dir / "rate_limit.json"
        self.requests_made = self._load_rate_limit_data()
        
        logger.info(f"Initialized Brave Search manager for workspace: {self.workspace.workspace_id}")
    
    def _load_rate_limit_data(self) -> Dict[str, Any]:
        """Load rate limiting data from file."""
        if self.rate_limit_file.exists():
            try:
                with open(self.rate_limit_file, 'r') as f:
                    data = json.load(f)
                    
                # Reset if it's a new hour
                last_reset = datetime.fromisoformat(data.get('last_reset', '2000-01-01T00:00:00'))
                if datetime.now() - last_reset > timedelta(hours=1):
                    data = {'count': 0, 'last_reset': datetime.now().isoformat()}
                    
                return data
            except (json.JSONDecodeError, ValueError):
                pass
        
        return {'count': 0, 'last_reset': datetime.now().isoformat()}
    
    def _save_rate_limit_data(self):
        """Save rate limiting data to file."""
        with open(self.rate_limit_file, 'w') as f:
            json.dump(self.requests_made, f)
    
    def _can_make_request(self) -> bool:
        """Check if we can make another API request."""
        return self.requests_made['count'] < DEFAULT_RATE_LIMIT
    
    def _increment_request_count(self):
        """Increment the request counter."""
        self.requests_made['count'] += 1
        self._save_rate_limit_data()
    
    def _generate_cache_key(self, query: str, params: Dict[str, Any] = None) -> str:
        """Generate cache key for a search query."""
        cache_data = {'query': query.lower().strip()}
        if params:
            cache_data.update(params)
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cached_results(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached search results if available and fresh."""
        cache_file = self.cache_dir / f"search_{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is still fresh (24 hours)
            cached_time = datetime.fromisoformat(cached_data.get('cached_at', '2000-01-01T00:00:00'))
            if datetime.now() - cached_time < timedelta(hours=24):
                logger.info(f"Using cached results for query: {cached_data.get('query', 'unknown')}")
                return cached_data
                
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
        
        return None
    
    def _cache_results(self, cache_key: str, query: str, results: Dict[str, Any]):
        """Cache search results for future use."""
        cache_data = {
            'query': query,
            'results': results,
            'cached_at': datetime.now().isoformat(),
            'workspace_id': self.workspace.workspace_id,
            'source': 'brave_search'
        }
        
        cache_file = self.cache_dir / f"search_{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Cached search results: {query}")
        except Exception as e:
            logger.error(f"Failed to cache results: {e}")
    
    def search(self, query: str, count: int = 10, safe_search: str = "moderate") -> Dict[str, Any]:
        """
        Search using Brave Search API with caching.
        
        Args:
            query: Search query string
            count: Number of results to return (max 20)
            safe_search: Safe search setting ("strict", "moderate", "off")
            
        Returns:
            Dictionary containing search results and metadata
        """
        # Generate cache key
        params = {'count': count, 'safe_search': safe_search}
        cache_key = self._generate_cache_key(query, params)
        
        # Try to get cached results first
        cached_results = self._get_cached_results(cache_key)
        if cached_results:
            return {
                'success': True,
                'query': query,
                'results': cached_results['results'],
                'from_cache': True,
                'cached_at': cached_results['cached_at']
            }
        
        # Check if we have API key and can make requests
        if not self.api_key:
            logger.warning("No Brave Search API key provided")
            return self._fallback_search(query, count)
        
        if not self._can_make_request():
            logger.warning("Rate limit exceeded, using fallback search")
            return self._fallback_search(query, count)
        
        # Make API request
        try:
            headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip',
                'X-Subscription-Token': self.api_key
            }
            
            params = {
                'q': query,
                'count': min(count, 20),  # Brave API max is 20
                'safesearch': safe_search,
                'freshness': 'pw',  # Past week for more recent results
                'text_decorations': False,
                'spellcheck': True
            }
            
            response = requests.get(BRAVE_SEARCH_API_URL, headers=headers, params=params, timeout=10)
            self._increment_request_count()
            
            if response.status_code == 200:
                data = response.json()
                
                # Format results
                formatted_results = self._format_brave_results(data)
                
                # Cache the results
                self._cache_results(cache_key, query, formatted_results)
                
                # Store in workspace for sharing
                self.workspace.store_research(query, formatted_results, 'brave_search')
                
                return {
                    'success': True,
                    'query': query,
                    'results': formatted_results,
                    'from_cache': False,
                    'api_requests_remaining': DEFAULT_RATE_LIMIT - self.requests_made['count']
                }
            else:
                logger.error(f"Brave Search API error: {response.status_code}")
                return self._fallback_search(query, count)
                
        except Exception as e:
            logger.error(f"Brave Search API request failed: {e}")
            return self._fallback_search(query, count)
    
    def _format_brave_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format Brave Search API results."""
        results = []
        
        web_results = data.get('web', {}).get('results', [])
        
        for result in web_results:
            formatted_result = {
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'description': result.get('description', ''),
                'age': result.get('age', ''),
                'language': result.get('language', ''),
                'source': 'brave_search'
            }
            results.append(formatted_result)
        
        return results
    
    def _fallback_search(self, query: str, count: int = 10) -> Dict[str, Any]:
        """
        Fallback search method when API is unavailable.
        Uses web scraping with appropriate delays and headers.
        """
        logger.info(f"Using fallback search for: {query}")
        
        try:
            # Use DuckDuckGo as fallback (no API key required)
            search_url = "https://duckduckgo.com/html/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            params = {'q': query}
            
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200 and BS4_AVAILABLE:
                soup = BeautifulSoup(response.content, 'html.parser')
                results = self._parse_duckduckgo_results(soup)
                
                # Cache fallback results too
                cache_key = self._generate_cache_key(f"fallback_{query}")
                self._cache_results(cache_key, query, results)
                
                return {
                    'success': True,
                    'query': query,
                    'results': results[:count],
                    'from_cache': False,
                    'source': 'fallback_duckduckgo'
                }
            else:
                return {
                    'success': False,
                    'query': query,
                    'error': 'Fallback search failed',
                    'results': []
                }
                
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'results': []
            }
    
    def _parse_duckduckgo_results(self, soup) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo search results from HTML."""
        results = []
        
        try:
            result_divs = soup.find_all('div', class_='web-result')
            
            for div in result_divs:
                title_elem = div.find('a', class_='result__a')
                snippet_elem = div.find('a', class_='result__snippet')
                
                if title_elem:
                    result = {
                        'title': title_elem.get_text(strip=True),
                        'url': title_elem.get('href', ''),
                        'description': snippet_elem.get_text(strip=True) if snippet_elem else '',
                        'source': 'duckduckgo_fallback'
                    }
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Failed to parse DuckDuckGo results: {e}")
        
        return results
    
    def get_research_history(self, workspace_id: str = None) -> List[Dict[str, Any]]:
        """Get research history for current or specified workspace."""
        target_workspace = workspace_id or self.workspace.workspace_id
        
        history = []
        
        # Search cached files
        for cache_file in self.cache_dir.glob("search_*.json"):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                if cached_data.get('workspace_id') == target_workspace:
                    history.append({
                        'query': cached_data['query'],
                        'cached_at': cached_data['cached_at'],
                        'result_count': len(cached_data.get('results', [])),
                        'source': cached_data.get('source', 'unknown')
                    })
                    
            except (json.JSONDecodeError, ValueError, KeyError):
                continue
        
        return sorted(history, key=lambda x: x['cached_at'], reverse=True)
    
    def search_cached(self, query_fragment: str) -> List[Dict[str, Any]]:
        """Search through cached results for queries containing the fragment."""
        matches = []
        
        for cache_file in self.cache_dir.glob("search_*.json"):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                if query_fragment.lower() in cached_data.get('query', '').lower():
                    matches.append({
                        'query': cached_data['query'],
                        'cached_at': cached_data['cached_at'],
                        'results': cached_data['results'],
                        'source': cached_data.get('source', 'unknown')
                    })
                    
            except (json.JSONDecodeError, ValueError, KeyError):
                continue
        
        return sorted(matches, key=lambda x: x['cached_at'], reverse=True)
    
    def clear_cache(self, older_than_days: int = 7):
        """Clear cached search results older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        cleared_count = 0
        
        for cache_file in self.cache_dir.glob("search_*.json"):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                cached_time = datetime.fromisoformat(cached_data.get('cached_at', '2000-01-01T00:00:00'))
                
                if cached_time < cutoff_date:
                    cache_file.unlink()
                    cleared_count += 1
                    
            except (json.JSONDecodeError, ValueError, KeyError, OSError):
                continue
        
        logger.info(f"Cleared {cleared_count} cached search results")
        return cleared_count


# Global search manager instance
_search_manager = None


def get_search_manager(api_key: str = None) -> BraveSearchManager:
    """Get or create the global search manager instance."""
    global _search_manager
    
    if _search_manager is None:
        _search_manager = BraveSearchManager(api_key)
    
    return _search_manager


# Utility functions for quick searches
def quick_search(query: str, count: int = 5) -> List[Dict[str, Any]]:
    """Perform a quick search and return just the results."""
    manager = get_search_manager()
    response = manager.search(query, count)
    return response.get('results', [])


def cached_search(query_fragment: str) -> List[Dict[str, Any]]:
    """Search through cached results."""
    manager = get_search_manager()
    return manager.search_cached(query_fragment)
