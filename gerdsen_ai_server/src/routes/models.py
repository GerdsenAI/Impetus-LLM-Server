#!/usr/bin/env python3
"""
Model Management API Routes
Provides model loading, optimization, and management endpoints
"""

from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
import os
import time
import threading
import logging
from typing import Dict, List, Any
from src.enhanced_mlx_manager import EnhancedMLXManager
from src.apple_silicon_detector import AppleSiliconDetector

models_bp = Blueprint('models', __name__)

# Global instances
mlx_manager = None
detector = None
model_operations_lock = threading.Lock()

def initialize_managers():
    """Initialize the MLX manager and detector"""
    global mlx_manager, detector
    if mlx_manager is None:
        mlx_manager = EnhancedMLXManager()
        detector = AppleSiliconDetector()
        logging.info("Model managers initialized")

# Initialize on module load
initialize_managers()

@models_bp.route('/list', methods=['GET'])
def list_models():
    """List all loaded and cached models"""
    try:
        if not mlx_manager:
            return jsonify({'error': 'MLX manager not available'}), 500
        
        # Get loaded models
        loaded_models = []
        for model_id, model_data in mlx_manager.loaded_models.items():
            model_info = mlx_manager.get_model_info(model_id)
            loaded_models.append({
                'id': model_id,
                'status': 'loaded',
                'info': model_info
            })
        
        # Get cached models
        cached_models = []
        for model_id, metadata in mlx_manager.persistence_manager.cached_models.items():
            if model_id not in mlx_manager.loaded_models:
                cached_models.append({
                    'id': model_id,
                    'status': 'cached',
                    'metadata': {
                        'name': metadata.name,
                        'size_bytes': metadata.size_bytes,
                        'last_accessed': metadata.last_accessed,
                        'access_count': metadata.access_count,
                        'quantization': metadata.quantization
                    }
                })
        
        return jsonify({
            'success': True,
            'data': {
                'loaded_models': loaded_models,
                'cached_models': cached_models,
                'total_loaded': len(loaded_models),
                'total_cached': len(cached_models)
            },
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error listing models: {e}")
        return jsonify({'error': str(e)}), 500

@models_bp.route('/load', methods=['POST'])
def load_model():
    """Load a model with optimizations"""
    try:
        if not mlx_manager:
            return jsonify({'error': 'MLX manager not available'}), 500
        
        data = request.get_json()
        if not data or 'path' not in data:
            return jsonify({'error': 'Model path is required'}), 400
        
        model_path = data['path']
        model_id = data.get('model_id')
        
        # Validate model path
        if not os.path.exists(model_path):
            return jsonify({'error': 'Model file not found'}), 404
        
        with model_operations_lock:
            # Load model with optimizations
            start_time = time.time()
            model_id = mlx_manager.load_model_optimized(model_path, model_id)
            load_time = time.time() - start_time
            
            # Get model information
            model_info = mlx_manager.get_model_info(model_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'model_id': model_id,
                    'load_time': load_time,
                    'model_info': model_info
                },
                'timestamp': time.time()
            })
    
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        return jsonify({'error': str(e)}), 500

@models_bp.route('/unload/<model_id>', methods=['POST'])
def unload_model(model_id):
    """Unload a model from memory"""
    try:
        if not mlx_manager:
            return jsonify({'error': 'MLX manager not available'}), 500
        
        if model_id not in mlx_manager.loaded_models:
            return jsonify({'error': 'Model not loaded'}), 404
        
        with model_operations_lock:
            mlx_manager.unload_model(model_id)
            
            return jsonify({
                'success': True,
                'message': f'Model {model_id} unloaded successfully',
                'timestamp': time.time()
            })
    
    except Exception as e:
        logging.error(f"Error unloading model: {e}")
        return jsonify({'error': str(e)}), 500

@models_bp.route('/info/<model_id>', methods=['GET'])
def get_model_info(model_id):
    """Get detailed information about a specific model"""
    try:
        if not mlx_manager:
            return jsonify({'error': 'MLX manager not available'}), 500
        
        model_info = mlx_manager.get_model_info(model_id)
        if not model_info:
            return jsonify({'error': 'Model not found'}), 404
        
        return jsonify({
            'success': True,
            'data': model_info,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting model info: {e}")
        return jsonify({'error': str(e)}), 500

@models_bp.route('/upload', methods=['POST'])
def upload_model():
    """Upload a model file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file extension
        allowed_extensions = {'.mlx', '.gguf', '.safetensors', '.bin', '.pt', '.pth'}
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Unsupported file type: {file_ext}'}), 400
        
        # Create uploads directory
        upload_dir = os.path.join(current_app.instance_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'data': {
                'filename': filename,
                'path': file_path,
                'size_bytes': os.path.getsize(file_path)
            },
            'message': 'File uploaded successfully',
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error uploading model: {e}")
        return jsonify({'error': str(e)}), 500

@models_bp.route('/optimize/<model_id>', methods=['POST'])
def optimize_model(model_id):
    """Apply additional optimizations to a loaded model"""
    try:
        if not mlx_manager:
            return jsonify({'error': 'MLX manager not available'}), 500
        
        if model_id not in mlx_manager.loaded_models:
            return jsonify({'error': 'Model not loaded'}), 404
        
        data = request.get_json() or {}
        optimization_options = data.get('options', {})
        
        with model_operations_lock:
            # Get current model configuration
            model_data = mlx_manager.loaded_models[model_id]
            current_config = model_data.get('config', {})
            
            # Apply additional optimizations
            optimized_config = mlx_manager.performance_optimizer.optimize_model(current_config)
            
            # Update model configuration
            model_data['config'] = optimized_config
            
            # Benchmark performance after optimization
            metrics = mlx_manager.performance_optimizer.benchmark_performance(model_id)
            model_data['metrics'] = metrics
            
            return jsonify({
                'success': True,
                'data': {
                    'model_id': model_id,
                    'optimizations_applied': list(optimized_config.keys()),
                    'performance_metrics': {
                        'load_time': metrics.load_time,
                        'tokens_per_second': metrics.tokens_per_second,
                        'memory_usage': metrics.memory_usage,
                        'gpu_utilization': metrics.gpu_utilization
                    }
                },
                'message': 'Model optimized successfully',
                'timestamp': time.time()
            })
    
    except Exception as e:
        logging.error(f"Error optimizing model: {e}")
        return jsonify({'error': str(e)}), 500

@models_bp.route('/performance/<model_id>', methods=['GET'])
def get_model_performance(model_id):
    """Get performance metrics for a specific model"""
    try:
        if not mlx_manager:
            return jsonify({'error': 'MLX manager not available'}), 500
        
        if model_id not in mlx_manager.loaded_models:
            return jsonify({'error': 'Model not loaded'}), 404
        
        model_data = mlx_manager.loaded_models[model_id]
        metrics = model_data.get('metrics')
        
        if not metrics:
            # Benchmark the model if no metrics available
            metrics = mlx_manager.performance_optimizer.benchmark_performance(model_id)
            model_data['metrics'] = metrics
        
        return jsonify({
            'success': True,
            'data': {
                'model_id': model_id,
                'performance_metrics': {
                    'load_time': metrics.load_time,
                    'first_token_latency': metrics.first_token_latency,
                    'tokens_per_second': metrics.tokens_per_second,
                    'memory_usage': metrics.memory_usage,
                    'gpu_utilization': metrics.gpu_utilization,
                    'temperature': metrics.temperature,
                    'power_consumption': metrics.power_consumption
                },
                'benchmark_timestamp': time.time()
            },
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting model performance: {e}")
        return jsonify({'error': str(e)}), 500

@models_bp.route('/cache/status', methods=['GET'])
def get_cache_status():
    """Get model cache status and statistics"""
    try:
        if not mlx_manager:
            return jsonify({'error': 'MLX manager not available'}), 500
        
        cache_manager = mlx_manager.persistence_manager
        
        # Calculate cache statistics
        total_models = len(cache_manager.cached_models)
        total_size_bytes = sum(metadata.size_bytes for metadata in cache_manager.cached_models.values())
        total_size_gb = total_size_bytes / (1024**3)
        
        # Get most accessed models
        most_accessed = sorted(
            cache_manager.cached_models.items(),
            key=lambda x: x[1].access_count,
            reverse=True
        )[:5]
        
        return jsonify({
            'success': True,
            'data': {
                'total_cached_models': total_models,
                'total_cache_size_bytes': total_size_bytes,
                'total_cache_size_gb': round(total_size_gb, 2),
                'cache_directory': str(cache_manager.cache_dir),
                'most_accessed_models': [
                    {
                        'model_id': model_id,
                        'name': metadata.name,
                        'access_count': metadata.access_count,
                        'last_accessed': metadata.last_accessed,
                        'size_gb': round(metadata.size_bytes / (1024**3), 2)
                    }
                    for model_id, metadata in most_accessed
                ]
            },
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting cache status: {e}")
        return jsonify({'error': str(e)}), 500

@models_bp.route('/cache/cleanup', methods=['POST'])
def cleanup_cache():
    """Clean up model cache based on size and access patterns"""
    try:
        if not mlx_manager:
            return jsonify({'error': 'MLX manager not available'}), 500
        
        data = request.get_json() or {}
        max_size_gb = data.get('max_size_gb', 100.0)
        
        cache_manager = mlx_manager.persistence_manager
        
        # Get cache size before cleanup
        size_before = sum(metadata.size_bytes for metadata in cache_manager.cached_models.values())
        models_before = len(cache_manager.cached_models)
        
        # Perform cleanup
        cache_manager.cleanup_cache(max_size_gb)
        
        # Get cache size after cleanup
        size_after = sum(metadata.size_bytes for metadata in cache_manager.cached_models.values())
        models_after = len(cache_manager.cached_models)
        
        return jsonify({
            'success': True,
            'data': {
                'models_removed': models_before - models_after,
                'space_freed_gb': round((size_before - size_after) / (1024**3), 2),
                'cache_size_before_gb': round(size_before / (1024**3), 2),
                'cache_size_after_gb': round(size_after / (1024**3), 2),
                'remaining_models': models_after
            },
            'message': 'Cache cleanup completed',
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error cleaning up cache: {e}")
        return jsonify({'error': str(e)}), 500

@models_bp.route('/system-status', methods=['GET'])
def get_system_status():
    """Get overall system status for model management"""
    try:
        if not mlx_manager:
            return jsonify({'error': 'MLX manager not available'}), 500
        
        system_status = mlx_manager.get_system_status()
        
        return jsonify({
            'success': True,
            'data': system_status,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500

