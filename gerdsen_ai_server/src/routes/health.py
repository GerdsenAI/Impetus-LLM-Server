"""
Health check and status endpoints for production monitoring
"""

import threading
import time
from datetime import datetime

import psutil
from flask import Blueprint, current_app
from loguru import logger

from ..config.settings import settings
from ..schemas.health_schemas import (
    DetailedHealthResponse,
    HealthMetrics,
    HealthStatus,
    LivenessResponse,
    MLXHealth,
    ModelHealth,
    ReadinessResponse,
    SystemHealth,
)
from ..utils.validation import create_response

bp = Blueprint('health', __name__)

start_time = datetime.now()
last_heartbeat = datetime.now()

# Health check state
health_state = {
    'last_successful_check': datetime.now(),
    'consecutive_failures': 0,
    'component_status': {},
    'metrics_history': []
}

# Thread to update heartbeat
def heartbeat_updater():
    """Update heartbeat timestamp every 5 seconds"""
    global last_heartbeat
    while True:
        last_heartbeat = datetime.now()
        time.sleep(5)

# Start heartbeat thread
heartbeat_thread = threading.Thread(target=heartbeat_updater, daemon=True)
heartbeat_thread.start()


@bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint - Kubernetes liveness probe"""
    try:
        # Quick health check
        uptime = (datetime.now() - start_time).total_seconds()

        # Check if heartbeat is recent (within last 30 seconds)
        heartbeat_age = (datetime.now() - last_heartbeat).total_seconds()
        if heartbeat_age > 30:
            logger.warning(f"Heartbeat is stale: {heartbeat_age}s")
            return create_response({
                'status': 'unhealthy',
                'error': 'Heartbeat stale',
                'timestamp': datetime.now().isoformat()
            }, 503)

        health_status = HealthStatus(
            status='healthy',
            timestamp=datetime.now(),
            version=settings.version,
            uptime_seconds=uptime
        )

        health_state['last_successful_check'] = datetime.now()
        health_state['consecutive_failures'] = 0

        return create_response(health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_state['consecutive_failures'] += 1

        return create_response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 503)


@bp.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness probe - checks if service is ready to handle requests"""
    try:
        checks = {}
        ready = True

        # Check if models are available (if required)
        app_state = current_app.config.get('app_state', {})
        loaded_models = app_state.get('loaded_models', {})

        # Check system resources
        memory = psutil.virtual_memory()
        checks['memory_available'] = memory.percent < 95
        checks['models_loaded'] = len(loaded_models) > 0 or not settings.model.require_model_for_ready

        # Check MLX availability (if on macOS)
        try:
            import platform
            if platform.system() == 'Darwin':
                import mlx.core as mx
                mx.array([1, 2, 3])  # Simple test
                checks['mlx_available'] = True
            else:
                checks['mlx_available'] = True  # Not required on non-macOS
        except Exception as e:
            logger.warning(f"MLX check failed: {e}")
            checks['mlx_available'] = False

        # Overall readiness
        ready = all(checks.values())

        response = ReadinessResponse(
            ready=ready,
            timestamp=datetime.now(),
            checks=checks,
            message="Ready" if ready else "Not ready"
        )

        return create_response(response, 200 if ready else 503)

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return create_response({
            'ready': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 503)


@bp.route('/status', methods=['GET'])
def detailed_status():
    """Detailed health status with component information"""
    try:
        uptime = (datetime.now() - start_time).total_seconds()
        app_state = current_app.config.get('app_state', {})

        # System health
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]

        # Get thermal state from hardware info
        app_state.get('hardware_info', {})
        thermal_state = 'nominal'  # Default

        system_health = SystemHealth(
            name='system',
            status='healthy' if cpu_percent < 80 and memory.percent < 90 else 'degraded',
            message=f"CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%",
            last_check=datetime.now(),
            cpu_usage_percent=cpu_percent,
            memory_usage_percent=memory.percent,
            thermal_state=thermal_state,
            load_average=list(load_avg)
        )

        # Model health
        loaded_models = app_state.get('loaded_models', {})
        model_inference_counts = app_state.get('model_inference_counts', {})
        model_health_list = []

        for model_id in loaded_models:
            model_health_list.append(ModelHealth(
                name=f"model_{model_id.replace('/', '_')}",
                status='healthy',
                model_id=model_id,
                load_status='loaded',
                last_check=datetime.now(),
                inference_count=model_inference_counts.get(model_id, 0)
            ))

        # MLX health
        mlx_health = None
        try:
            import platform
            if platform.system() == 'Darwin':
                import mlx
                mlx_health = MLXHealth(
                    name='mlx',
                    status='healthy',
                    version=mlx.__version__,
                    metal_available=True,
                    last_check=datetime.now()
                )
        except Exception as e:
            logger.warning(f"MLX health check failed: {e}")

        # Calculate overall health score
        health_score = 100.0
        if cpu_percent > 80:
            health_score -= 20
        if memory.percent > 90:
            health_score -= 30
        if len(loaded_models) == 0:
            health_score -= 10

        overall_status = 'healthy'
        if health_score < 70:
            overall_status = 'degraded'
        if health_score < 40:
            overall_status = 'unhealthy'

        response = DetailedHealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version=settings.version,
            uptime_seconds=uptime,
            components=[system_health],
            system=system_health,
            models=model_health_list,
            mlx=mlx_health,
            health_score=health_score
        )

        return create_response(response)

    except Exception as e:
        logger.error(f"Detailed status check failed: {e}")
        return create_response({
            'error': str(e),
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat()
        }, 500)


@bp.route('/live', methods=['GET'])
def liveness_check():
    """Kubernetes liveness probe - simpler than /health"""
    try:
        response = LivenessResponse(
            alive=True,
            timestamp=datetime.now(),
            uptime_seconds=(datetime.now() - start_time).total_seconds(),
            last_heartbeat=last_heartbeat
        )
        return create_response(response)
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return create_response({
            'alive': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 503)


@bp.route('/metrics', methods=['GET'])
def prometheus_metrics():
    """Enhanced Prometheus-compatible metrics endpoint"""
    try:
        app_state = current_app.config.get('app_state', {})
        metrics = app_state.get('metrics', {})
        loaded_models = app_state.get('loaded_models', {})

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        uptime = (datetime.now() - start_time).total_seconds()

        # Format metrics in Prometheus format
        output = []

        # Application metrics
        output.append('# HELP impetus_info Application information')
        output.append('# TYPE impetus_info gauge')
        output.append(f'impetus_info{{version=\"{settings.version}\",environment=\"{settings.environment}\"}} 1')

        output.append('# HELP impetus_uptime_seconds Application uptime in seconds')
        output.append('# TYPE impetus_uptime_seconds gauge')
        output.append(f'impetus_uptime_seconds {uptime}')

        # Request metrics
        output.append('# HELP impetus_requests_total Total number of requests')
        output.append('# TYPE impetus_requests_total counter')
        output.append(f'impetus_requests_total {metrics.get("requests_total", 0)}')

        output.append('# HELP impetus_tokens_generated_total Total tokens generated')
        output.append('# TYPE impetus_tokens_generated_total counter')
        output.append(f'impetus_tokens_generated_total {metrics.get("tokens_generated", 0)}')

        output.append('# HELP impetus_average_latency_ms Average request latency in milliseconds')
        output.append('# TYPE impetus_average_latency_ms gauge')
        output.append(f'impetus_average_latency_ms {metrics.get("average_latency_ms", 0)}')

        # Model metrics
        output.append('# HELP impetus_models_loaded Number of models currently loaded')
        output.append('# TYPE impetus_models_loaded gauge')
        output.append(f'impetus_models_loaded {len(loaded_models)}')

        # System metrics
        output.append('# HELP impetus_cpu_usage_percent CPU usage percentage')
        output.append('# TYPE impetus_cpu_usage_percent gauge')
        output.append(f'impetus_cpu_usage_percent {cpu_percent}')

        output.append('# HELP impetus_memory_usage_percent Memory usage percentage')
        output.append('# TYPE impetus_memory_usage_percent gauge')
        output.append(f'impetus_memory_usage_percent {memory.percent}')

        output.append('# HELP impetus_memory_available_bytes Available memory in bytes')
        output.append('# TYPE impetus_memory_available_bytes gauge')
        output.append(f'impetus_memory_available_bytes {memory.available}')

        # Health check metrics
        output.append('# HELP impetus_health_status Health status (1=healthy, 0=unhealthy)')
        output.append('# TYPE impetus_health_status gauge')
        output.append(f'impetus_health_status {1 if health_state["consecutive_failures"] == 0 else 0}')

        output.append('# HELP impetus_consecutive_health_failures Number of consecutive health check failures')
        output.append('# TYPE impetus_consecutive_health_failures gauge')
        output.append(f'impetus_consecutive_health_failures {health_state["consecutive_failures"]}')

        # Per-model metrics
        for model_id in loaded_models:
            model_id.replace('/', '_').replace('-', '_')
            output.append('# HELP impetus_model_loaded Model loaded status')
            output.append('# TYPE impetus_model_loaded gauge')
            output.append(f'impetus_model_loaded{{model=\"{model_id}\"}} 1')

        return '\n'.join(output), 200, {'Content-Type': 'text/plain; charset=utf-8'}

    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return f"# Error generating metrics: {e}", 500, {'Content-Type': 'text/plain'}


@bp.route('/metrics/json', methods=['GET'])
def json_metrics():
    """JSON format metrics for easier consumption"""
    try:
        app_state = current_app.config.get('app_state', {})
        metrics = app_state.get('metrics', {})
        loaded_models = app_state.get('loaded_models', {})

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        (datetime.now() - start_time).total_seconds()

        # Get process metrics
        process = psutil.Process()
        process_memory = process.memory_info()

        metrics_response = HealthMetrics(
            timestamp=datetime.now(),
            total_requests=metrics.get('requests_total', 0),
            successful_requests=metrics.get('successful_requests', 0),
            failed_requests=metrics.get('failed_requests', 0),
            requests_per_minute=metrics.get('requests_per_minute', 0.0),
            avg_response_time_ms=metrics.get('average_latency_ms', 0.0),
            p50_response_time_ms=metrics.get('p50_latency_ms', 0.0),
            p95_response_time_ms=metrics.get('p95_latency_ms', 0.0),
            p99_response_time_ms=metrics.get('p99_latency_ms', 0.0),
            error_rate_percent=metrics.get('error_rate_percent', 0.0),
            error_count_5min=metrics.get('error_count_5min', 0),
            cpu_usage_percent=cpu_percent,
            memory_usage_mb=process_memory.rss / (1024 * 1024),
            memory_usage_percent=memory.percent,
            loaded_models_count=len(loaded_models),
            total_inferences=metrics.get('total_inferences', 0),
            avg_inference_time_ms=metrics.get('avg_inference_time_ms', 0.0),
            active_connections=metrics.get('active_connections', 0),
            websocket_connections=metrics.get('websocket_connections', 0)
        )

        return create_response(metrics_response)

    except Exception as e:
        logger.error(f"JSON metrics endpoint failed: {e}")
        return create_response({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500)
