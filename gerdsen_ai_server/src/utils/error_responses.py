"""
User-friendly error responses with actionable suggestions
"""

from flask import jsonify
from typing import Dict, Optional, Any
from loguru import logger


class ErrorResponse:
    """Standardized error responses with helpful suggestions"""
    
    @staticmethod
    def model_not_found(model_id: str) -> tuple:
        """Model not found error with suggestions"""
        return jsonify({
            'error': 'Model not found',
            'message': f'Model "{model_id}" is not loaded or does not exist',
            'suggestions': [
                'Check available models with: GET /api/models/list',
                'Load the model with: POST /api/models/load',
                'Download from HuggingFace with: POST /api/models/download'
            ],
            'model_id': model_id
        }), 404
    
    @staticmethod
    def insufficient_memory(required_gb: float, available_gb: float) -> tuple:
        """Memory error with suggestions"""
        return jsonify({
            'error': 'Insufficient memory',
            'message': f'Need {required_gb:.1f}GB but only {available_gb:.1f}GB available',
            'suggestions': [
                'Try a smaller model (4-bit quantized versions)',
                'Unload other models with: POST /api/models/unload',
                'Close other applications to free memory',
                'Use IMPETUS_MAX_MEMORY_PERCENT to adjust limits'
            ],
            'required_gb': required_gb,
            'available_gb': available_gb
        }), 507
    
    @staticmethod
    def port_in_use(port: int) -> tuple:
        """Port conflict error with suggestions"""
        return jsonify({
            'error': 'Port already in use',
            'message': f'Port {port} is already being used by another process',
            'suggestions': [
                f'Check what\'s using port {port}: lsof -i :{port}',
                'Use a different port: IMPETUS_PORT=8081',
                'Stop the conflicting process',
                'Update port in .env file'
            ],
            'port': port
        }), 500
    
    @staticmethod
    def mlx_not_available() -> tuple:
        """MLX not available error"""
        return jsonify({
            'error': 'MLX not available',
            'message': 'MLX framework is not installed or not compatible',
            'suggestions': [
                'Install MLX: pip install mlx mlx-lm',
                'Verify Apple Silicon Mac: uname -m (should show arm64)',
                'Check Python version: python3 --version (need 3.11+)',
                'Run validation: impetus validate'
            ]
        }), 500
    
    @staticmethod
    def model_load_failed(model_id: str, error: str) -> tuple:
        """Model loading failed with specific error"""
        suggestions = [
            'Check if model exists in ~/.impetus/models/',
            'Verify model format is supported (MLX, GGUF)',
            'Check available disk space: df -h',
            'Review logs for detailed error'
        ]
        
        # Add specific suggestions based on error
        if 'memory' in error.lower():
            suggestions.insert(0, 'Try a smaller or more quantized model')
        elif 'permission' in error.lower():
            suggestions.insert(0, 'Check file permissions: ls -la ~/.impetus/models/')
        elif 'corrupt' in error.lower() or 'invalid' in error.lower():
            suggestions.insert(0, 'Re-download the model, files may be corrupted')
        
        return jsonify({
            'error': 'Model load failed',
            'message': f'Failed to load model "{model_id}": {error}',
            'suggestions': suggestions,
            'model_id': model_id,
            'details': error
        }), 500
    
    @staticmethod
    def download_failed(model_id: str, error: str) -> tuple:
        """Download failed with suggestions"""
        suggestions = [
            'Check internet connection',
            'Verify HuggingFace is accessible',
            'Check available disk space: df -h',
            'Try again later if HuggingFace is down'
        ]
        
        if 'space' in error.lower():
            suggestions.insert(0, 'Free up disk space - need at least 10GB')
        elif 'token' in error.lower() or 'auth' in error.lower():
            suggestions.insert(0, 'Some models require HF_TOKEN in .env')
        
        return jsonify({
            'error': 'Download failed',
            'message': f'Failed to download model "{model_id}": {error}',
            'suggestions': suggestions,
            'model_id': model_id,
            'details': error
        }), 500
    
    @staticmethod
    def invalid_request(field: str, expected: str) -> tuple:
        """Invalid request parameter"""
        return jsonify({
            'error': 'Invalid request',
            'message': f'Missing or invalid field: {field}',
            'suggestions': [
                f'Include "{field}" in request body',
                f'Expected format: {expected}',
                'Check API documentation for required fields'
            ],
            'field': field,
            'expected': expected
        }), 400
    
    @staticmethod
    def thermal_throttling() -> tuple:
        """Thermal throttling warning"""
        return jsonify({
            'error': 'Thermal throttling detected',
            'message': 'System is running hot and performance is reduced',
            'suggestions': [
                'Let system cool down for a few minutes',
                'Use efficiency mode: IMPETUS_PERFORMANCE_MODE=efficiency',
                'Reduce inference batch size',
                'Check Activity Monitor for high CPU processes',
                'Ensure good ventilation'
            ],
            'status': 'degraded_performance'
        }), 503
    
    @staticmethod
    def generic_error(error: Exception, context: str = "") -> tuple:
        """Generic error with context"""
        error_str = str(error)
        logger.error(f"Error in {context}: {error_str}")
        
        # Try to provide helpful suggestions based on error type
        suggestions = ['Check server logs for details']
        
        if 'timeout' in error_str.lower():
            suggestions.append('Increase timeout values in settings')
        elif 'connection' in error_str.lower():
            suggestions.append('Check if all services are running')
        
        return jsonify({
            'error': 'Internal server error',
            'message': f'An error occurred{f" in {context}" if context else ""}: {error_str}',
            'suggestions': suggestions,
            'context': context
        }), 500


def handle_error(error: Exception, context: str = "") -> tuple:
    """Main error handler that returns user-friendly responses"""
    error_str = str(error).lower()
    
    # Route to specific error handlers based on content
    if 'memory' in error_str or 'oom' in error_str:
        # Try to extract memory info
        import psutil
        mem = psutil.virtual_memory()
        return ErrorResponse.insufficient_memory(8.0, mem.available / (1024**3))
    
    elif 'mlx' in error_str and ('not found' in error_str or 'import' in error_str):
        return ErrorResponse.mlx_not_available()
    
    elif 'address already in use' in error_str or 'port' in error_str:
        # Extract port if possible
        import re
        port_match = re.search(r'(\d{4,5})', error_str)
        port = int(port_match.group(1)) if port_match else 8080
        return ErrorResponse.port_in_use(port)
    
    elif 'thermal' in error_str or 'throttl' in error_str:
        return ErrorResponse.thermal_throttling()
    
    else:
        return ErrorResponse.generic_error(error, context)