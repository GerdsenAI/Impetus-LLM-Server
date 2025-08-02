"""
Model management endpoints
"""

from flask import Blueprint, jsonify, request, current_app
from pathlib import Path
from loguru import logger
from typing import Dict, List
from ..config.settings import settings
from ..services.model_discovery import ModelDiscoveryService, ModelCategory
from ..services.download_manager import download_manager

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
    auto_load = data.get('auto_load', False)
    
    if not model_id:
        return jsonify({'error': 'model_id is required'}), 400
    
    # Import services
    from ..services.download_manager import download_manager
    from ..services.model_discovery import ModelDiscoveryService
    
    # Get model info
    discovery = ModelDiscoveryService()
    model_info = discovery.get_model_info(model_id)
    
    if not model_info:
        # Try to estimate size for unknown models
        estimated_size = download_manager.get_download_size(model_id) or 5.0
    else:
        estimated_size = model_info.size_gb
    
    # Check disk space
    has_space, available_gb = download_manager.check_disk_space(estimated_size)
    if not has_space:
        return jsonify({
            'error': 'Insufficient disk space',
            'message': f'Need {estimated_size:.1f}GB but only {available_gb:.1f}GB available'
        }), 507
    
    # Create download task
    task_id = download_manager.create_download_task(model_id)
    
    # Start download in background
    import asyncio
    from threading import Thread
    
    def download_in_background():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create progress callback for WebSocket updates
        def progress_callback(progress):
            app_state = current_app.config.get('app_state', {})
            socketio = app_state.get('socketio')
            if socketio:
                socketio.emit('download_progress', {
                    'task_id': progress.task_id,
                    'downloaded_gb': progress.downloaded_bytes / (1024 ** 3),
                    'total_gb': progress.total_bytes / (1024 ** 3),
                    'speed_mbps': progress.speed_mbps,
                    'eta_seconds': progress.eta_seconds,
                    'progress': progress.downloaded_bytes / progress.total_bytes if progress.total_bytes > 0 else 0
                }, room=f'download_{task_id}')
        
        # Register callback
        download_manager.register_progress_callback(task_id, progress_callback)
        
        async def do_download():
            success = await download_manager.download_model(task_id)
            
            # Send completion event
            app_state = current_app.config.get('app_state', {})
            socketio = app_state.get('socketio')
            if socketio:
                task = download_manager.get_task_status(task_id)
                socketio.emit('download_complete', {
                    'task_id': task_id,
                    'model_id': model_id,
                    'success': success,
                    'status': task.status.value if task else 'unknown'
                }, room=f'download_{task_id}')
            
            if success and auto_load:
                # TODO: Auto-load the model after download
                logger.info(f"Model {model_id} downloaded, auto-load requested")
        
        loop.run_until_complete(do_download())
    
    thread = Thread(target=download_in_background, daemon=True)
    thread.start()
    
    return jsonify({
        'status': 'started',
        'task_id': task_id,
        'model_id': model_id,
        'estimated_size_gb': estimated_size
    })


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


@bp.route('/discover', methods=['GET'])
def discover_models():
    """Discover available models from curated list"""
    discovery = ModelDiscoveryService()
    
    # Get query parameters
    category = request.args.get('category')
    search = request.args.get('search')
    available_memory = request.args.get('available_memory', type=float)
    use_case = request.args.get('use_case')
    
    # Get models based on filters
    if search:
        models = discovery.search_models(search)
    elif category:
        try:
            cat = ModelCategory(category)
            models = discovery.get_models_by_category(cat)
        except ValueError:
            return jsonify({'error': f'Invalid category: {category}'}), 400
    elif available_memory and use_case:
        models = discovery.get_recommended_models(available_memory, use_case)
    else:
        models = discovery.get_all_models()
    
    # Get current hardware info for performance estimates
    app_state = current_app.config.get('app_state', {})
    hardware_info = app_state.get('hardware_info', {})
    chip_type = hardware_info.get('chip_type', 'M1')
    
    # Convert to JSON-serializable format
    results = []
    for model in models:
        estimated_performance = discovery.estimate_performance(model.id, chip_type)
        results.append({
            'id': model.id,
            'name': model.name,
            'category': model.category.value,
            'size_gb': model.size_gb,
            'quantization': model.quantization,
            'context_length': model.context_length,
            'description': model.description,
            'features': model.features,
            'recommended_for': model.recommended_for,
            'min_memory_gb': model.min_memory_gb,
            'popularity_score': model.popularity_score,
            'estimated_tokens_per_sec': estimated_performance
        })
    
    return jsonify({
        'models': results,
        'total': len(results),
        'hardware': chip_type
    })


@bp.route('/recommended', methods=['GET'])
def get_recommended_models():
    """Get recommended models based on system capabilities"""
    import psutil
    
    discovery = ModelDiscoveryService()
    
    # Get available memory
    memory = psutil.virtual_memory()
    available_gb = memory.available / (1024 ** 3)
    
    # Get use case from query
    use_case = request.args.get('use_case', 'general-qa')
    
    # Get recommendations
    models = discovery.get_recommended_models(available_gb, use_case)
    
    # Get hardware info
    app_state = current_app.config.get('app_state', {})
    hardware_info = app_state.get('hardware_info', {})
    chip_type = hardware_info.get('chip_type', 'M1')
    
    # Format results
    results = []
    for model in models:
        estimated_performance = discovery.estimate_performance(model.id, chip_type)
        results.append({
            'id': model.id,
            'name': model.name,
            'category': model.category.value,
            'size_gb': model.size_gb,
            'quantization': model.quantization,
            'description': model.description,
            'estimated_tokens_per_sec': estimated_performance,
            'reason': f"Fits in {available_gb:.1f}GB available memory"
        })
    
    return jsonify({
        'recommendations': results,
        'system': {
            'available_memory_gb': available_gb,
            'chip_type': chip_type,
            'use_case': use_case
        }
    })


@bp.route('/download/<task_id>', methods=['GET'])
def get_download_status(task_id: str):
    """Get status of a download task"""
    task = download_manager.get_task_status(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({
        'task_id': task.task_id,
        'model_id': task.model_id,
        'status': task.status.value,
        'progress': task.progress,
        'downloaded_gb': task.downloaded_bytes / (1024 ** 3) if task.downloaded_bytes else 0,
        'total_gb': task.total_bytes / (1024 ** 3) if task.total_bytes else 0,
        'speed_mbps': task.speed_mbps,
        'eta_seconds': task.eta_seconds,
        'error': task.error,
        'started_at': task.started_at.isoformat() if task.started_at else None,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None
    })


@bp.route('/download/<task_id>', methods=['DELETE'])
def cancel_download(task_id: str):
    """Cancel a download task"""
    success = download_manager.cancel_download(task_id)
    
    if not success:
        return jsonify({'error': 'Cannot cancel task'}), 400
    
    return jsonify({
        'status': 'cancelled',
        'task_id': task_id
    })


@bp.route('/downloads', methods=['GET'])
def list_downloads():
    """List all download tasks"""
    tasks = download_manager.get_all_tasks()
    
    results = []
    for task in tasks.values():
        results.append({
            'task_id': task.task_id,
            'model_id': task.model_id,
            'status': task.status.value,
            'progress': task.progress,
            'started_at': task.started_at.isoformat() if task.started_at else None
        })
    
    return jsonify({
        'downloads': results,
        'total': len(results)
    })