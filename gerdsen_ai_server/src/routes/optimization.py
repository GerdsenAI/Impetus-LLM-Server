#!/usr/bin/env python3
"""
Optimization API Routes
Provides Apple Silicon optimization and framework integration endpoints
"""

from flask import Blueprint, jsonify, request
import logging
import time
import os
from typing import Dict, Any
from src.apple_frameworks_integration import AppleFrameworksIntegration

optimization_bp = Blueprint('optimization', __name__)

# Global integration instance
frameworks_integration = None

def initialize_integration():
    """Initialize the Apple frameworks integration"""
    global frameworks_integration
    if frameworks_integration is None:
        frameworks_integration = AppleFrameworksIntegration()
        logging.info("Apple frameworks integration initialized")

# Initialize on module load
initialize_integration()

@optimization_bp.route('/capabilities', methods=['GET'])
def get_capabilities():
    """Get Apple frameworks capabilities"""
    try:
        if not frameworks_integration:
            return jsonify({'error': 'Frameworks integration not available'}), 500
        
        capabilities = frameworks_integration.capabilities
        
        return jsonify({
            'success': True,
            'data': {
                'coreml_available': capabilities.coreml_available,
                'mlx_available': capabilities.mlx_available,
                'mps_available': capabilities.mps_available,
                'neural_engine_available': capabilities.neural_engine_available,
                'metal_gpu_available': capabilities.metal_gpu_available,
                'unified_memory': capabilities.unified_memory,
                'platform': capabilities.platform
            },
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting capabilities: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/profiles', methods=['GET'])
def get_optimization_profiles():
    """Get available optimization profiles"""
    try:
        if not frameworks_integration:
            return jsonify({'error': 'Frameworks integration not available'}), 500
        
        profiles = {}
        for name, profile in frameworks_integration.optimization_profiles.items():
            profiles[name] = {
                'framework': profile.framework,
                'device': profile.device,
                'memory_allocation': profile.memory_allocation,
                'batch_size': profile.batch_size,
                'precision': profile.precision,
                'neural_engine_enabled': profile.neural_engine_enabled,
                'metal_enabled': profile.metal_enabled
            }
        
        return jsonify({
            'success': True,
            'data': profiles,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting optimization profiles: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/optimal-profile', methods=['GET'])
def get_optimal_profile():
    """Get optimal optimization profile for given requirements"""
    try:
        if not frameworks_integration:
            return jsonify({'error': 'Frameworks integration not available'}), 500
        
        model_type = request.args.get('model_type', 'general')
        performance_priority = request.args.get('performance_priority', 'balanced')
        
        profile = frameworks_integration.get_optimal_profile(model_type, performance_priority)
        
        return jsonify({
            'success': True,
            'data': {
                'framework': profile.framework,
                'device': profile.device,
                'memory_allocation': profile.memory_allocation,
                'batch_size': profile.batch_size,
                'precision': profile.precision,
                'neural_engine_enabled': profile.neural_engine_enabled,
                'metal_enabled': profile.metal_enabled,
                'model_type': model_type,
                'performance_priority': performance_priority
            },
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting optimal profile: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/optimize-model', methods=['POST'])
def optimize_model():
    """Optimize a model for Apple Silicon"""
    try:
        if not frameworks_integration:
            return jsonify({'error': 'Frameworks integration not available'}), 500
        
        data = request.get_json()
        if not data or 'model_path' not in data:
            return jsonify({'error': 'Model path is required'}), 400
        
        model_path = data['model_path']
        output_path = data.get('output_path')
        target_profile = data.get('target_profile', 'auto')
        
        # Validate model path
        if not os.path.exists(model_path):
            return jsonify({'error': 'Model file not found'}), 404
        
        # Perform optimization
        start_time = time.time()
        results = frameworks_integration.optimize_model_for_apple_silicon(
            model_path, output_path, target_profile
        )
        optimization_time = time.time() - start_time
        
        results['optimization_time'] = optimization_time
        
        return jsonify({
            'success': results.get('success', False),
            'data': results,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error optimizing model: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/benchmark-model', methods=['POST'])
def benchmark_model():
    """Benchmark model performance on Apple Silicon"""
    try:
        if not frameworks_integration:
            return jsonify({'error': 'Frameworks integration not available'}), 500
        
        data = request.get_json()
        if not data or 'model_path' not in data:
            return jsonify({'error': 'Model path is required'}), 400
        
        model_path = data['model_path']
        profile_name = data.get('profile')
        
        # Validate model path
        if not os.path.exists(model_path):
            return jsonify({'error': 'Model file not found'}), 404
        
        # Get profile if specified
        profile = None
        if profile_name and profile_name in frameworks_integration.optimization_profiles:
            profile = frameworks_integration.optimization_profiles[profile_name]
        
        # Perform benchmark
        results = frameworks_integration.benchmark_model_performance(model_path, profile)
        
        return jsonify({
            'success': results.get('success', False),
            'data': results,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error benchmarking model: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/neural-engine', methods=['GET'])
def get_neural_engine_status():
    """Get Neural Engine utilization and status"""
    try:
        if not frameworks_integration:
            return jsonify({'error': 'Frameworks integration not available'}), 500
        
        neural_engine_info = frameworks_integration.get_neural_engine_utilization()
        
        return jsonify({
            'success': True,
            'data': neural_engine_info,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting Neural Engine status: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/metal-gpu', methods=['GET'])
def get_metal_gpu_status():
    """Get Metal GPU information and utilization"""
    try:
        if not frameworks_integration:
            return jsonify({'error': 'Frameworks integration not available'}), 500
        
        gpu_info = frameworks_integration.get_metal_gpu_info()
        
        return jsonify({
            'success': True,
            'data': gpu_info,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting Metal GPU status: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/recommendations', methods=['GET'])
def get_framework_recommendations():
    """Get framework recommendations based on use case"""
    try:
        if not frameworks_integration:
            return jsonify({'error': 'Frameworks integration not available'}), 500
        
        use_case = request.args.get('use_case', 'general')
        
        recommendations = frameworks_integration.get_framework_recommendations(use_case)
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/comprehensive-status', methods=['GET'])
def get_comprehensive_status():
    """Get comprehensive optimization and frameworks status"""
    try:
        if not frameworks_integration:
            return jsonify({'error': 'Frameworks integration not available'}), 500
        
        status = frameworks_integration.get_comprehensive_status()
        
        return jsonify({
            'success': True,
            'data': status,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting comprehensive status: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/memory-optimization', methods=['GET'])
def get_memory_optimization_info():
    """Get memory optimization information for unified memory architecture"""
    try:
        if not frameworks_integration:
            return jsonify({'error': 'Frameworks integration not available'}), 500
        
        capabilities = frameworks_integration.capabilities
        
        memory_info = {
            'unified_memory_available': capabilities.unified_memory,
            'optimization_strategies': [],
            'recommended_allocation': {},
            'memory_pressure_handling': {}
        }
        
        if capabilities.unified_memory:
            memory_info['optimization_strategies'] = [
                'Use 75% rule for memory allocation',
                'Leverage shared memory between CPU and GPU',
                'Minimize memory copies between devices',
                'Use memory mapping for large models'
            ]
            
            memory_info['recommended_allocation'] = {
                'model_weights': 0.6,  # 60% for model weights
                'activations': 0.15,   # 15% for activations
                'system_reserve': 0.25  # 25% for system and other processes
            }
            
            memory_info['memory_pressure_handling'] = {
                'monitor_pressure': True,
                'dynamic_batch_sizing': True,
                'model_quantization': True,
                'gradient_checkpointing': True
            }
        else:
            memory_info['optimization_strategies'] = [
                'Traditional CPU-GPU memory management',
                'Explicit memory transfers required',
                'Consider memory bandwidth limitations'
            ]
        
        return jsonify({
            'success': True,
            'data': memory_info,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting memory optimization info: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/performance-tuning', methods=['POST'])
def get_performance_tuning_suggestions():
    """Get performance tuning suggestions based on current system state"""
    try:
        if not frameworks_integration:
            return jsonify({'error': 'Frameworks integration not available'}), 500
        
        data = request.get_json() or {}
        current_performance = data.get('current_performance', {})
        target_metrics = data.get('target_metrics', {})
        
        suggestions = {
            'framework_optimizations': [],
            'hardware_optimizations': [],
            'model_optimizations': [],
            'system_optimizations': []
        }
        
        capabilities = frameworks_integration.capabilities
        
        # Framework-specific suggestions
        if capabilities.mlx_available:
            suggestions['framework_optimizations'].append({
                'type': 'mlx_optimization',
                'description': 'Use MLX for optimal Apple Silicon performance',
                'impact': 'high',
                'implementation': 'Convert models to MLX format'
            })
        
        if capabilities.coreml_available and capabilities.neural_engine_available:
            suggestions['framework_optimizations'].append({
                'type': 'neural_engine_optimization',
                'description': 'Leverage Neural Engine for inference',
                'impact': 'high',
                'implementation': 'Convert models to Core ML with ANE optimization'
            })
        
        # Hardware-specific suggestions
        if capabilities.metal_gpu_available:
            suggestions['hardware_optimizations'].append({
                'type': 'metal_acceleration',
                'description': 'Enable Metal GPU acceleration',
                'impact': 'medium',
                'implementation': 'Use Metal Performance Shaders for parallel operations'
            })
        
        if capabilities.unified_memory:
            suggestions['hardware_optimizations'].append({
                'type': 'unified_memory_optimization',
                'description': 'Optimize for unified memory architecture',
                'impact': 'high',
                'implementation': 'Reduce memory copies and use memory mapping'
            })
        
        # Model-specific suggestions
        suggestions['model_optimizations'] = [
            {
                'type': 'quantization',
                'description': 'Apply model quantization for reduced memory usage',
                'impact': 'medium',
                'implementation': 'Use float16 or int8 quantization'
            },
            {
                'type': 'pruning',
                'description': 'Remove unnecessary model parameters',
                'impact': 'medium',
                'implementation': 'Apply structured or unstructured pruning'
            },
            {
                'type': 'knowledge_distillation',
                'description': 'Create smaller, faster models',
                'impact': 'high',
                'implementation': 'Train smaller student models from larger teachers'
            }
        ]
        
        # System-specific suggestions
        suggestions['system_optimizations'] = [
            {
                'type': 'thermal_management',
                'description': 'Monitor and manage thermal throttling',
                'impact': 'medium',
                'implementation': 'Implement dynamic performance scaling'
            },
            {
                'type': 'memory_pressure',
                'description': 'Monitor memory pressure and adjust accordingly',
                'impact': 'high',
                'implementation': 'Implement dynamic batch size adjustment'
            },
            {
                'type': 'power_optimization',
                'description': 'Optimize for power efficiency',
                'impact': 'medium',
                'implementation': 'Use power-aware scheduling and frequency scaling'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': suggestions,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logging.error(f"Error getting performance tuning suggestions: {e}")
        return jsonify({'error': str(e)}), 500

