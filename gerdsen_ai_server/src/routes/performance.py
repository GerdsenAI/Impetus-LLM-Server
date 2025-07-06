from flask import Blueprint, jsonify, current_app
import time

performance_bp = Blueprint('performance_bp', __name__)

# In-memory store for performance data (replace with a proper time-series DB in production)
performance_history = []

@performance_bp.route('/api/performance/history', methods=['GET'])
def get_performance_history():
    """
    Returns a history of performance metrics.
    In this mock implementation, it generates random data.
    """
    global performance_history
    
    # Get real metrics from the metrics collector
    try:
        # Access metrics collector from the current app context
        from gerdsen_ai_server.src.production_gerdsen_ai import RealTimeMetricsCollector
        from gerdsen_ai_server.src.enhanced_apple_silicon_detector import EnhancedAppleSiliconDetector
        
        # Create metrics collector if not available (fallback)
        if not hasattr(current_app, 'metrics_collector'):
            detector = EnhancedAppleSiliconDetector()
            current_app.metrics_collector = RealTimeMetricsCollector(detector)
        
        metrics_collector = current_app.metrics_collector
        
        # Get real metrics
        cpu_metrics = metrics_collector.get_cpu_metrics()
        memory_metrics = metrics_collector.get_memory_metrics()
        gpu_metrics = metrics_collector.get_gpu_metrics()
        
        new_point = {
            "timestamp": int(time.time() * 1000),
            "cpu_usage": cpu_metrics.get('usage_percent', 0),
            "memory_usage": memory_metrics.get('percent_used', 0),
            "gpu_usage": gpu_metrics.get('gpu_utilization_percent', 0),
            "tokens_per_second": 0  # This would come from active inference sessions
        }
    except Exception as e:
        # Fallback to default values if metrics collection fails
        new_point = {
            "timestamp": int(time.time() * 1000),
            "cpu_usage": 0,
            "memory_usage": 0,
            "gpu_usage": 0,
            "tokens_per_second": 0
        }
    
    # Add to history and keep the last 60 points (5 minutes of data)
    performance_history.append(new_point)
    performance_history = performance_history[-60:]
    
    return jsonify(performance_history)

@performance_bp.route('/api/performance/current', methods=['GET'])
def get_current_performance():
    """
    Returns the latest performance metrics.
    """
    if not performance_history:
        return jsonify({
            "timestamp": int(time.time() * 1000),
            "cpu_usage": 0,
            "memory_usage": 0,
            "gpu_usage": 0,
            "tokens_per_second": 0
        })
    return jsonify(performance_history[-1])
