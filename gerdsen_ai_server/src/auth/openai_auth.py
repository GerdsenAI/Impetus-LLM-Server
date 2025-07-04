#!/usr/bin/env python3
"""
OpenAI API Authentication Middleware
Provides API key authentication for OpenAI-compatible endpoints
"""

import os
import hashlib
import hmac
import time
import logging
from functools import wraps
from typing import Optional, Dict, Any

from flask import request, jsonify, current_app

class OpenAIAuth:
    """OpenAI API authentication handler"""
    
    def __init__(self, app=None):
        self.app = app
        self.api_keys = set()
        self.master_key = None
        self.logger = logging.getLogger(__name__)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize authentication with Flask app"""
        self.app = app
        
        # Load configuration
        self.master_key = app.config.get('OPENAI_MASTER_KEY', 'gerdsen-ai-master-key-2025')
        
        # Load API keys from environment or config
        env_keys = os.environ.get('OPENAI_API_KEYS', '')
        if env_keys:
            self.api_keys.update(env_keys.split(','))
        
        # Add default development keys
        self.api_keys.add('sk-dev-gerdsen-ai-local-development-key')
        self.api_keys.add('sk-test-gerdsen-ai-testing-key')
        
        self.logger.info(f"OpenAI Auth initialized with {len(self.api_keys)} API keys")
    
    def add_api_key(self, api_key: str) -> bool:
        """Add a new API key"""
        if not api_key or len(api_key) < 10:
            return False
        
        self.api_keys.add(api_key)
        self.logger.info(f"Added API key: {api_key[:10]}...")
        return True
    
    def remove_api_key(self, api_key: str) -> bool:
        """Remove an API key"""
        if api_key in self.api_keys:
            self.api_keys.remove(api_key)
            self.logger.info(f"Removed API key: {api_key[:10]}...")
            return True
        return False
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate an API key"""
        if not api_key:
            return False
        
        # Check against stored keys
        if api_key in self.api_keys:
            return True
        
        # Check against master key
        if api_key == self.master_key:
            return True
        
        # For development: accept any key starting with 'sk-'
        if current_app.debug and api_key.startswith('sk-'):
            self.logger.debug(f"Accepting debug API key: {api_key[:10]}...")
            return True
        
        return False
    
    def extract_api_key(self, request) -> Optional[str]:
        """Extract API key from request"""
        # Check Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Check query parameter (less secure, for testing)
        api_key = request.args.get('api_key')
        if api_key:
            return api_key
        
        # Check form data
        if request.is_json:
            data = request.get_json(silent=True)
            if data and 'api_key' in data:
                return data['api_key']
        
        return None
    
    def require_api_key(self, f):
        """Decorator to require API key authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = self.extract_api_key(request)
            
            if not api_key:
                return jsonify({
                    "error": {
                        "message": "No API key provided",
                        "type": "authentication_error",
                        "code": "missing_api_key"
                    }
                }), 401
            
            if not self.validate_api_key(api_key):
                return jsonify({
                    "error": {
                        "message": "Invalid API key",
                        "type": "authentication_error", 
                        "code": "invalid_api_key"
                    }
                }), 401
            
            # Add API key to request context
            request.api_key = api_key
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def optional_api_key(self, f):
        """Decorator for optional API key authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = self.extract_api_key(request)
            
            # Add API key to request context (may be None)
            request.api_key = api_key
            request.authenticated = self.validate_api_key(api_key) if api_key else False
            
            return f(*args, **kwargs)
        
        return decorated_function

class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self):
        self.requests = {}  # {api_key: [(timestamp, count), ...]}
        self.limits = {
            'default': {'requests': 100, 'window': 3600},  # 100 requests per hour
            'premium': {'requests': 1000, 'window': 3600},  # 1000 requests per hour
        }
        self.logger = logging.getLogger(__name__)
    
    def is_rate_limited(self, api_key: str, tier: str = 'default') -> bool:
        """Check if API key is rate limited"""
        now = time.time()
        limit_config = self.limits.get(tier, self.limits['default'])
        
        # Clean old entries
        if api_key in self.requests:
            self.requests[api_key] = [
                (ts, count) for ts, count in self.requests[api_key]
                if now - ts < limit_config['window']
            ]
        else:
            self.requests[api_key] = []
        
        # Count requests in current window
        total_requests = sum(count for ts, count in self.requests[api_key])
        
        if total_requests >= limit_config['requests']:
            self.logger.warning(f"Rate limit exceeded for API key: {api_key[:10]}...")
            return True
        
        # Add current request
        self.requests[api_key].append((now, 1))
        return False
    
    def rate_limit(self, tier: str = 'default'):
        """Decorator to apply rate limiting"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                api_key = getattr(request, 'api_key', None)
                
                if api_key and self.is_rate_limited(api_key, tier):
                    return jsonify({
                        "error": {
                            "message": "Rate limit exceeded",
                            "type": "rate_limit_error",
                            "code": "rate_limit_exceeded"
                        }
                    }), 429
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator

# Global instances
openai_auth = OpenAIAuth()
rate_limiter = RateLimiter()

def init_openai_auth(app):
    """Initialize OpenAI authentication with Flask app"""
    openai_auth.init_app(app)
    
    # Add authentication endpoints
    @app.route('/v1/auth/keys', methods=['GET'])
    @openai_auth.require_api_key
    def list_api_keys():
        """List API keys (admin only)"""
        api_key = request.api_key
        
        # Only master key can list keys
        if api_key != openai_auth.master_key:
            return jsonify({
                "error": {
                    "message": "Insufficient permissions",
                    "type": "permission_error"
                }
            }), 403
        
        # Return masked keys for security
        masked_keys = [f"{key[:10]}..." for key in openai_auth.api_keys]
        
        return jsonify({
            "keys": masked_keys,
            "count": len(openai_auth.api_keys)
        })
    
    @app.route('/v1/auth/keys', methods=['POST'])
    @openai_auth.require_api_key
    def create_api_key():
        """Create a new API key (admin only)"""
        api_key = request.api_key
        
        # Only master key can create keys
        if api_key != openai_auth.master_key:
            return jsonify({
                "error": {
                    "message": "Insufficient permissions",
                    "type": "permission_error"
                }
            }), 403
        
        data = request.get_json()
        new_key = data.get('key') if data else None
        
        if not new_key:
            # Generate a new key
            import secrets
            new_key = f"sk-gerdsen-{secrets.token_urlsafe(32)}"
        
        if openai_auth.add_api_key(new_key):
            return jsonify({
                "key": new_key,
                "message": "API key created successfully"
            })
        else:
            return jsonify({
                "error": {
                    "message": "Failed to create API key",
                    "type": "creation_error"
                }
            }), 400
    
    @app.route('/v1/auth/validate', methods=['POST'])
    def validate_api_key():
        """Validate an API key"""
        api_key = openai_auth.extract_api_key(request)
        
        if not api_key:
            return jsonify({
                "valid": False,
                "error": "No API key provided"
            })
        
        is_valid = openai_auth.validate_api_key(api_key)
        
        return jsonify({
            "valid": is_valid,
            "key": f"{api_key[:10]}..." if is_valid else None
        })

# Export decorators for use in routes
require_api_key = openai_auth.require_api_key
optional_api_key = openai_auth.optional_api_key
rate_limit = rate_limiter.rate_limit

