#!/usr/bin/env python3
"""
Enhanced Hardware API Routes
Provides real-time hardware monitoring and Apple Silicon optimization endpoints
"""

from flask import Blueprint, jsonify, request
from ..enhanced_apple_frameworks_integration import EnhancedAppleFrameworksIntegration
import logging
import time
import threading
from typing import Dict, Any

hardware_bp = Blueprint('hardware', __name__)

# Global enhanced frameworks integration instance
frameworks = None
metrics_cache = {}
cache_lock = threading.Lock()

def initialize_frameworks():
    """Initialize the enhanced Apple frameworks integration"""
    global frameworks
    if frameworks is None:
        frameworks = EnhancedAppleFrameworksIntegration()
        logging.info("Enhanced Apple frameworks integration initialized")

def update_metrics_cache():
    """Update metrics cache in background"""
    global metrics_cache
    if frameworks:
        try:
            # Get comprehensive system info including real-time metrics
            system_info = frameworks.get_system_info()
            benchmark_data = frameworks.benchmark_performance()
            
            new_metrics = {
                'system_info': system_info,
                'benchmarks': benchmark_data.get('benchmarks', {}),
                'timestamp': time.time()
            }
            
            with cache_lock:
                metrics_cache = new_metrics
        except Exception as e:
            logging.error(f"Failed to update metrics cache: {e}")

# Initialize frameworks on module load
initialize_frameworks()

@hardware_bp.route('/system-info', methods=['GET'])
def get_system_info():
    """Get comprehensive system information with Apple Silicon details"""
    try:
        if not frameworks:
            return jsonify({'error': 'Apple frameworks integration not available'}), 500
        
        info = frameworks.get_system_info()
        return jsonify({
            'success': True,
            'data': info,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting system info: {e}")
        return jsonify({'error': str(e)}), 500

@hardware_bp.route('/chip-info', methods=['GET'])
def get_chip_info():
    """Get detailed Apple Silicon chip information"""
    try:
        if not frameworks:
            return jsonify({'error': 'Apple frameworks integration not available'}), 500
        
        system_info = frameworks.get_system_info()
        chip_info = system_info.get('chip_info')
        
        if not chip_info:
            return jsonify({'error': 'Chip information not available'}), 400
        
        return jsonify({
            'success': True,
            'data': chip_info,
            'apple_silicon': system_info.get('apple_silicon', False),
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting chip info: {e}")
        return jsonify({'error': str(e)}), 500

@hardware_bp.route('/real-time-metrics', methods=['GET'])
def get_real_time_metrics():
    """Get real-time system performance metrics"""
    try:
        if not frameworks:
            return jsonify({'error': 'Apple frameworks integration not available'}), 500
        
        # Use cached metrics if available and recent
        with cache_lock:
            if metrics_cache and time.time() - metrics_cache.get('timestamp', 0) < 2:
                return jsonify({
                    'success': True,
                    'data': metrics_cache,
                    'cached': True
                })
        
        # Get fresh metrics
        benchmark_data = frameworks.benchmark_performance()
        
        # Extract real-time metrics
        metrics = {
            'cpu': benchmark_data.get('benchmarks', {}).get('cpu', {}),
            'memory': benchmark_data.get('benchmarks', {}).get('memory', {}),
            'gpu': benchmark_data.get('benchmarks', {}).get('gpu', {}),
            'neural_engine': benchmark_data.get('benchmarks', {}).get('neural_engine', {}),
            'timestamp': time.time()
        }
        
        # Update cache
        with cache_lock:
            metrics_cache.update(metrics)
        
        return jsonify({
            'success': True,
            'data': metrics,
            'cached': False
        })
    
    except Exception as e:
        logging.error(f"Error getting real-time metrics: {e}")
        return jsonify({'error': str(e)}), 500

@hardware_bp.route('/neural-engine', methods=['GET'])
def get_neural_engine_info():
    """Get Neural Engine information and capabilities"""
    try:
        if not frameworks:
            return jsonify({'error': 'Apple frameworks integration not available'}), 500
        
        system_info = frameworks.get_system_info()
        optimization_profile = system_info.get('optimization_profile', {})
        
        neural_info = {
            'available': optimization_profile.get('neural_engine_enabled', False),
            'cores': optimization_profile.get('neural_engine_cores', 0),
            'chip_name': optimization_profile.get('chip_name', 'Unknown'),
            'framework_support': system_info.get('framework_availability', {}),
            'optimization_recommendations': system_info.get('recommended_optimizations', [])
        }
        
        # Add Neural Engine benchmark if available
        benchmark_data = frameworks.benchmark_performance()
        neural_benchmark = benchmark_data.get('benchmarks', {}).get('neural_engine', {})
        if neural_benchmark:
            neural_info['performance'] = neural_benchmark
        
        return jsonify({
            'success': True,
            'data': neural_info,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting Neural Engine info: {e}")
        return jsonify({'error': str(e)}), 500

@hardware_bp.route('/gpu-info', methods=['GET'])
def get_gpu_info():
    """Get GPU information and Metal capabilities"""
    try:
        if not frameworks:
            return jsonify({'error': 'Apple frameworks integration not available'}), 500
        
        system_info = frameworks.get_system_info()
        optimization_profile = system_info.get('optimization_profile', {})
        
        gpu_info = {
            'cores': optimization_profile.get('gpu_cores', 0),
            'metal_enabled': optimization_profile.get('metal_enabled', False),
            'chip_name': optimization_profile.get('chip_name', 'Unknown'),
            'framework_support': system_info.get('framework_availability', {})
        }
        
        # Add GPU benchmark if available
        benchmark_data = frameworks.benchmark_performance()
        gpu_benchmark = benchmark_data.get('benchmarks', {}).get('gpu', {})
        if gpu_benchmark:
            gpu_info['performance'] = gpu_benchmark
        
        return jsonify({
            'success': True,
            'data': gpu_info,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting GPU info: {e}")
        return jsonify({'error': str(e)}), 500

@hardware_bp.route('/optimization-status', methods=['GET'])
def get_optimization_status():
    """Get comprehensive hardware optimization status"""
    try:
        if not frameworks:
            return jsonify({'error': 'Apple frameworks integration not available'}), 500
        
        system_info = frameworks.get_system_info()
        optimization_profile = system_info.get('optimization_profile', {})
        framework_availability = system_info.get('framework_availability', {})
        
        optimization_status = {
            'apple_silicon_optimized': system_info.get('apple_silicon', False),
            'neural_engine_available': optimization_profile.get('neural_engine_enabled', False),
            'neural_engine_cores': optimization_profile.get('neural_engine_cores', 0),
            'gpu_cores': optimization_profile.get('gpu_cores', 0),
            'metal_support': optimization_profile.get('metal_enabled', False),
            'mlx_support': optimization_profile.get('mlx_enabled', False),
            'coreml_support': framework_availability.get('coreml', False),
            'unified_memory': optimization_profile.get('memory_gb', 0) > 0,
            'optimization_level': 'enhanced' if system_info.get('apple_silicon') else 'basic',
            'recommended_optimizations': system_info.get('recommended_optimizations', [])
        }
        
        return jsonify({
            'success': True,
            'data': optimization_status,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting optimization status: {e}")
        return jsonify({'error': str(e)}), 500

@hardware_bp.route('/performance-profile', methods=['GET'])
def get_performance_profile():
    """Get recommended performance profile based on detected hardware"""
    try:
        if not frameworks:
            return jsonify({'error': 'Apple frameworks integration not available'}), 500
        
        system_info = frameworks.get_system_info()
        optimization_profile = system_info.get('optimization_profile', {})
        
        chip_name = optimization_profile.get('chip_name', 'Unknown')
        gpu_cores = optimization_profile.get('gpu_cores', 0)
        memory_gb = optimization_profile.get('memory_gb', 0)
        neural_engine_cores = optimization_profile.get('neural_engine_cores', 0)
        
        # Determine performance profile based on chip capabilities
        if 'M4' in chip_name and 'Ultra' in chip_name:
            profile = 'ultra_high_performance'
            recommended_settings = {
                'max_batch_size': 64,
                'memory_allocation': 0.85,
                'gpu_utilization_target': 0.95,
                'neural_engine_enabled': True,
                'metal_performance_shaders': True,
                'mlx_optimization': True,
                'coreml_optimization': True
            }
        elif 'M4' in chip_name or ('M3' in chip_name and 'Ultra' in chip_name):
            profile = 'ultra_performance'
            recommended_settings = {
                'max_batch_size': 48,
                'memory_allocation': 0.8,
                'gpu_utilization_target': 0.9,
                'neural_engine_enabled': True,
                'metal_performance_shaders': True,
                'mlx_optimization': True,
                'coreml_optimization': True
            }
        elif gpu_cores >= 32 and memory_gb >= 64:
            profile = 'high_performance'
            recommended_settings = {
                'max_batch_size': 32,
                'memory_allocation': 0.8,
                'gpu_utilization_target': 0.9,
                'neural_engine_enabled': True,
                'metal_performance_shaders': True,
                'mlx_optimization': True,
                'coreml_optimization': True
            }
        elif gpu_cores >= 16 and memory_gb >= 32:
            profile = 'balanced_performance'
            recommended_settings = {
                'max_batch_size': 16,
                'memory_allocation': 0.75,
                'gpu_utilization_target': 0.85,
                'neural_engine_enabled': True,
                'metal_performance_shaders': True,
                'mlx_optimization': True,
                'coreml_optimization': True
            }
        elif gpu_cores >= 8 and memory_gb >= 16:
            profile = 'balanced'
            recommended_settings = {
                'max_batch_size': 8,
                'memory_allocation': 0.7,
                'gpu_utilization_target': 0.8,
                'neural_engine_enabled': True,
                'metal_performance_shaders': True,
                'mlx_optimization': True,
                'coreml_optimization': True
            }
        else:
            profile = 'efficiency'
            recommended_settings = {
                'max_batch_size': 4,
                'memory_allocation': 0.6,
                'gpu_utilization_target': 0.7,
                'neural_engine_enabled': neural_engine_cores > 0,
                'metal_performance_shaders': gpu_cores > 0,
                'mlx_optimization': system_info.get('apple_silicon', False),
                'coreml_optimization': system_info.get('apple_silicon', False)
            }
        
        return jsonify({
            'success': True,
            'data': {
                'profile': profile,
                'chip_name': chip_name,
                'recommended_settings': recommended_settings,
                'hardware_capabilities': {
                    'gpu_cores': gpu_cores,
                    'memory_gb': memory_gb,
                    'neural_engine_cores': neural_engine_cores,
                    'cpu_cores': optimization_profile.get('cpu_cores', 0)
                },
                'optimization_potential': _calculate_optimization_potential(optimization_profile)
            },
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting performance profile: {e}")
        return jsonify({'error': str(e)}), 500

@hardware_bp.route('/optimize-model', methods=['POST'])
def optimize_model():
    """Optimize a model for the current Apple Silicon hardware"""
    try:
        if not frameworks:
            return jsonify({'error': 'Apple frameworks integration not available'}), 500
        
        data = request.get_json()
        model_path = data.get('model_path')
        target_format = data.get('target_format', 'coreml')
        
        if not model_path:
            return jsonify({'error': 'model_path is required'}), 400
        
        # Perform optimization using enhanced Apple frameworks
        optimization_result = frameworks.optimize_model_for_apple_silicon(
            model_path=model_path,
            target_format=target_format
        )
        
        return jsonify({
            'success': optimization_result.success,
            'data': {
                'optimizations_applied': optimization_result.optimizations_applied,
                'performance_improvement': optimization_result.performance_improvement,
                'memory_reduction': optimization_result.memory_reduction,
                'error': optimization_result.error
            },
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error optimizing model: {e}")
        return jsonify({'error': str(e)}), 500

@hardware_bp.route('/benchmark', methods=['POST'])
def run_benchmark():
    """Run comprehensive hardware benchmark"""
    try:
        if not frameworks:
            return jsonify({'error': 'Apple frameworks integration not available'}), 500
        
        # Run full benchmark
        benchmark_results = frameworks.benchmark_performance()
        
        return jsonify({
            'success': True,
            'data': benchmark_results,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error running benchmark: {e}")
        return jsonify({'error': str(e)}), 500

def _calculate_optimization_potential(optimization_profile):
    """Calculate optimization potential based on hardware capabilities"""
    try:
        gpu_cores = optimization_profile.get('gpu_cores', 0)
        neural_engine_cores = optimization_profile.get('neural_engine_cores', 0)
        memory_gb = optimization_profile.get('memory_gb', 0)
        
        # Calculate potential based on hardware capabilities
        gpu_potential = min(gpu_cores * 2.5, 100)  # GPU cores contribute significantly
        neural_potential = min(neural_engine_cores * 5, 100)  # Neural Engine is highly optimized
        memory_potential = min(memory_gb * 2, 100)  # More memory allows larger models
        
        overall_potential = (gpu_potential + neural_potential + memory_potential) / 3
        
        return {
            'overall_score': round(overall_potential, 1),
            'gpu_optimization_potential': round(gpu_potential, 1),
            'neural_engine_potential': round(neural_potential, 1),
            'memory_optimization_potential': round(memory_potential, 1),
            'recommendations': _get_optimization_recommendations(optimization_profile)
        }
    
    except Exception as e:
        logging.error(f"Error calculating optimization potential: {e}")
        return {'overall_score': 0, 'error': str(e)}

def _get_optimization_recommendations(optimization_profile):
    """Get specific optimization recommendations"""
    recommendations = []
    
    gpu_cores = optimization_profile.get('gpu_cores', 0)
    neural_engine_cores = optimization_profile.get('neural_engine_cores', 0)
    memory_gb = optimization_profile.get('memory_gb', 0)
    
    if neural_engine_cores > 0:
        recommendations.append("Enable Neural Engine acceleration for AI workloads")
    
    if gpu_cores >= 16:
        recommendations.append("Use Metal Performance Shaders for GPU acceleration")
    
    if memory_gb >= 32:
        recommendations.append("Enable unified memory optimization for large models")
    
    if optimization_profile.get('mlx_enabled'):
        recommendations.append("Use MLX framework for optimal Apple Silicon performance")
    
    if optimization_profile.get('neural_engine_enabled'):
        recommendations.append("Apply Core ML quantization for Neural Engine compatibility")
    
    return recommendations

# Background metrics updater
def start_metrics_updater():
    """Start background thread to update metrics cache"""
    def updater():
        while True:
            try:
                update_metrics_cache()
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                logging.error(f"Metrics updater error: {e}")
                time.sleep(5)  # Wait longer on error
    
    thread = threading.Thread(target=updater, daemon=True)
    thread.start()
    logging.info("Enhanced background metrics updater started")

# Start the background updater when module is imported
start_metrics_updater()
