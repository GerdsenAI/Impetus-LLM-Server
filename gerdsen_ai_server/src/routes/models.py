"""
Model management endpoints
"""

from flask import Blueprint, jsonify, request, current_app
from pathlib import Path
from loguru import logger
from typing import Dict, List
from ..config.settings import settings

bp = Blueprint('models', __name__)


def get_available_models() -> List[Dict]:
    """Get list of available models from the models directory"""
    models = []
    models_dir = settings.model.models_dir
    
    if models_dir.exists():
        # Look for model directories
        for model_path in models_dir.iterdir():
            if model_path.is_dir():
                # Check for common model files
                model_info = {
                    'id': model_path.name,
                    'name': model_path.name,
                    'path': str(model_path),
                    'size_gb': 0,
                    'format': 'unknown',
                    'loaded': False
                }
                
                # Check for MLX format
                if (model_path / 'config.json').exists():
                    model_info['format'] = 'mlx'
                    # Calculate total size
                    total_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
                    model_info['size_gb'] = total_size / (1024 ** 3)
                
                # Check for GGUF format
                gguf_files = list(model_path.glob('*.gguf'))
                if gguf_files:
                    model_info['format'] = 'gguf'
                    model_info['size_gb'] = gguf_files[0].stat().st_size / (1024 ** 3)
                
                models.append(model_info)
    
    # Add loaded models
    app_state = current_app.config.get('app_state', {})
    loaded_models = app_state.get('loaded_models', {})
    
    for model_id in loaded_models:
        # Mark as loaded if already in list
        for model in models:
            if model['id'] == model_id:
                model['loaded'] = True
                break
        else:
            # Add if not in list (e.g., downloaded from hub)
            models.append({
                'id': model_id,
                'name': model_id,
                'path': 'hub',
                'size_gb': 0,
                'format': 'mlx',
                'loaded': True
            })
    
    return models


@bp.route('/list', methods=['GET'])
def list_models():
    """List all available models"""
    try:
        models = get_available_models()
        return jsonify({
            'models': models,
            'models_directory': str(settings.model.models_dir)
        })
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return jsonify({'error': 'Failed to list models'}), 500


@bp.route('/load', methods=['POST'])
def load_model():
    """Load a model into memory"""
    data = request.get_json()
    model_id = data.get('model_id')
    
    if not model_id:
        return jsonify({'error': 'model_id is required'}), 400
    
    app_state = current_app.config.get('app_state', {})
    loaded_models = app_state.get('loaded_models', {})
    
    # Check if already loaded
    if model_id in loaded_models:
        return jsonify({
            'status': 'already_loaded',
            'model_id': model_id,
            'message': 'Model is already loaded'
        })
    
    # Check memory before loading
    import psutil
    memory = psutil.virtual_memory()
    if memory.percent > settings.hardware.max_memory_percent:
        return jsonify({
            'error': 'Insufficient memory',
            'message': f'Memory usage ({memory.percent}%) exceeds limit ({settings.hardware.max_memory_percent}%)'
        }), 507
    
    # Check if we need to unload models
    if len(loaded_models) >= settings.model.max_loaded_models:
        # Unload least recently used model
        # For now, just return error
        return jsonify({
            'error': 'Model limit reached',
            'message': f'Maximum {settings.model.max_loaded_models} models can be loaded simultaneously'
        }), 507
    
    try:
        # Import model loader
        from ..model_loaders.mlx_loader import MLXModelLoader
        
        # Create loader and load model
        loader = MLXModelLoader()
        model = loader.load_model(model_id)
        
        # Store in app state
        loaded_models[model_id] = model
        
        logger.info(f"Successfully loaded model: {model_id}")
        
        return jsonify({
            'status': 'success',
            'model_id': model_id,
            'message': 'Model loaded successfully',
            'memory_used_gb': psutil.virtual_memory().used / (1024 ** 3)
        })
        
    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {e}")
        return jsonify({
            'error': 'Failed to load model',
            'message': str(e)
        }), 500


@bp.route('/unload', methods=['POST'])
def unload_model():
    """Unload a model from memory"""
    data = request.get_json()
    model_id = data.get('model_id')
    
    if not model_id:
        return jsonify({'error': 'model_id is required'}), 400
    
    app_state = current_app.config.get('app_state', {})
    loaded_models = app_state.get('loaded_models', {})
    
    if model_id not in loaded_models:
        return jsonify({
            'error': 'Model not loaded',
            'message': f'Model {model_id} is not currently loaded'
        }), 404
    
    try:
        # Remove from loaded models
        model = loaded_models.pop(model_id)
        
        # Clean up model resources
        if hasattr(model, 'unload'):
            model.unload()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        logger.info(f"Successfully unloaded model: {model_id}")
        
        return jsonify({
            'status': 'success',
            'model_id': model_id,
            'message': 'Model unloaded successfully',
            'memory_freed_gb': psutil.virtual_memory().available / (1024 ** 3)
        })
        
    except Exception as e:
        logger.error(f"Failed to unload model {model_id}: {e}")
        return jsonify({
            'error': 'Failed to unload model',
            'message': str(e)
        }), 500


@bp.route('/download', methods=['POST'])
def download_model():
    """Download a model from HuggingFace Hub"""
    data = request.get_json()
    model_id = data.get('model_id')
    
    if not model_id:
        return jsonify({'error': 'model_id is required'}), 400
    
    # TODO: Implement model downloading
    # This would use HuggingFace Hub API to download models
    
    return jsonify({
        'error': 'Not implemented',
        'message': 'Model downloading will be implemented in the next phase'
    }), 501


@bp.route('/optimize', methods=['POST'])
def optimize_model():
    """Optimize a model for Apple Silicon"""
    data = request.get_json()
    model_id = data.get('model_id')
    optimization_type = data.get('type', 'quantize')  # quantize, compile, etc.
    
    if not model_id:
        return jsonify({'error': 'model_id is required'}), 400
    
    # TODO: Implement model optimization
    # This would use MLX optimization techniques
    
    return jsonify({
        'error': 'Not implemented',
        'message': 'Model optimization will be implemented in the next phase'
    }), 501