"""
Brave Search API Integration for MCP Research Tool
Provides real web search capabilities with caching
"""

import requests
import json
import hashlib
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class BraveSearchManager:
    """Manages Brave Search API integration with caching"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1"
        self.cache_dir = Path.home() / ".mcp" / "research_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        
        if not self.api_key:
            logger.warning("No Brave Search API key provided. Research will use cached results only.")
    
    def _get_cache_path(self, query: str) -> Path:
        """Get cache file path for a query"""
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        return self.cache_dir / f"search_{query_hash}.json"
    
    def _load_from_cache(self, query: str, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
        """Load search results from cache if not expired"""
        cache_path = self._get_cache_path(query)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path) as f:
                cached_data = json.load(f)
            
            # Check if cache is still valid
            cache_age = time.time() - cached_data.get('timestamp', 0)
            if cache_age < (max_age_hours * 3600):
                logger.debug(f"Using cached results for: {query}")
                return cached_data
            else:
                logger.debug(f"Cache expired for: {query}")
                return None
                
        except Exception as e:
            logger.warning(f"Error loading cache: {e}")
            return None
    
    def _save_to_cache(self, query: str, results: Dict[str, Any]):
        """Save search results to cache"""
        cache_path = self._get_cache_path(query)
        
        cache_data = {
            'query': query,
            'results': results,
            'timestamp': time.time(),
            'source': 'brave_search_api'
        }
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"Cached results for: {query}")
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search_web(self, query: str, count: int = 10, use_cache: bool = True) -> Dict[str, Any]:
        """Search the web using Brave Search API"""
        
        # Check cache first if enabled
        if use_cache:
            cached_result = self._load_from_cache(query)
            if cached_result:
                return {
                    'success': True,
                    'query': query,
                    'results': cached_result['results'],
                    'source': 'cache',
                    'cached': True
                }
        
        # If no API key, return error
        if not self.api_key:
            return {
                'success': False,
                'error': 'No Brave Search API key configured',
                'query': query,
                'results': [],
                'source': 'none'
            }
        
        # Make API request
        try:
            self._enforce_rate_limit()
            
            headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip',
                'X-Subscription-Token': self.api_key
            }
            
            params = {
                'q': query,
                'count': count,
                'search_lang': 'en',
                'country': 'US',
                'safesearch': 'moderate',
                'freshness': 'pw'  # Past week for fresher results
            }
            
            response = requests.get(
                f"{self.base_url}/web/search",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract and format results
                results = []
                web_results = data.get('web', {}).get('results', [])
                
                for item in web_results:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'description': item.get('description', ''),
                        'age': item.get('age', ''),
                        'language': item.get('language', 'en')
                    })
                
                result_data = {
                    'success': True,
                    'query': query,
                    'results': results,
                    'total_results': len(results),
                    'source': 'brave_search_api',
                    'cached': False
                }
                
                # Cache the results
                if use_cache:
                    self._save_to_cache(query, results)
                
                logger.info(f"Brave Search API returned {len(results)} results for: {query}")
                return result_data
                
            else:
                logger.error(f"Brave Search API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'API request failed: {response.status_code}',
                    'query': query,
                    'results': [],
                    'source': 'brave_search_api'
                }
                
        except Exception as e:
            logger.error(f"Brave Search API exception: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'results': [],
                'source': 'brave_search_api'
            }
    
    def search_news(self, query: str, count: int = 10, use_cache: bool = True) -> Dict[str, Any]:
        """Search for news using Brave Search API"""
        
        # Check cache first
        cache_key = f"news_{query}"
        if use_cache:
            cached_result = self._load_from_cache(cache_key, max_age_hours=6)  # News expires faster
            if cached_result:
                return {
                    'success': True,
                    'query': query,
                    'results': cached_result['results'],
                    'source': 'cache',
                    'cached': True,
                    'type': 'news'
                }
        
        if not self.api_key:
            return {
                'success': False,
                'error': 'No Brave Search API key configured',
                'query': query,
                'results': [],
                'source': 'none',
                'type': 'news'
            }
        
        try:
            self._enforce_rate_limit()
            
            headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip',
                'X-Subscription-Token': self.api_key
            }
            
            params = {
                'q': query,
                'count': count,
                'search_lang': 'en',
                'country': 'US',
                'safesearch': 'moderate',
                'freshness': 'pd'  # Past day for news
            }
            
            response = requests.get(
                f"{self.base_url}/news/search",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                results = []
                news_results = data.get('results', [])
                
                for item in news_results:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'description': item.get('description', ''),
                        'age': item.get('age', ''),
                        'source': item.get('meta_url', {}).get('hostname', ''),
                        'published': item.get('age', '')
                    })
                
                result_data = {
                    'success': True,
                    'query': query,
                    'results': results,
                    'total_results': len(results),
                    'source': 'brave_search_api',
                    'cached': False,
                    'type': 'news'
                }
                
                if use_cache:
                    self._save_to_cache(cache_key, results)
                
                logger.info(f"Brave Search News API returned {len(results)} results for: {query}")
                return result_data
                
            else:
                logger.error(f"Brave Search News API error: {response.status_code}")
                return {
                    'success': False,
                    'error': f'News API request failed: {response.status_code}',
                    'query': query,
                    'results': [],
                    'source': 'brave_search_api',
                    'type': 'news'
                }
                
        except Exception as e:
            logger.error(f"Brave Search News API exception: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'results': [],
                'source': 'brave_search_api',
                'type': 'news'
            }
    
    def research_topic(self, topic: str, include_news: bool = True) -> Dict[str, Any]:
        """Comprehensive research on a topic combining web and news search"""
        
        # Web search
        web_results = self.search_web(topic, count=8)
        
        # News search if requested
        news_results = None
        if include_news:
            news_results = self.search_news(topic, count=5)
        
        # Combine results
        research_data = {
            'topic': topic,
            'timestamp': time.time(),
            'web_search': web_results,
            'news_search': news_results,
            'success': web_results.get('success', False)
        }
        
        # Create summary
        all_results = []
        if web_results.get('success'):
            all_results.extend(web_results.get('results', []))
        if news_results and news_results.get('success'):
            all_results.extend(news_results.get('results', []))
        
        research_data['summary'] = {
            'total_results': len(all_results),
            'web_results': len(web_results.get('results', [])),
            'news_results': len(news_results.get('results', [])) if news_results else 0,
            'sources': list(set([r.get('source', r.get('url', '').split('/')[2] if r.get('url') else '') 
                                for r in all_results if r.get('url')]))[:10]
        }
        
        return research_data
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the research cache"""
        cache_files = list(self.cache_dir.glob("search_*.json"))
        
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'cache_directory': str(self.cache_dir),
            'cached_searches': len(cache_files),
            'total_cache_size_bytes': total_size,
            'total_cache_size_mb': round(total_size / (1024 * 1024), 2),
            'api_key_configured': bool(self.api_key)
        }
    
    def clear_cache(self, older_than_days: int = 30) -> Dict[str, Any]:
        """Clear old cache files"""
        cache_files = list(self.cache_dir.glob("search_*.json"))
        
        cutoff_time = time.time() - (older_than_days * 24 * 3600)
        deleted_count = 0
        
        for cache_file in cache_files:
            if cache_file.stat().st_mtime < cutoff_time:
                try:
                    cache_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Could not delete cache file {cache_file}: {e}")
        
        return {
            'deleted_files': deleted_count,
            'remaining_files': len(list(self.cache_dir.glob("search_*.json"))),
            'cutoff_days': older_than_days
        }


# Global instance
_brave_search_manager = None

def get_brave_search_manager(api_key: str = None) -> BraveSearchManager:
    """Get the global Brave Search manager instance"""
    global _brave_search_manager
    if _brave_search_manager is None:
        _brave_search_manager = BraveSearchManager(api_key)
    return _brave_search_manager
