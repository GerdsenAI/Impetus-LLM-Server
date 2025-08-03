"""
WebSocket handlers for real-time updates
"""

import threading
import time

import psutil
from flask_socketio import emit, join_room, leave_room
from loguru import logger

from ..utils.error_recovery import ErrorType, error_recovery_service
from ..utils.hardware_detector import get_thermal_state
from ..utils.metal_monitor import metal_monitor


def register_handlers(socketio, app_state):
    """Register WebSocket event handlers"""

    # Store socketio instance for use by other modules
    app_state['socketio'] = socketio

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        client_id = request.sid
        logger.info(f"Client connected: {client_id}")

        # Add to active sessions
        app_state['active_sessions'][client_id] = {
            'connected_at': time.time(),
            'rooms': set()
        }

        # Send initial hardware info
        emit('hardware_info', app_state.get('hardware_info', {}))

        # Send loaded models
        loaded_models = list(app_state.get('loaded_models', {}).keys())
        emit('models_update', {'loaded_models': loaded_models})


    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        client_id = request.sid
        logger.info(f"Client disconnected: {client_id}")

        # Remove from active sessions
        app_state['active_sessions'].pop(client_id, None)


    @socketio.on('subscribe')
    def handle_subscribe(data):
        """Subscribe to specific update channels"""
        client_id = request.sid
        room = data.get('room')

        if room in ['metrics', 'hardware', 'models', 'logs']:
            join_room(room)
            if client_id in app_state['active_sessions']:
                app_state['active_sessions'][client_id]['rooms'].add(room)
            logger.info(f"Client {client_id} subscribed to {room}")
            emit('subscribed', {'room': room})
        else:
            emit('error', {'message': f'Invalid room: {room}'})


    @socketio.on('unsubscribe')
    def handle_unsubscribe(data):
        """Unsubscribe from update channels"""
        client_id = request.sid
        room = data.get('room')

        leave_room(room)
        if client_id in app_state['active_sessions']:
            app_state['active_sessions'][client_id]['rooms'].discard(room)
        logger.info(f"Client {client_id} unsubscribed from {room}")
        emit('unsubscribed', {'room': room})


    @socketio.on('get_metrics')
    def handle_get_metrics():
        """Get current metrics on demand"""
        metrics = gather_metrics(app_state)
        emit('metrics_update', metrics)


    @socketio.on('get_hardware_status')
    def handle_get_hardware_status():
        """Get current hardware status"""
        hardware_status = gather_hardware_status(app_state)
        emit('hardware_status', hardware_status)


    @socketio.on('subscribe_download')
    def handle_subscribe_download(data):
        """Subscribe to download progress updates"""
        task_id = data.get('task_id')
        if not task_id:
            emit('error', {'message': 'task_id required'})
            return

        # Join download-specific room
        room = f'download_{task_id}'
        join_room(room)
        logger.info(f"Client {request.sid} subscribed to download {task_id}")

        # Send current status
        from ..services.download_manager import download_manager
        task = download_manager.get_task_status(task_id)
        if task:
            emit('download_progress', {
                'task_id': task.task_id,
                'model_id': task.model_id,
                'status': task.status.value,
                'progress': task.progress,
                'downloaded_gb': task.downloaded_bytes / (1024 ** 3) if task.downloaded_bytes else 0,
                'total_gb': task.total_bytes / (1024 ** 3) if task.total_bytes else 0,
                'speed_mbps': task.speed_mbps,
                'eta_seconds': task.eta_seconds
            })


    @socketio.on('unsubscribe_download')
    def handle_unsubscribe_download(data):
        """Unsubscribe from download progress updates"""
        task_id = data.get('task_id')
        if task_id:
            room = f'download_{task_id}'
            leave_room(room)
            logger.info(f"Client {request.sid} unsubscribed from download {task_id}")


    # Start background tasks for periodic updates
    def metrics_broadcaster():
        """Broadcast metrics to subscribed clients"""
        while True:
            try:
                metrics = gather_metrics(app_state)
                socketio.emit('metrics_update', metrics, room='metrics')
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                logger.error(f"Error broadcasting metrics: {e}")
                time.sleep(5)


    def hardware_monitor():
        """Monitor hardware status and broadcast updates"""
        last_thermal_state = None

        while True:
            try:
                hardware_status = gather_hardware_status(app_state)
                thermal_state = hardware_status.get('thermal', {}).get('thermal_state')

                # Always broadcast to hardware room
                socketio.emit('hardware_status', hardware_status, room='hardware')

                # Broadcast thermal warnings to all clients
                if thermal_state != last_thermal_state and thermal_state in ['serious', 'critical']:
                    socketio.emit('thermal_warning', {
                        'state': thermal_state,
                        'message': f'System thermal state: {thermal_state}'
                    })

                    # Trigger thermal recovery
                    if thermal_state == 'critical':
                        error_recovery_service.handle_error(
                            ErrorType.THERMAL_THROTTLE,
                            Exception(f"Critical thermal state: {thermal_state}"),
                            {'thermal_state': thermal_state}
                        )

                last_thermal_state = thermal_state
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Error monitoring hardware: {e}")
                time.sleep(10)


    # Start background threads
    metrics_thread = threading.Thread(target=metrics_broadcaster, daemon=True)
    metrics_thread.start()

    hardware_thread = threading.Thread(target=hardware_monitor, daemon=True)
    hardware_thread.start()

    logger.info("WebSocket handlers registered and background tasks started")


def gather_metrics(app_state):
    """Gather current system and application metrics"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    # Get process metrics
    process = psutil.Process()
    process_memory = process.memory_info().rss / (1024 ** 3)  # GB

    # Get GPU metrics if available
    gpu_data = None
    if metal_monitor._is_macos():
        try:
            metal_metrics = metal_monitor.get_current_metrics()
            gpu_data = {
                'utilization_percent': metal_metrics.gpu_utilization,
                'memory_used_gb': metal_metrics.memory_used_gb,
                'memory_bandwidth_percent': metal_metrics.memory_bandwidth_utilization
            }
        except:
            pass

    metrics = {
        'timestamp': time.time(),
        'system': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024 ** 3)
        },
        'gpu': gpu_data,
        'process': {
            'memory_gb': process_memory,
            'threads': process.num_threads()
        },
        'application': app_state.get('metrics', {}),
        'models': {
            'loaded_count': len(app_state.get('loaded_models', {})),
            'loaded_models': list(app_state.get('loaded_models', {}).keys())
        }
    }

    return metrics


def gather_hardware_status(app_state):
    """Gather current hardware status"""
    thermal = get_thermal_state()
    cpu_freq = psutil.cpu_freq()

    # Get per-core CPU usage
    cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)

    status = {
        'timestamp': time.time(),
        'thermal': thermal,
        'cpu': {
            'frequency_mhz': cpu_freq.current if cpu_freq else 0,
            'usage_per_core': cpu_per_core,
            'average_usage': sum(cpu_per_core) / len(cpu_per_core)
        },
        'performance_mode': app_state.get('hardware_info', {}).get('performance_mode', 'balanced')
    }

    return status


# Import request context for WebSocket handlers
from flask import request
