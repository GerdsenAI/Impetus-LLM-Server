#!/usr/bin/env python3
"""
File security utilities for safe file operations
"""

import os
import re
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

# Dangerous path patterns
DANGEROUS_PATTERNS = [
    r'\.\./',  # Parent directory traversal
    r'\.\.\\',  # Windows parent directory traversal
    r'^/',  # Absolute paths
    r'^\\',  # Windows absolute paths
    r'^~',  # Home directory expansion
    r'^\$',  # Environment variable expansion
    r'[<>:"|?*]',  # Invalid Windows characters
    r'\x00',  # Null bytes
]

# Compiled regex for efficiency
DANGEROUS_REGEX = re.compile('|'.join(DANGEROUS_PATTERNS))

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and other attacks
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename safe for filesystem use
    """
    if not filename:
        return "unnamed"
    
    # Remove any directory components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = DANGEROUS_REGEX.sub('', filename)
    
    # Replace spaces and special chars with underscores
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Ensure it doesn't start with a dot (hidden files)
    if filename.startswith('.'):
        filename = 'file_' + filename[1:]
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    filename = name + ext
    
    # Ensure we have a valid filename
    if not filename or filename == '.':
        filename = "unnamed"
        
    return filename

def is_safe_path(base_path: str, requested_path: str) -> bool:
    """
    Check if a requested path is safe (within base directory)
    
    Args:
        base_path: The base directory that should contain all files
        requested_path: The path being requested
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        # Resolve to absolute paths
        base = Path(base_path).resolve()
        requested = Path(requested_path).resolve()
        
        # Check if requested path is within base path
        return requested.parts[:len(base.parts)] == base.parts
    except Exception as e:
        logger.warning(f"Path safety check failed: {e}")
        return False

def validate_file_type(filename: str, allowed_extensions: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate file type based on extension and MIME type
    
    Args:
        filename: The filename to check
        allowed_extensions: List of allowed extensions (with dots, e.g., ['.txt', '.pdf'])
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "No filename provided"
    
    # Check extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        return False, f"File type '{ext}' not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    # Additional MIME type check
    mime_type, _ = mimetypes.guess_type(filename)
    
    # Map extensions to expected MIME types for additional validation
    mime_map = {
        '.gguf': 'application/octet-stream',
        '.safetensors': 'application/octet-stream',
        '.mlx': 'application/octet-stream',
        '.mlmodel': 'application/octet-stream',
        '.pt': 'application/octet-stream',
        '.pth': 'application/octet-stream',
        '.bin': 'application/octet-stream',
        '.onnx': 'application/octet-stream',
        '.mlpackage': 'application/octet-stream',
    }
    
    # For our ML model formats, we expect binary data
    expected_mime = mime_map.get(ext, 'application/octet-stream')
    
    # Don't reject based on MIME type for ML models (often detected as application/octet-stream)
    # But log for monitoring
    if mime_type and mime_type != expected_mime:
        logger.info(f"MIME type mismatch for {filename}: detected {mime_type}, expected {expected_mime}")
    
    return True, None

def generate_safe_path(base_dir: str, filename: str, create_dirs: bool = True) -> str:
    """
    Generate a safe file path within the base directory
    
    Args:
        base_dir: Base directory for files
        filename: Filename to use
        create_dirs: Whether to create directories if they don't exist
        
    Returns:
        Safe absolute path for the file
    """
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    # Determine subdirectory based on file extension
    ext = os.path.splitext(safe_filename)[1].lower()
    
    # Map extensions to directories
    dir_map = {
        '.gguf': 'GGUF',
        '.safetensors': 'SafeTensors',
        '.mlx': 'MLX',
        '.mlmodel': 'CoreML',
        '.mlpackage': 'CoreML',
        '.pt': 'PyTorch',
        '.pth': 'PyTorch',
        '.bin': 'Universal',
        '.onnx': 'ONNX',
    }
    
    format_dir = dir_map.get(ext, 'Universal')
    
    # Create full path
    base_path = Path(base_dir).expanduser().resolve()
    file_dir = base_path / format_dir / 'uploaded'
    
    # Create directories if needed
    if create_dirs:
        file_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename if file exists
    file_path = file_dir / safe_filename
    if file_path.exists():
        # Add timestamp hash to make unique
        timestamp_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        name, ext = os.path.splitext(safe_filename)
        safe_filename = f"{name}_{timestamp_hash}{ext}"
        file_path = file_dir / safe_filename
    
    # Final safety check
    if not is_safe_path(str(base_path), str(file_path)):
        raise ValueError(f"Generated path {file_path} is outside base directory")
    
    return str(file_path)

def get_file_info(file_path: str) -> dict:
    """
    Get safe file information
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {'error': 'File not found'}
            
        stat = path.stat()
        return {
            'name': path.name,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'extension': path.suffix.lower(),
            'exists': True
        }
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        return {'error': str(e)}

# Import time at the top of the file
import time