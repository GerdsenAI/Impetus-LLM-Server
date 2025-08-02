"""
Hardware monitoring and optimization endpoints
"""

from flask import Blueprint, jsonify, current_app
import psutil
from loguru import logger
from ..utils.hardware_detector import detect_hardware, get_thermal_state
from ..utils.metal_monitor import metal_monitor, MetalMetrics
from ..config.settings import settings

bp = Blueprint('hardware', __name__)


@bp.route('/info', methods=['GET'])
def hardware_info():
    """Get hardware information"""
    app_state = current_app.config.get('app_state', {})
    hardware_info = app_state.get('hardware_info')
    
    if not hardware_info:
        # Re-detect if not cached
        hardware_info = detect_hardware()
        app_state['hardware_info'] = hardware_info
    
    return jsonify(hardware_info)


@bp.route('/metrics', methods=['GET'])
def hardware_metrics():
    """Get real-time hardware metrics"""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        # Temperature and thermal state
        thermal = get_thermal_state()
        
        # Process-specific metrics
        process = psutil.Process()
        process_info = {
            'cpu_percent': process.cpu_percent(interval=0.1),
            'memory_mb': process.memory_info().rss / (1024 * 1024),
            'threads': process.num_threads(),
            'open_files': len(process.open_files())
        }
        
        # Get Metal GPU metrics if available
        gpu_metrics = None
        if metal_monitor._is_macos():
            try:
                metal_metrics = metal_monitor.get_current_metrics()
                gpu_metrics = {
                    'utilization_percent': metal_metrics.gpu_utilization,
                    'frequency_mhz': metal_metrics.gpu_frequency_mhz,
                    'memory_used_gb': metal_metrics.memory_used_gb,
                    'memory_total_gb': metal_metrics.memory_total_gb,
                    'memory_bandwidth_percent': metal_metrics.memory_bandwidth_utilization,
                    'temperature_celsius': metal_metrics.temperature_celsius
                }
            except Exception as e:
                logger.debug(f"Failed to get Metal metrics: {e}")
        
        metrics = {
            'timestamp': psutil.boot_time(),
            'cpu': {
                'usage_percent': sum(cpu_percent) / len(cpu_percent),
                'usage_per_core': cpu_percent,
                'frequency_mhz': cpu_freq.current if cpu_freq else 0,
                'frequency_min_mhz': cpu_freq.min if cpu_freq else 0,
                'frequency_max_mhz': cpu_freq.max if cpu_freq else 0
            },
            'memory': {
                'total_gb': memory.total / (1024 ** 3),
                'available_gb': memory.available / (1024 ** 3),
                'used_gb': memory.used / (1024 ** 3),
                'percent': memory.percent,
                'swap_used_gb': swap.used / (1024 ** 3),
                'swap_percent': swap.percent
            },
            'gpu': gpu_metrics,
            'disk': {
                'total_gb': disk.total / (1024 ** 3),
                'used_gb': disk.used / (1024 ** 3),
                'free_gb': disk.free / (1024 ** 3),
                'percent': disk.percent
            },
            'network': {
                'bytes_sent_mb': net_io.bytes_sent / (1024 * 1024),
                'bytes_recv_mb': net_io.bytes_recv / (1024 * 1024),
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            },
            'thermal': thermal,
            'process': process_info
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error getting hardware metrics: {e}")
        return jsonify({'error': 'Failed to get hardware metrics'}), 500


@bp.route('/optimization', methods=['GET'])
def optimization_recommendations():
    """Get hardware-specific optimization recommendations"""
    app_state = current_app.config.get('app_state', {})
    hardware_info = app_state.get('hardware_info', {})
    
    # Get current metrics
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=0.1)
    thermal = get_thermal_state()
    
    recommendations = {
        'current_performance_mode': settings.hardware.performance_mode,
        'chip_type': hardware_info.get('chip_type', 'Unknown'),
        'recommendations': []
    }
    
    # Memory recommendations
    if memory.percent > 80:
        recommendations['recommendations'].append({
            'type': 'memory',
            'severity': 'high',
            'message': 'High memory usage detected. Consider unloading unused models.',
            'action': 'unload_models'
        })
    
    # Thermal recommendations
    if thermal['thermal_state'] in ['serious', 'critical']:
        recommendations['recommendations'].append({
            'type': 'thermal',
            'severity': 'high',
            'message': 'High thermal state detected. Switching to efficiency mode recommended.',
            'action': 'set_efficiency_mode'
        })
    
    # CPU recommendations
    if cpu_percent > 90:
        recommendations['recommendations'].append({
            'type': 'cpu',
            'severity': 'medium',
            'message': 'High CPU usage. Consider reducing batch size or concurrent requests.',
            'action': 'reduce_load'
        })
    
    # Model-specific recommendations
    if hardware_info.get('chip_type', '').startswith('M'):
        bandwidth = hardware_info.get('max_memory_bandwidth_gbps', 100)
        
        recommendations['hardware_capabilities'] = {
            'max_memory_bandwidth_gbps': bandwidth,
            'recommended_batch_size': hardware_info.get('recommended_batch_size', 1),
            'recommended_context_length': hardware_info.get('recommended_context_length', 2048),
            'supports_metal': True,
            'supports_neural_engine': True
        }
        
        # Chip-specific optimizations
        if 'Ultra' in hardware_info.get('chip_type', ''):
            recommendations['recommendations'].append({
                'type': 'performance',
                'severity': 'info',
                'message': 'Ultra chip detected. You can enable multi-model inference for maximum throughput.',
                'action': 'enable_multi_model'
            })
        elif 'Max' in hardware_info.get('chip_type', ''):
            recommendations['recommendations'].append({
                'type': 'performance',
                'severity': 'info',
                'message': 'Max chip detected. Optimal for large models up to 70B parameters.',
                'action': 'use_large_models'
            })
    
    return jsonify(recommendations)


@bp.route('/performance-mode', methods=['POST'])
def set_performance_mode():
    """Set performance mode"""
    from flask import request
    
    data = request.get_json()
    mode = data.get('mode', 'balanced')
    
    if mode not in ['efficiency', 'balanced', 'performance']:
        return jsonify({'error': 'Invalid performance mode'}), 400
    
    settings.hardware.performance_mode = mode
    
    # Adjust settings based on mode
    if mode == 'efficiency':
        settings.hardware.max_cpu_percent = 60.0
        settings.hardware.max_memory_percent = 70.0
        logger.info("Switched to efficiency mode")
    elif mode == 'performance':
        settings.hardware.max_cpu_percent = 95.0
        settings.hardware.max_memory_percent = 90.0
        logger.info("Switched to performance mode")
    else:  # balanced
        settings.hardware.max_cpu_percent = 80.0
        settings.hardware.max_memory_percent = 75.0
        logger.info("Switched to balanced mode")
    
    return jsonify({
        'mode': mode,
        'settings': {
            'max_cpu_percent': settings.hardware.max_cpu_percent,
            'max_memory_percent': settings.hardware.max_memory_percent
        }
    })


@bp.route('/gpu/metrics', methods=['GET'])
def gpu_metrics():
    """Get detailed GPU/Metal metrics"""
    if not metal_monitor._is_macos():
        return jsonify({'error': 'GPU metrics only available on macOS'}), 404
    
    try:
        # Get current metrics
        current = metal_monitor.get_current_metrics()
        
        # Get average metrics over last minute
        avg_1min = metal_monitor.get_average_metrics(window_seconds=60)
        
        # Get peak metrics
        peak = metal_monitor.get_peak_metrics()
        
        metrics = {
            'current': {
                'timestamp': current.timestamp,
                'gpu_utilization_percent': current.gpu_utilization,
                'gpu_frequency_mhz': current.gpu_frequency_mhz,
                'memory_used_gb': current.memory_used_gb,
                'memory_total_gb': current.memory_total_gb,
                'memory_bandwidth_percent': current.memory_bandwidth_utilization,
                'temperature_celsius': current.temperature_celsius,
                'power_watts': current.power_watts
            },
            'average_1min': {
                'gpu_utilization_percent': avg_1min.gpu_utilization if avg_1min else 0,
                'gpu_frequency_mhz': avg_1min.gpu_frequency_mhz if avg_1min else 0,
                'memory_bandwidth_percent': avg_1min.memory_bandwidth_utilization if avg_1min else 0
            } if avg_1min else None,
            'peak': {
                'gpu_utilization_percent': peak.gpu_utilization if peak else 0,
                'gpu_frequency_mhz': peak.gpu_frequency_mhz if peak else 0,
                'timestamp': peak.timestamp if peak else 0
            } if peak else None,
            'history_size': len(metal_monitor.metrics_history)
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error getting GPU metrics: {e}")
        return jsonify({'error': 'Failed to get GPU metrics'}), 500


@bp.route('/gpu/start-monitoring', methods=['POST'])
def start_gpu_monitoring():
    """Start continuous GPU monitoring"""
    try:
        if not metal_monitor._is_macos():
            return jsonify({'error': 'GPU monitoring only available on macOS'}), 404
        
        metal_monitor.start_monitoring(interval_seconds=1.0)
        
        return jsonify({
            'status': 'started',
            'message': 'GPU monitoring started',
            'interval_seconds': 1.0
        })
    except Exception as e:
        logger.error(f"Error starting GPU monitoring: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/gpu/stop-monitoring', methods=['POST'])
def stop_gpu_monitoring():
    """Stop continuous GPU monitoring"""
    try:
        metal_monitor.stop_monitoring()
        
        return jsonify({
            'status': 'stopped',
            'message': 'GPU monitoring stopped'
        })
    except Exception as e:
        logger.error(f"Error stopping GPU monitoring: {e}")
        return jsonify({'error': str(e)}), 500