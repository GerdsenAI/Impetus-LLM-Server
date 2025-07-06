from flask import Blueprint, jsonify, current_app
import time
import threading
import psutil
import logging

performance_bp = Blueprint('performance_bp', __name__)

# In-memory store for performance data (replace with a proper time-series DB in production)
performance_history = []
metrics_lock = threading.Lock()
logger = logging.getLogger(__name__)

def get_real_system_metrics():
    """Get real system metrics using psutil"""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        
        # Network I/O
        network_io = psutil.net_io_counters()
        
        # Try to get temperature (macOS specific)
        temperature = 45.0  # Default fallback
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get first available temperature sensor
                    for sensor_name, sensor_list in temps.items():
                        if sensor_list:
                            temperature = sensor_list[0].current
                            break
        except:
            pass
        
        return {
            'cpu_usage': round(cpu_percent, 1),
            'cpu_per_core': [round(usage, 1) for usage in cpu_per_core],
            'memory_usage': round(memory.percent, 1),
            'memory_used_gb': round(memory.used / (1024**3), 2),
            'memory_total_gb': round(memory.total / (1024**3), 2),
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'disk_read_mb': round(disk_io.read_bytes / (1024**2), 1) if disk_io else 0,
            'disk_write_mb': round(disk_io.write_bytes / (1024**2), 1) if disk_io else 0,
            'network_sent_mb': round(network_io.bytes_sent / (1024**2), 1) if network_io else 0,
            'network_recv_mb': round(network_io.bytes_recv / (1024**2), 1) if network_io else 0,
            'temperature': round(temperature, 1),
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {
            'cpu_usage': 0,
            'memory_usage': 0,
            'temperature': 45.0,
            'error': str(e)
        }

@performance_bp.route('/history', methods=['GET'])
def get_performance_history():
    """
    Returns a history of performance metrics using real system data.
    """
    global performance_history
    
    with metrics_lock:
        # Get real system metrics
        try:
            system_metrics = get_real_system_metrics()
            
            new_point = {
                "timestamp": int(time.time() * 1000),
                "cpu_usage": system_metrics.get('cpu_usage', 0),
                "memory_usage": system_metrics.get('memory_usage', 0),
                "temperature": system_metrics.get('temperature', 45.0),
                "memory_used_gb": system_metrics.get('memory_used_gb', 0),
                "memory_total_gb": system_metrics.get('memory_total_gb', 0),
                "load_average": system_metrics.get('load_average', 0),
                "cpu_per_core": system_metrics.get('cpu_per_core', []),
                "disk_read_mb": system_metrics.get('disk_read_mb', 0),
                "disk_write_mb": system_metrics.get('disk_write_mb', 0),
                "network_sent_mb": system_metrics.get('network_sent_mb', 0),
                "network_recv_mb": system_metrics.get('network_recv_mb', 0)
            }
            
            # Add to history and keep the last 60 points (5 minutes of data)
            performance_history.append(new_point)
            performance_history = performance_history[-60:]
            
        except Exception as e:
            logger.error(f"Error getting performance history: {e}")
            # Return existing history if available
            if not performance_history:
                return jsonify([]), 500
    
    return jsonify(performance_history)

@performance_bp.route('/current', methods=['GET'])
def get_current_performance():
    """
    Returns the latest performance metrics in real-time.
    """
    try:
        system_metrics = get_real_system_metrics()
        
        current_metrics = {
            "timestamp": int(time.time() * 1000),
            "cpu_usage": system_metrics.get('cpu_usage', 0),
            "memory_usage": system_metrics.get('memory_usage', 0),
            "temperature": system_metrics.get('temperature', 45.0),
            "memory_used_gb": system_metrics.get('memory_used_gb', 0),
            "memory_total_gb": system_metrics.get('memory_total_gb', 0),
            "memory_available_gb": system_metrics.get('memory_available_gb', 0),
            "load_average": system_metrics.get('load_average', 0),
            "cpu_per_core": system_metrics.get('cpu_per_core', []),
            "disk_io": {
                "read_mb": system_metrics.get('disk_read_mb', 0),
                "write_mb": system_metrics.get('disk_write_mb', 0)
            },
            "network_io": {
                "sent_mb": system_metrics.get('network_sent_mb', 0),
                "recv_mb": system_metrics.get('network_recv_mb', 0)
            }
        }
        
        return jsonify(current_metrics)
        
    except Exception as e:
        logger.error(f"Error getting current performance: {e}")
        return jsonify({
            "timestamp": int(time.time() * 1000),
            "cpu_usage": 0,
            "memory_usage": 0,
            "temperature": 45.0,
            "error": str(e)
        }), 500

@performance_bp.route('/system-info', methods=['GET'])
def get_system_info():
    """
    Returns detailed system information including Apple Silicon details.
    """
    try:
        # Get Apple Silicon info if available
        apple_silicon_info = {}
        try:
            from ..enhanced_apple_silicon_detector import EnhancedAppleSiliconDetector
            detector = EnhancedAppleSiliconDetector()
            chip_info = detector.get_chip_info()
            apple_silicon_info = {
                'chip_name': chip_info.get('chip_name', 'Unknown'),
                'cpu_cores': chip_info.get('total_cores', psutil.cpu_count()),
                'gpu_cores': chip_info.get('gpu_cores', 0),
                'neural_engine_cores': chip_info.get('neural_engine_cores', 0),
                'memory_gb': chip_info.get('memory_gb', 0),
                'is_apple_silicon': detector.is_apple_silicon
            }
        except Exception as e:
            logger.warning(f"Could not get Apple Silicon info: {e}")
        
        # Get basic system info
        cpu_info = {
            'physical_cores': psutil.cpu_count(logical=False),
            'logical_cores': psutil.cpu_count(logical=True),
            'max_frequency': getattr(psutil.cpu_freq(), 'max', 0) if psutil.cpu_freq() else 0,
            'current_frequency': getattr(psutil.cpu_freq(), 'current', 0) if psutil.cpu_freq() else 0
        }
        
        memory_info = psutil.virtual_memory()
        
        system_info = {
            'cpu': cpu_info,
            'memory': {
                'total_gb': round(memory_info.total / (1024**3), 2),
                'available_gb': round(memory_info.available / (1024**3), 2)
            },
            'apple_silicon': apple_silicon_info,
            'platform': {
                'system': psutil.WINDOWS if hasattr(psutil, 'WINDOWS') else 'darwin',
                'boot_time': psutil.boot_time()
            }
        }
        
        return jsonify({
            'success': True,
            'data': system_info,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/apple-silicon-metrics', methods=['GET'])
def get_apple_silicon_metrics():
    """
    Returns Apple Silicon specific performance metrics.
    """
    try:
        from ..enhanced_apple_frameworks_integration import EnhancedAppleFrameworksIntegration
        
        frameworks = EnhancedAppleFrameworksIntegration()
        benchmark_data = frameworks.benchmark_performance()
        
        apple_metrics = {
            'timestamp': time.time(),
            'benchmarks': benchmark_data.get('benchmarks', {}),
            'system_info': benchmark_data.get('system_info', {}),
            'optimization_recommendations': frameworks._get_recommended_optimizations()
        }
        
        return jsonify({
            'success': True,
            'data': apple_metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting Apple Silicon metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {}
        }), 500
