#!/usr/bin/env python3
"""
Configuration utilities for loading environment variables
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

def load_env_file(env_path: Optional[str] = None) -> bool:
    """
    Load environment variables from .env file
    
    Args:
        env_path: Optional path to .env file. If not provided, searches for .env in project root
        
    Returns:
        bool: True if env file was loaded, False otherwise
    """
    try:
        from dotenv import load_dotenv
        
        if env_path:
            if os.path.exists(env_path):
                load_dotenv(env_path)
                logger.info(f"Loaded environment from: {env_path}")
                return True
        else:
            # Search for .env file in common locations
            search_paths = [
                Path.cwd() / '.env',
                Path.cwd().parent / '.env',
                Path.cwd().parent.parent / '.env',
                Path.home() / '.impetus' / '.env'
            ]
            
            for path in search_paths:
                if path.exists():
                    load_dotenv(path)
                    logger.info(f"Loaded environment from: {path}")
                    return True
                    
        logger.info("No .env file found, using system environment variables")
        return False
        
    except ImportError:
        logger.warning("python-dotenv not installed, using system environment variables only")
        return False

def get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get environment variable with optional default and validation
    
    Args:
        key: Environment variable name
        default: Default value if not found
        required: If True, raises ValueError if not found
        
    Returns:
        Environment variable value or default
        
    Raises:
        ValueError: If required and not found
    """
    value = os.environ.get(key, default)
    
    if required and not value:
        raise ValueError(f"Required environment variable '{key}' not set")
        
    return value

def get_env_bool(key: str, default: bool = False) -> bool:
    """Get environment variable as boolean"""
    value = get_env(key, str(default))
    return value.lower() in ('true', '1', 'yes', 'on', 'enabled')

def get_env_int(key: str, default: int = 0) -> int:
    """Get environment variable as integer"""
    value = get_env(key, str(default))
    try:
        return int(value)
    except ValueError:
        logger.warning(f"Invalid integer value for {key}: {value}, using default: {default}")
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    """Get environment variable as float"""
    value = get_env(key, str(default))
    try:
        return float(value)
    except ValueError:
        logger.warning(f"Invalid float value for {key}: {value}, using default: {default}")
        return default

def get_env_list(key: str, default: Optional[List[str]] = None, separator: str = ',') -> List[str]:
    """Get environment variable as list"""
    value = get_env(key)
    if not value:
        return default or []
    
    # Split and clean values
    return [item.strip() for item in value.split(separator) if item.strip()]

def get_cors_origins() -> List[str]:
    """Get CORS allowed origins from environment"""
    origins = get_env_list('ALLOWED_ORIGINS', default=['http://localhost:8080', 'http://127.0.0.1:8080'])
    
    # Validate origins
    valid_origins = []
    for origin in origins:
        if origin.startswith(('http://', 'https://')):
            # Check for wildcards in production
            if not get_env_bool('DEBUG', False) and '*' in origin:
                logger.warning(f"Wildcard in CORS origin ignored in production: {origin}")
                continue
            valid_origins.append(origin)
        else:
            logger.warning(f"Invalid CORS origin format: {origin}")
            
    return valid_origins

def get_upload_config() -> Dict[str, Any]:
    """Get file upload configuration"""
    return {
        'max_size_mb': get_env_int('UPLOAD_MAX_SIZE_MB', 5000),
        'allowed_extensions': get_env_list('UPLOAD_ALLOWED_EXTENSIONS', 
            default=['.gguf', '.safetensors', '.mlx', '.mlmodel', '.pt', '.pth', '.bin', '.onnx', '.mlpackage']),
        'upload_directory': os.path.expanduser(get_env('UPLOAD_DIRECTORY', '~/Models'))
    }

def get_api_config() -> Dict[str, Any]:
    """Get API configuration"""
    return {
        'secret_key': get_env('SECRET_KEY', required=not get_env_bool('DEBUG', False)),
        'api_keys': get_env_list('OPENAI_API_KEYS'),
        'master_key': get_env('OPENAI_MASTER_KEY'),
        'enable_auth': get_env_bool('ENABLE_AUTH', True),
        'require_api_key': get_env_bool('REQUIRE_API_KEY', True),
        'enable_admin_endpoints': get_env_bool('ENABLE_ADMIN_ENDPOINTS', False)
    }

def get_rate_limit_config() -> Dict[str, Any]:
    """Get rate limiting configuration"""
    return {
        'enabled': get_env_bool('ENABLE_RATE_LIMIT', True),
        'default_limit': get_env('RATE_LIMIT_PER_MINUTE', '100/minute'),
        'premium_limit': get_env('RATE_LIMIT_PREMIUM_PER_MINUTE', '1000/minute')
    }

# Initialize environment on module import
load_env_file()