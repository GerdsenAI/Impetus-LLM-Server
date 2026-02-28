"""
Model management endpoints
"""

from pathlib import Path

import psutil
from flask import Blueprint, current_app, jsonify, request
from loguru import logger

from ..config.settings import settings
from ..inference.kv_cache_manager import kv_cache_manager
from ..services.benchmark_service import benchmark_service
from ..services.download_manager import download_manager
from ..services.model_discovery import ModelCategory, ModelDiscoveryService
from ..services.model_warmup import model_warmup_service
from ..utils.error_recovery import ErrorType, with_error_recovery
from ..utils.error_responses import ErrorResponse, handle_error
from ..utils.mmap_loader import mmap_loader

bp = Blueprint('models', __name__)


@with_error_recovery(ErrorType.MODEL_LOAD_FAILURE, max_retries=2)
def _load_model_internal(model_id: str, app_state: dict) -> dict:
    """Internal function to load a model. Returns result dict with status/error."""
    loaded_models = app_state.get('loaded_models', {})

    # Check if already loaded
    if model_id in loaded_models:
        return {
            'status': 'already_loaded',
            'model_id': model_id,
            'message': 'Model is already loaded'
        }

    # Check memory before loading
    import psutil
    memory = psutil.virtual_memory()
    if memory.percent > settings.hardware.max_memory_percent:
        available_gb = memory.available / (1024 ** 3)
        # Estimate required memory (rough estimate)
        required_gb = 8.0  # Default estimate for 7B model
        return ErrorResponse.insufficient_memory(required_gb, available_gb)[1]

    # Check if we need to unload models
    if len(loaded_models) >= settings.model.max_loaded_models:
        return {
            'error': 'Model limit reached',
            'message': f'Maximum {settings.model.max_loaded_models} models can be loaded simultaneously',
            'status_code': 507
        }

    try:
        # Import model loader
        from ..model_loaders.mlx_loader import MLXModelLoader

        # Create loader and load model
        loader = MLXModelLoader()
        model = loader.load_model(model_id)

        # Store in app state
        loaded_models[model_id] = model

        logger.info(f"Successfully loaded model: {model_id}")

        return {
            'status': 'success',
            'model_id': model_id,
            'message': 'Model loaded successfully',
            'memory_used_gb': psutil.virtual_memory().used / (1024 ** 3)
        }

    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {e}")
        error_resp = ErrorResponse.model_load_failed(model_id, str(e))
        return {
            'error': error_resp[0].json['error'],
            'message': error_resp[0].json['message'],
            'status_code': error_resp[1]
        }


def get_available_models() -> list[dict]:
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

        # Add benchmark info if available
        app_state = current_app.config.get('app_state', {})
        model_benchmarks = app_state.get('model_benchmarks', {})

        for model in models:
            model_id = model['id']
            if model_id in model_benchmarks:
                model['benchmark'] = {
                    'available': True,
                    'latest': model_benchmarks[model_id]['latest'],
                    'tokens_per_second': model_benchmarks[model_id]['average_tokens_per_second']
                }
            else:
                model['benchmark'] = {'available': False}

            # Add warmup status
            warmup_status = model_warmup_service.get_warmup_status(model_id)
            if warmup_status:
                model['warmup'] = {
                    'is_warmed': warmup_status.is_warmed,
                    'warmup_time_ms': warmup_status.warmup_time_ms,
                    'kernel_compilation_time_ms': warmup_status.kernel_compilation_time_ms
                }
            else:
                model['warmup'] = {'is_warmed': False}

        return jsonify({
            'models': models,
            'models_directory': str(settings.model.models_dir)
        })
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return handle_error(e, "listing models")


@bp.route('/load', methods=['POST'])
def load_model():
    """Load a model into memory with optional warmup and memory mapping"""
    data = request.get_json()
    model_id = data.get('model_id')
    auto_warmup = data.get('auto_warmup', False)
    use_mmap = data.get('use_mmap', True)

    if not model_id:
        return jsonify({'error': 'model_id is required'}), 400

    app_state = current_app.config.get('app_state', {})

    # Pass auto_warmup to the loader
    if auto_warmup:
        # Import model loader
        from ..model_loaders.mlx_loader import MLXModelLoader
        loader = MLXModelLoader()

        try:
            # Load with auto warmup and optional mmap
            model = loader.load_model(
                model_id,
                auto_warmup=True,
                warmup_async=True,
                use_mmap=use_mmap
            )
            app_state['loaded_models'][model_id] = model

            # Get warmup status
            warmup_status = model_warmup_service.get_warmup_status(model_id)

            return jsonify({
                'status': 'success',
                'model_id': model_id,
                'message': 'Model loaded and warming up' if auto_warmup else 'Model loaded successfully',
                'memory_used_gb': psutil.virtual_memory().used / (1024 ** 3),
                'warmup': {
                    'is_warmed': warmup_status.is_warmed if warmup_status else False,
                    'status': 'warming' if auto_warmup and warmup_status and not warmup_status.is_warmed else 'not_started'
                }
            })
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return jsonify({
                'error': 'Failed to load model',
                'message': str(e)
            }), 500
    else:
        # Regular load without warmup
        result = _load_model_internal(model_id, app_state)

        # Return appropriate response based on result
        if 'error' in result:
            status_code = result.get('status_code', 500)
            return jsonify({
                'error': result['error'],
                'message': result['message']
            }), status_code
        else:
            return jsonify(result)


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

    estimated_size = download_manager.get_download_size(model_id) or 5.0 if not model_info else model_info.size_gb

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

        # Store the app for context
        app = current_app._get_current_object()

        # Create progress callback for WebSocket updates
        def progress_callback(progress):
            with app.app_context():
                app_state = app.config.get('app_state', {})
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
            with app.app_context():
                app_state = app.config.get('app_state', {})
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
                    logger.info(f"Model {model_id} downloaded, starting auto-load")

                    # Emit auto-load started event
                    if socketio:
                        socketio.emit('auto_load_started', {
                            'model_id': model_id,
                            'message': 'Starting automatic model loading'
                        }, room=f'download_{task_id}')

                    # Attempt to load the model
                    load_result = _load_model_internal(model_id, app_state)

                    if 'error' in load_result:
                        # Auto-load failed
                        logger.error(f"Auto-load failed for {model_id}: {load_result['message']}")
                        if socketio:
                            socketio.emit('auto_load_failed', {
                                'model_id': model_id,
                                'error': load_result['error'],
                                'message': load_result['message']
                            }, room=f'download_{task_id}')
                    else:
                        # Auto-load succeeded
                        logger.info(f"Auto-load successful for {model_id}")
                        if socketio:
                            socketio.emit('auto_load_complete', {
                                'model_id': model_id,
                                'status': load_result['status'],
                                'message': load_result['message'],
                                'memory_used_gb': load_result.get('memory_used_gb', 0)
                            }, room=f'download_{task_id}')

                            # Also emit models update to all clients
                            loaded_models = list(app_state.get('loaded_models', {}).keys())
                            socketio.emit('models_update', {
                                'loaded_models': loaded_models
                            }, room='models')

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
    data.get('type', 'quantize')  # quantize, compile, etc.

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


@bp.route('/benchmark/<model_id>', methods=['POST'])
def benchmark_model(model_id: str):
    """Run performance benchmark on a loaded model"""
    app_state = current_app.config.get('app_state', {})
    loaded_models = app_state.get('loaded_models', {})

    # Check if model is loaded
    if model_id not in loaded_models:
        return jsonify({
            'error': 'Model not loaded',
            'message': f'Model {model_id} must be loaded before benchmarking'
        }), 404

    # Get hardware info
    hardware_info = app_state.get('hardware_info', {})
    chip_type = hardware_info.get('chip_type', 'Unknown')

    # Get custom prompts if provided
    data = request.get_json() or {}
    custom_prompts = data.get('prompts')

    try:
        # Run benchmark
        model = loaded_models[model_id]
        suite = benchmark_service.benchmark_model(
            model=model,
            model_id=model_id,
            chip_type=chip_type,
            custom_prompts=custom_prompts
        )

        # Update model info with benchmark results
        if 'model_benchmarks' not in app_state:
            app_state['model_benchmarks'] = {}

        app_state['model_benchmarks'][model_id] = {
            'latest': suite.timestamp,
            'average_tokens_per_second': suite.average_tokens_per_second,
            'average_first_token_latency_ms': suite.average_first_token_latency_ms,
            'peak_tokens_per_second': suite.peak_tokens_per_second
        }

        return jsonify({
            'status': 'success',
            'model_id': model_id,
            'chip_type': chip_type,
            'timestamp': suite.timestamp,
            'summary': {
                'average_tokens_per_second': round(suite.average_tokens_per_second, 1),
                'average_first_token_latency_ms': round(suite.average_first_token_latency_ms, 1),
                'peak_tokens_per_second': round(suite.peak_tokens_per_second, 1),
                'average_memory_gb': round(suite.average_memory_gb, 2)
            },
            'results': [
                {
                    'prompt_length': r.prompt_length,
                    'output_tokens': r.output_tokens,
                    'tokens_per_second': round(r.tokens_per_second, 1),
                    'time_to_first_token_ms': round(r.time_to_first_token_ms, 1),
                    'total_time_ms': round(r.total_time_ms, 1),
                    'gpu_utilization': round(r.gpu_utilization_avg, 1)
                }
                for r in suite.results
            ]
        })

    except Exception as e:
        logger.error(f"Benchmark failed for {model_id}: {e}")
        return jsonify({
            'error': 'Benchmark failed',
            'message': str(e)
        }), 500


@bp.route('/benchmark/<model_id>/history', methods=['GET'])
def get_benchmark_history(model_id: str):
    """Get benchmark history for a model"""
    limit = request.args.get('limit', 10, type=int)

    try:
        history = benchmark_service.get_model_history(model_id, limit=limit)

        return jsonify({
            'model_id': model_id,
            'history': [
                {
                    'timestamp': suite.timestamp,
                    'chip_type': suite.chip_type,
                    'average_tokens_per_second': round(suite.average_tokens_per_second, 1),
                    'average_first_token_latency_ms': round(suite.average_first_token_latency_ms, 1),
                    'peak_tokens_per_second': round(suite.peak_tokens_per_second, 1),
                    'run_count': len(suite.results)
                }
                for suite in history
            ]
        })

    except Exception as e:
        logger.error(f"Failed to get benchmark history: {e}")
        return jsonify({'error': 'Failed to retrieve history'}), 500


@bp.route('/benchmarks/comparison', methods=['GET'])
def get_benchmark_comparison():
    """Get benchmark comparison across all models and chips"""
    try:
        summary = benchmark_service.get_all_models_summary()

        # Group by model
        models = {}
        for row in summary:
            model_id = row['model_id']
            if model_id not in models:
                models[model_id] = {
                    'model_id': model_id,
                    'chips': {}
                }

            models[model_id]['chips'][row['chip_type']] = {
                'average_tokens_per_second': round(row['avg_tps'], 1),
                'average_first_token_latency_ms': round(row['avg_ttft'], 1),
                'average_memory_gb': round(row['avg_memory'], 2),
                'latest_run': row['latest_run'],
                'total_runs': row['total_runs']
            }

        return jsonify({
            'models': list(models.values()),
            'total_models': len(models)
        })

    except Exception as e:
        logger.error(f"Failed to get benchmark comparison: {e}")
        return jsonify({'error': 'Failed to retrieve comparison'}), 500


@bp.route('/cache/status', methods=['GET'])
def get_cache_status():
    """Get KV cache status and statistics"""
    stats = kv_cache_manager.get_stats()
    return jsonify(stats)


@bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear KV cache for specific conversation or all"""
    data = request.get_json() or {}
    model_id = data.get('model_id')
    conversation_id = data.get('conversation_id')

    if model_id and conversation_id:
        # Clear specific conversation cache
        success = kv_cache_manager.clear_cache(model_id, conversation_id)
        return jsonify({
            'status': 'success' if success else 'not_found',
            'model_id': model_id,
            'conversation_id': conversation_id,
            'message': f'Cache {"cleared" if success else "not found"}'
        })
    elif model_id:
        # Clear all caches for model
        cleared = kv_cache_manager.clear_model_caches(model_id)
        return jsonify({
            'status': 'success',
            'model_id': model_id,
            'caches_cleared': cleared,
            'message': f'Cleared {cleared} caches for model'
        })
    else:
        # Clear all caches
        kv_cache_manager.clear_all_caches()
        return jsonify({
            'status': 'success',
            'message': 'All caches cleared'
        })


@bp.route('/cache/settings', methods=['GET', 'PUT'])
def cache_settings():
    """Get or update KV cache settings"""
    if request.method == 'GET':
        return jsonify({
            'enabled': kv_cache_manager.enabled,
            'max_memory_gb': kv_cache_manager.max_memory_mb / 1024,
            'max_conversations': kv_cache_manager.max_conversations,
            'current_memory_mb': kv_cache_manager.total_memory_mb,
            'num_active_caches': len(kv_cache_manager.caches)
        })
    else:
        # Update settings
        data = request.get_json()

        if 'max_memory_gb' in data:
            kv_cache_manager.max_memory_mb = data['max_memory_gb'] * 1024

        if 'max_conversations' in data:
            kv_cache_manager.max_conversations = data['max_conversations']

        return jsonify({
            'status': 'updated',
            'max_memory_gb': kv_cache_manager.max_memory_mb / 1024,
            'max_conversations': kv_cache_manager.max_conversations
        })


@bp.route('/warmup/<model_id>', methods=['POST'])
def warmup_model(model_id: str):
    """Warm up a model to eliminate cold start latency"""
    app_state = current_app.config.get('app_state', {})
    loaded_models = app_state.get('loaded_models', {})

    # Check if model is loaded
    if model_id not in loaded_models:
        return jsonify({
            'error': 'Model not loaded',
            'message': f'Model {model_id} must be loaded before warming up'
        }), 404

    # Get parameters
    data = request.get_json() or {}
    num_prompts = data.get('num_prompts', 3)
    async_warmup = data.get('async', True)

    try:
        # Warm up the model
        model = loaded_models[model_id]
        status = model_warmup_service.warmup_model(
            model,
            model_id,
            num_prompts=num_prompts,
            async_warmup=async_warmup
        )

        return jsonify({
            'status': 'warming' if async_warmup and not status.is_warmed else 'warmed',
            'model_id': model_id,
            'is_warmed': status.is_warmed,
            'warmup_time_ms': status.warmup_time_ms if status.warmup_time_ms > 0 else None,
            'kernel_compilation_time_ms': status.kernel_compilation_time_ms if status.kernel_compilation_time_ms > 0 else None,
            'error': status.error
        })

    except Exception as e:
        logger.error(f"Failed to warm up model {model_id}: {e}")
        return jsonify({
            'error': 'Warmup failed',
            'message': str(e)
        }), 500


@bp.route('/warmup/status', methods=['GET'])
def get_warmup_status():
    """Get warmup status for all models"""
    all_status = model_warmup_service.get_all_warmup_status()

    # Get loaded models
    app_state = current_app.config.get('app_state', {})
    loaded_models = set(app_state.get('loaded_models', {}).keys())

    # Include loaded models that haven't been warmed
    for model_id in loaded_models:
        if model_id not in all_status:
            all_status[model_id] = {
                'is_warmed': False,
                'warmup_time_ms': 0,
                'last_warmup': None,
                'warmup_prompts_used': 0,
                'kernel_compilation_time_ms': 0,
                'error': None,
                'age_seconds': None
            }

    return jsonify({
        'warmup_status': all_status,
        'total_models': len(all_status),
        'warmed_models': sum(1 for s in all_status.values() if s['is_warmed'])
    })


@bp.route('/warmup/<model_id>/benchmark', methods=['POST'])
def benchmark_cold_vs_warm(model_id: str):
    """Benchmark cold vs warm performance for a model"""
    app_state = current_app.config.get('app_state', {})
    loaded_models = app_state.get('loaded_models', {})

    # Check if model is loaded
    if model_id not in loaded_models:
        return jsonify({
            'error': 'Model not loaded',
            'message': f'Model {model_id} must be loaded before benchmarking'
        }), 404

    try:
        # Run cold vs warm benchmark
        model = loaded_models[model_id]
        results = model_warmup_service.benchmark_cold_vs_warm(model, model_id)

        if 'error' in results:
            return jsonify(results), 500

        return jsonify(results)

    except Exception as e:
        logger.error(f"Benchmark failed for {model_id}: {e}")
        return jsonify({
            'error': 'Benchmark failed',
            'message': str(e)
        }), 500


@bp.route('/mmap/benchmark', methods=['POST'])
def benchmark_mmap_loading():
    """Benchmark memory-mapped loading vs regular loading"""
    data = request.get_json() or {}
    model_path = data.get('model_path')

    if not model_path:
        # Try to find a loaded model to benchmark
        app_state = current_app.config.get('app_state', {})
        loaded_models = app_state.get('loaded_models', {})

        if not loaded_models:
            return jsonify({
                'error': 'No model specified',
                'message': 'Provide model_path or load a model first'
            }), 400

        # Use first loaded model
        model_id = next(iter(loaded_models.keys()))
        model_path = settings.model.models_dir / model_id.replace('/', '_')
    else:
        model_path = Path(model_path)

    if not model_path.exists():
        return jsonify({
            'error': 'Model path not found',
            'message': f'Path does not exist: {model_path}'
        }), 404

    try:
        # Run benchmark
        results = mmap_loader.benchmark_load_time(model_path)

        # Add memory usage info
        memory_stats = mmap_loader.get_memory_usage()
        results.update(memory_stats)

        return jsonify({
            'status': 'success',
            'model_path': str(model_path),
            'results': results,
            'recommendation': 'Use mmap' if results.get('speedup', 0) > 1.2 else 'Regular loading is fine'
        })

    except Exception as e:
        logger.error(f"Memory map benchmark failed: {e}")
        return jsonify({
            'error': 'Benchmark failed',
            'message': str(e)
        }), 500


@bp.route('/mmap/status', methods=['GET'])
def get_mmap_status():
    """Get memory-mapped loading status"""
    stats = mmap_loader.get_memory_usage()

    return jsonify({
        'enabled': True,
        'stats': stats,
        'supported_formats': ['safetensors', 'numpy', 'pytorch']
    })
