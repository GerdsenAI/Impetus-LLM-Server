"""
Health check and status endpoints
"""

from flask import Blueprint, jsonify, current_app
from datetime import datetime
import psutil
from ..config.settings import settings

bp = Blueprint('health', __name__)

start_time = datetime.now()


@bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': settings.version
    })


@bp.route('/status', methods=['GET'])
def status():
    """Detailed status information"""
    uptime = (datetime.now() - start_time).total_seconds()
    
    # Get current resource usage
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    # Get app state from current_app
    app_state = current_app.config.get('app_state', {})
    
    return jsonify({
        'status': 'operational',
        'version': settings.version,
        'environment': settings.environment,
        'uptime_seconds': uptime,
        'timestamp': datetime.now().isoformat(),
        'system': {
            'cpu_usage_percent': cpu_percent,
            'memory_usage_percent': memory.percent,
            'memory_available_gb': memory.available / (1024 ** 3)
        },
        'models': {
            'loaded_count': len(app_state.get('loaded_models', {})),
            'loaded_models': list(app_state.get('loaded_models', {}).keys())
        },
        'metrics': app_state.get('metrics', {}),
        'hardware': {
            'chip_type': app_state.get('hardware_info', {}).get('chip_type', 'Unknown'),
            'performance_mode': settings.hardware.performance_mode
        }
    })


@bp.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus-compatible metrics endpoint"""
    app_state = current_app.config.get('app_state', {})
    metrics = app_state.get('metrics', {})
    
    # Format metrics in Prometheus format
    output = []
    output.append(f'# HELP impetus_requests_total Total number of requests')
    output.append(f'# TYPE impetus_requests_total counter')
    output.append(f'impetus_requests_total {metrics.get("requests_total", 0)}')
    
    output.append(f'# HELP impetus_tokens_generated_total Total tokens generated')
    output.append(f'# TYPE impetus_tokens_generated_total counter')
    output.append(f'impetus_tokens_generated_total {metrics.get("tokens_generated", 0)}')
    
    output.append(f'# HELP impetus_average_latency_ms Average request latency')
    output.append(f'# TYPE impetus_average_latency_ms gauge')
    output.append(f'impetus_average_latency_ms {metrics.get("average_latency_ms", 0)}')
    
    output.append(f'# HELP impetus_models_loaded Number of models currently loaded')
    output.append(f'# TYPE impetus_models_loaded gauge')
    output.append(f'impetus_models_loaded {len(app_state.get("loaded_models", {}))}')
    
    return '\n'.join(output), 200, {'Content-Type': 'text/plain'}