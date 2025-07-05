#!/usr/bin/env python3
"""
Integrated MLX Manager with Apple Frameworks Integration
Combines MLX functionality with Core ML, Metal, and Neural Engine optimization
"""

import os
import json
import time
import threading
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

# Import our Apple frameworks integration
from gerdsen_ai_server.src.enhanced_apple_frameworks_integration import (
    EnhancedAppleFrameworksIntegration
)
from gerdsen_ai_server.src.enhanced_apple_silicon_detector import (
    EnhancedAppleSiliconDetector
)
from gerdsen_ai_server.src.dummy_model_loader import load_dummy_model, dummy_predict
from gerdsen_ai_server.src.model_loaders import GGUFLoader, SafeTensorsLoader, MLXLoader, CoreMLLoader
from gerdsen_ai_server.src.inference import GGUFInferenceEngine, GenerationConfig

# MLX imports
try:
    import mlx.core as mx
    import mlx.nn as nn
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    print("MLX not available - using fallback mode")

# NumPy for data handling
import numpy as np

# Define missing enums and classes
from enum import Enum

class ModelFormat(Enum):
    """Model format enumeration"""
    MLX = "mlx"
    COREML = "coreml"
    ONNX = "onnx"
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"

class ComputeDevice(Enum):
    """Compute device enumeration"""
    CPU = "cpu"
    GPU = "gpu"
    NEURAL_ENGINE = "neural_engine"
    AUTO = "auto"

class ThermalState(Enum):
    """Thermal state enumeration"""
    NOMINAL = "nominal"
    FAIR = "fair"
    SERIOUS = "serious"
    CRITICAL = "critical"

class PowerState(Enum):
    """Power state enumeration"""
    HIGH_PERFORMANCE = "high_performance"
    BALANCED = "balanced"
    LOW_POWER = "low_power"
    BATTERY_SAVER = "battery_saver"
    LOW_BATTERY = "low_battery"

@dataclass
class PerformanceMetrics:
    """Performance metrics for models"""
    inference_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    throughput_tokens_per_sec: float = 0.0
    accuracy: float = 0.0

@dataclass
class IntegratedModelInfo:
    """Enhanced model information with Apple frameworks integration"""
    model_id: str
    name: str
    path: str
    framework: ModelFormat
    compute_device: ComputeDevice
    size_bytes: int
    parameters: int
    quantization: str
    optimization_level: str
    performance_metrics: Optional[PerformanceMetrics]
    apple_silicon_optimized: bool
    neural_engine_compatible: bool
    metal_accelerated: bool
    last_accessed: float
    access_count: int

class IntegratedMLXManager:
    """MLX Manager with full Apple frameworks integration"""
    
    def __init__(self, cache_dir: str = None, apple_detector=None, frameworks=None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize Apple frameworks integration
        self.apple_frameworks = frameworks
        
        # Initialize Apple Silicon detector
        self.silicon_detector = apple_detector
        
        # Model management
        self.models = {}
        self.model_cache = {}
        self.performance_history = {}
        
        # Model loaders
        self.gguf_loader = GGUFLoader()
        self.safetensors_loader = SafeTensorsLoader()
        self.mlx_loader = MLXLoader()
        self.coreml_loader = CoreMLLoader()
        
        # Inference engines
        self.gguf_inference = GGUFInferenceEngine()
        
        # Configuration
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.gerdsen_ai/model_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Optimization settings
        self.auto_optimization = True
        self.thermal_throttling = True
        self.power_management = True
        
        # Start Apple Silicon monitoring
        self.silicon_detector.start_monitoring()
        
        # Register optimization callbacks
        self.silicon_detector.register_optimization_callback(self._handle_performance_optimization)
        self.silicon_detector.register_thermal_callback(self._handle_thermal_event)
        self.silicon_detector.register_power_callback(self._handle_power_event)
        
        self.logger.info("Integrated MLX Manager initialized with Apple frameworks")
        self._load_models_from_config()
    
    def _load_models_from_config(self, config_dir: str = "config/models"):
        """Load all models from the specified configuration directory."""
        config_path = Path(config_dir)
        if not config_path.exists():
            self.logger.warning(f"Model configuration directory not found: {config_dir}")
            return

        for filename in os.listdir(config_path):
            if filename.endswith(".json"):
                file_path = os.path.join(config_path, filename)
                with open(file_path, "r") as f:
                    try:
                        model_config = json.load(f)
                        self.load_model(
                            model_path=model_config["path"],
                            model_name=model_config["display_name"],
                            framework=model_config["framework"],
                        )
                    except json.JSONDecodeError:
                        self.logger.error(f"Invalid JSON in model config: {file_path}")
                    except KeyError as e:
                        self.logger.error(f"Missing key in model config {file_path}: {e}")

    def load_model(self, 
                   model_path: str, 
                   model_name: str = None,
                   framework: str = 'auto',
                   compute_device: ComputeDevice = ComputeDevice.AUTO,
                   optimize_for_apple_silicon: bool = True) -> Optional[str]:
        """Load a model with Apple frameworks integration"""
        
        try:
            if not model_name:
                model_name = os.path.basename(model_path)
            
            # Determine optimal compute device based on current system state
            if compute_device == ComputeDevice.AUTO:
                compute_device = self._determine_optimal_device(model_path)
            
            # Detect model format and load accordingly
            if model_path.lower().endswith('.gguf'):
                # Load GGUF model
                try:
                    model_data = self.gguf_loader.load_model(model_path, model_name)
                    model_load_result = {
                        "status": "loaded",
                        "format": "gguf",
                        "size_bytes": model_data['info'].model_size,
                        "parameters": f"{model_data['info'].n_layers}L-{model_data['info'].n_heads}H",
                        "quantization": model_data['info'].quantization,
                        "context_length": model_data['info'].context_length,
                        "capabilities": model_data['capabilities']
                    }
                    model_id = model_data['id']
                    self.model_cache[model_id] = {"path": model_path, "loader": "gguf", "data": model_data}
                    
                    # Load model into inference engine
                    inference_success = self.gguf_inference.load_model_for_inference(
                        model_id, model_path, model_data['info'].__dict__
                    )
                    if not inference_success:
                        self.logger.error(f"Failed to load GGUF model into inference engine")
                        return None
                        
                except Exception as e:
                    self.logger.error(f"Failed to load GGUF model: {e}")
                    return None
                    
            elif model_path.lower().endswith('.safetensors'):
                # Load SafeTensors model
                try:
                    model_info = self.safetensors_loader.load_model(model_path)
                    model_load_result = {
                        "status": "loaded",
                        "format": "safetensors",
                        "size_bytes": model_info['file_size'],
                        "parameters": model_info['total_parameters'],
                        "architecture": model_info['architecture'],
                        "num_tensors": model_info['num_tensors'],
                        "capabilities": ["text-generation"]  # Default for now
                    }
                    model_id = Path(model_path).stem
                    self.model_cache[model_id] = {"path": model_path, "loader": "safetensors", "data": model_info}
                    
                    # TODO: Implement SafeTensors inference engine
                    self.logger.info(f"SafeTensors model loaded successfully: {model_id}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to load SafeTensors model: {e}")
                    return None
                    
            elif model_path.lower().endswith(('.mlx', '.npz')):
                # Load MLX model
                try:
                    model_info = self.mlx_loader.load_model(model_path)
                    model_load_result = {
                        "status": "loaded",
                        "format": "mlx",
                        "size_bytes": model_info['file_size'],
                        "parameters": model_info['total_parameters'],
                        "architecture": model_info['architecture'],
                        "device": model_info['device'],
                        "optimized_for": model_info['optimized_for'],
                        "capabilities": ["text-generation", "apple-silicon-optimized"]
                    }
                    model_id = Path(model_path).stem
                    self.model_cache[model_id] = {"path": model_path, "loader": "mlx", "data": model_info}
                    
                    # Apply device-specific optimizations
                    if self.silicon_detector and optimize_for_apple_silicon:
                        device_profile = {
                            'gpu_cores': self.silicon_detector.chip_info.get('specifications', {}).get('gpu_cores', 0),
                            'neural_engine_cores': self.silicon_detector.chip_info.get('specifications', {}).get('neural_engine_cores', 0),
                            'memory_gb': self.silicon_detector.chip_info.get('detected_memory_gb', 0)
                        }
                        self.mlx_loader.optimize_for_device(model_id, device_profile)
                    
                    self.logger.info(f"MLX model loaded successfully: {model_id}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to load MLX model: {e}")
                    return None
                    
            elif model_path.lower().endswith(('.mlmodel', '.mlpackage')):
                # Load CoreML model
                try:
                    model_info = self.coreml_loader.load_model(model_path)
                    model_load_result = {
                        "status": "loaded",
                        "format": "coreml",
                        "size_bytes": model_info['file_size'],
                        "model_type": model_info['model_type'],
                        "inputs": model_info['inputs'],
                        "outputs": model_info['outputs'],
                        "compute_units": model_info['compute_units'],
                        "capabilities": ["inference", "ios-compatible", "macos-compatible"]
                    }
                    model_id = Path(model_path).stem
                    self.model_cache[model_id] = {"path": model_path, "loader": "coreml", "data": model_info}
                    
                    # Optimize for available compute units
                    if optimize_for_apple_silicon and 'neural_engine' in model_info['compute_units']:
                        self.coreml_loader.optimize_for_device(model_id, 'NEURAL_ENGINE')
                    elif 'gpu' in model_info['compute_units']:
                        self.coreml_loader.optimize_for_device(model_id, 'GPU')
                    
                    self.logger.info(f"CoreML model loaded successfully: {model_id}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to load CoreML model: {e}")
                    return None
                    
            else:
                # Load using dummy loader for other formats
                model_load_result = load_dummy_model(model_path)
                if model_load_result["status"] != "loaded":
                    self.logger.error(f"Failed to load dummy model: {model_path}")
                    return None
                model_id = model_name
                self.model_cache[model_id] = {"path": model_path, "loader": "dummy"}
            
            # Determine framework from load result if available
            result_framework = model_load_result.get("format", framework)
            
            # Get model information with additional metadata from load result
            model_info = self._create_integrated_model_info(
                model_id, 
                model_name, 
                model_path, 
                result_framework, 
                compute_device,
                size_bytes=model_load_result.get("size_bytes", 0),
                parameters=model_load_result.get("parameters", 0),
                quantization=model_load_result.get("quantization", "unknown")
            )
            
            # Apply Apple Silicon optimizations
            if optimize_for_apple_silicon and self.silicon_detector.is_apple_silicon:
                optimization_success = self.apple_frameworks.optimize_model(model_id)
                model_info.apple_silicon_optimized = optimization_success
                
                if optimization_success:
                    self.logger.info(f"Applied Apple Silicon optimizations to {model_id}")
            
            # Store model information
            self.models[model_id] = model_info
            
            # Run initial performance benchmark
            self._benchmark_model_performance(model_id)
            
            self.logger.info(f"Successfully loaded model: {model_id}")
            return model_id
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_path}: {e}")
            return None
    
    def _determine_optimal_device(self, model_path: str) -> ComputeDevice:
        """Determine optimal compute device based on system state and model characteristics"""
        
        try:
            # Get current system metrics
            metrics = self.silicon_detector.get_real_time_metrics()
            
            # Check thermal state
            if self.silicon_detector.current_thermal_state in [
                ThermalState.SERIOUS,
                ThermalState.CRITICAL,
            ]:
                # Use Neural Engine for cooler operation
                return ComputeDevice.NEURAL_ENGINE
            
            # Check power state
            if self.silicon_detector.current_power_state == PowerState.LOW_BATTERY:
                # Use Neural Engine for power efficiency
                return ComputeDevice.NEURAL_ENGINE
            
            # Check memory pressure
            memory_pressure = metrics.get('memory', {}).get('pressure', 'normal')
            if memory_pressure in ['urgent', 'critical']:
                # Use Neural Engine for lower memory usage
                return ComputeDevice.NEURAL_ENGINE
            
            # Check model characteristics
            model_size = os.path.getsize(model_path) if os.path.exists(model_path) else 0
            
            # Large models (>1GB) prefer GPU
            if model_size > 1024 * 1024 * 1024:
                return ComputeDevice.GPU
            
            # Medium models prefer Neural Engine
            if model_size > 100 * 1024 * 1024:
                return ComputeDevice.NEURAL_ENGINE
            
            # Small models can use AUTO
            return ComputeDevice.AUTO
            
        except Exception as e:
            self.logger.warning(f"Failed to determine optimal device: {e}")
            return ComputeDevice.AUTO
    
    def _create_integrated_model_info(self, 
                                    model_id: str, 
                                    model_name: str, 
                                    model_path: str,
                                    framework: str,
                                    compute_device: ComputeDevice,
                                    size_bytes: int = 0,
                                    parameters: int = 0,
                                    quantization: str = "unknown") -> IntegratedModelInfo:
        """Create integrated model information with provided metadata"""
        
        try:
            # Get file size from provided value or fallback to actual file size
            actual_size = size_bytes if size_bytes > 0 else (os.path.getsize(model_path) if os.path.exists(model_path) else 0)
            
            # Determine framework
            if framework == 'auto':
                if model_path.endswith('.mlpackage') or model_path.endswith('.mlmodel'):
                    framework_enum = ModelFormat.COREML
                elif model_path.endswith('.npz') or 'mlx' in model_path.lower():
                    framework_enum = ModelFormat.MLX
                elif model_path.endswith('.gguf'):
                    framework_enum = ModelFormat.MLX  # GGUF models can use MLX backend
                else:
                    framework_enum = ModelFormat.COREML
            else:
                framework_enum = ModelFormat(framework)
            
            # Check Neural Engine compatibility
            neural_engine_compatible = (
                framework_enum in [ModelFormat.COREML, ModelFormat.MLX] and
                self.silicon_detector.is_apple_silicon
            )
            
            # Check Metal acceleration
            metal_accelerated = (
                compute_device in [ComputeDevice.GPU, ComputeDevice.AUTO] and
                self.apple_frameworks.metal_manager.available
            )
            
            return IntegratedModelInfo(
                model_id=model_id,
                name=model_name,
                path=model_path,
                framework=framework_enum,
                compute_device=compute_device,
                size_bytes=actual_size,
                parameters=parameters,
                quantization=quantization,
                optimization_level="default",
                performance_metrics=None,
                apple_silicon_optimized=False,
                neural_engine_compatible=neural_engine_compatible,
                metal_accelerated=metal_accelerated,
                last_accessed=time.time(),
                access_count=0
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create model info: {e}")
            return None
    
    def predict(self, model_id: str, input_data: Any, **kwargs) -> Optional[Any]:
        """Run prediction with integrated Apple frameworks optimization"""
        
        try:
            if model_id not in self.models:
                self.logger.error(f"Model {model_id} not found")
                return None
            
            model_info = self.models[model_id]
            
            # Update access statistics
            model_info.last_accessed = time.time()
            model_info.access_count += 1
            
            # Check system state and adjust if needed
            self._adjust_for_system_state(model_id)
            
            # Check if this is a GGUF model and handle accordingly
            cache_data = self.model_cache.get(model_id, {})
            if cache_data.get("loader") == "gguf":
                # Use GGUF inference engine for chat/completions
                if "messages" in input_data:
                    # Chat completion request
                    messages = input_data.get("messages", [])
                    stream = kwargs.get("stream", False)
                    
                    # Create generation config from kwargs
                    config = GenerationConfig(
                        max_tokens=kwargs.get("max_tokens", 512),
                        temperature=kwargs.get("temperature", 0.7),
                        top_p=kwargs.get("top_p", 0.9),
                        stream=stream
                    )
                    
                    # Generate response
                    response = self.gguf_inference.create_chat_completion(
                        model_id, messages, config, stream
                    )
                    
                    # For non-streaming, extract the content for backward compatibility
                    if not stream and isinstance(response, dict):
                        content = response['choices'][0]['message']['content']
                        return {
                            'content': content,
                            'prompt_tokens': response['usage']['prompt_tokens'],
                            'completion_tokens': response['usage']['completion_tokens'],
                            'total_tokens': response['usage']['total_tokens']
                        }
                    
                    return response
                    
                elif "prompt" in input_data:
                    # Text completion request
                    prompt = input_data.get("prompt", "")
                    config = GenerationConfig(
                        max_tokens=kwargs.get("max_tokens", 512),
                        temperature=kwargs.get("temperature", 0.7),
                        top_p=kwargs.get("top_p", 0.9)
                    )
                    
                    result = self.gguf_inference.generate(model_id, prompt, config)
                    
                    return {
                        'text': result.text,
                        'prompt_tokens': len(prompt.split()),
                        'completion_tokens': result.tokens_generated,
                        'total_tokens': len(prompt.split()) + result.tokens_generated
                    }
            
            # Fall back to dummy predict for non-GGUF models
            start_time = time.time()
            result = dummy_predict(input_data)
            inference_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Update performance metrics
            self._update_performance_metrics(model_id, inference_time)
            
            self.logger.debug(f"Prediction completed for {model_id} in {inference_time:.2f}ms")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Prediction failed for {model_id}: {e}")
            return None
    
    def _adjust_for_system_state(self, model_id: str):
        """Adjust model execution based on current system state"""
        
        try:
            model_info = self.models[model_id]
            current_metrics = self.silicon_detector.get_real_time_metrics()
            
            # Thermal management
            if self.thermal_throttling and self.silicon_detector.current_thermal_state == ThermalState.SERIOUS:
                # Reduce inference frequency or switch to more efficient device
                self.logger.info(f"Thermal throttling active for {model_id}")
                # Implementation would adjust model parameters here
            
            # Power management
            if self.power_management and self.silicon_detector.current_power_state == PowerState.LOW_BATTERY:
                # Switch to power-efficient mode
                self.logger.info(f"Power saving mode active for {model_id}")
                # Implementation would adjust model parameters here
            
            # Memory management
            memory_pressure = current_metrics.get('memory', {}).get('pressure', 'normal')
            if memory_pressure in ['urgent', 'critical']:
                # Free up memory or reduce model precision
                self.logger.info(f"Memory pressure management for {model_id}")
                # Implementation would adjust memory usage here
                
        except Exception as e:
            self.logger.warning(f"Failed to adjust for system state: {e}")
    
    def _benchmark_model_performance(self, model_id: str):
        """Benchmark model performance with Apple frameworks"""
        
        try:
            if model_id not in self.models:
                return
            
            self.logger.info(f"Benchmarking model performance: {model_id}")
            
            # Run benchmark using Apple frameworks
            benchmark_result = self.apple_frameworks.benchmark_performance(model_id, num_iterations=10)
            
            if 'error' not in benchmark_result:
                # Create performance metrics
                performance_metrics = PerformanceMetrics(
                    inference_time_ms=benchmark_result['average_inference_time_ms'],
                    memory_usage_mb=0.0,  # Would be measured in real implementation
                    throughput_tokens_per_sec=benchmark_result['throughput_inferences_per_sec'],
                )
                
                # Update model info
                self.models[model_id].performance_metrics = performance_metrics
                
                # Store in performance history
                self.performance_history[model_id] = benchmark_result
                
                self.logger.info(f"Benchmark completed for {model_id}: {benchmark_result['average_inference_time_ms']:.2f}ms")
            
        except Exception as e:
            self.logger.error(f"Benchmarking failed for {model_id}: {e}")
    
    def _update_performance_metrics(self, model_id: str, inference_time_ms: float):
        """Update performance metrics for a model"""
        
        try:
            if model_id not in self.models:
                return
            
            model_info = self.models[model_id]
            
            if model_info.performance_metrics:
                # Update existing metrics with exponential moving average
                alpha = 0.1  # Smoothing factor
                current_metrics = model_info.performance_metrics
                
                current_metrics.inference_time_ms = (
                    alpha * inference_time_ms + 
                    (1 - alpha) * current_metrics.inference_time_ms
                )
                
                current_metrics.throughput_ops_per_sec = (
                    1000 / current_metrics.inference_time_ms 
                    if current_metrics.inference_time_ms > 0 else 0
                )
            else:
                # Create new metrics
                model_info.performance_metrics = PerformanceMetrics(
                    inference_time_ms=inference_time_ms,
                    memory_usage_mb=0.0,
                    throughput_ops_per_sec=1000 / inference_time_ms if inference_time_ms > 0 else 0,
                    energy_efficiency_score=0.0,
                    device_utilization_percent=0.0
                )
                
        except Exception as e:
            self.logger.warning(f"Failed to update performance metrics: {e}")
    
    def _handle_performance_optimization(self, metrics: Dict[str, Any]):
        """Handle performance optimization callback from Apple Silicon detector"""
        
        try:
            # Check if any models need optimization
            cpu_usage = metrics.get('cpu', {}).get('usage_percent_total', 0)
            memory_usage = metrics.get('memory', {}).get('usage_percent', 0)
            
            if cpu_usage > 80 or memory_usage > 85:
                # Apply optimizations to loaded models
                for model_id in self.models:
                    if self.auto_optimization:
                        self._optimize_model_for_current_state(model_id, metrics)
                        
        except Exception as e:
            self.logger.error(f"Performance optimization callback failed: {e}")
    
    def _handle_thermal_event(self, thermal_state: ThermalState, metrics: Dict[str, Any]):
        """Handle thermal event callback"""
        
        try:
            if thermal_state in [ThermalState.HOT, ThermalState.THROTTLED]:
                self.logger.warning(f"Thermal event: {thermal_state.value}")
                
                # Reduce model performance to cool down
                for model_id in self.models:
                    self._apply_thermal_throttling(model_id)
                    
        except Exception as e:
            self.logger.error(f"Thermal event callback failed: {e}")
    
    def _handle_power_event(self, power_state: PowerState, metrics: Dict[str, Any]):
        """Handle power event callback"""
        
        try:
            if power_state == PowerState.LOW_BATTERY:
                self.logger.info("Low battery detected - enabling power saving mode")
                
                # Switch models to power-efficient mode
                for model_id in self.models:
                    self._apply_power_saving(model_id)
                    
        except Exception as e:
            self.logger.error(f"Power event callback failed: {e}")
    
    def _optimize_model_for_current_state(self, model_id: str, metrics: Dict[str, Any]):
        """Optimize model based on current system state"""
        
        try:
            # This would implement dynamic optimization based on system metrics
            self.logger.debug(f"Optimizing {model_id} for current system state")
            
            # Example optimizations:
            # - Switch compute device based on load
            # - Adjust batch size based on memory
            # - Change precision based on thermal state
            
        except Exception as e:
            self.logger.warning(f"Model optimization failed for {model_id}: {e}")
    
    def _apply_thermal_throttling(self, model_id: str):
        """Apply thermal throttling to a model"""
        
        try:
            self.logger.debug(f"Applying thermal throttling to {model_id}")
            
            # Implementation would:
            # - Reduce inference frequency
            # - Switch to more efficient compute device
            # - Lower model precision
            
        except Exception as e:
            self.logger.warning(f"Thermal throttling failed for {model_id}: {e}")
    
    def _apply_power_saving(self, model_id: str):
        """Apply power saving optimizations to a model"""
        
        try:
            self.logger.debug(f"Applying power saving to {model_id}")
            
            # Implementation would:
            # - Switch to Neural Engine for efficiency
            # - Reduce model precision
            # - Batch multiple requests
            
        except Exception as e:
            self.logger.warning(f"Power saving failed for {model_id}: {e}")
    
    def get_model_info(self, model_id: str) -> Optional[IntegratedModelInfo]:
        """Get comprehensive model information"""
        return self.models.get(model_id)
    
    def list_models(self) -> List[str]:
        """List all loaded models"""
        return list(self.models.keys())
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        try:
            # Get Apple Silicon detector info
            silicon_info = self.silicon_detector.get_comprehensive_info()
            
            # Get Apple frameworks status
            frameworks_status = self.apple_frameworks.get_framework_status()
            
            # Get model statistics
            model_stats = {
                'total_models': len(self.models),
                'models_by_framework': {},
                'models_by_device': {},
                'total_memory_usage': 0
            }
            
            for model_info in self.models.values():
                framework = model_info.framework.value
                device = model_info.compute_device.value
                
                model_stats['models_by_framework'][framework] = model_stats['models_by_framework'].get(framework, 0) + 1
                model_stats['models_by_device'][device] = model_stats['models_by_device'].get(device, 0) + 1
                model_stats['total_memory_usage'] += model_info.size_bytes
            
            return {
                'apple_silicon': silicon_info,
                'frameworks': frameworks_status,
                'models': model_stats,
                'performance_history': self.performance_history,
                'optimization_settings': {
                    'auto_optimization': self.auto_optimization,
                    'thermal_throttling': self.thermal_throttling,
                    'power_management': self.power_management
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {}
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations"""
        
        recommendations = []
        
        try:
            # Get Apple frameworks recommendations
            framework_recommendations = self.apple_frameworks.get_performance_recommendations()
            recommendations.extend(framework_recommendations)
            
            # Get Apple Silicon recommendations
            silicon_recommendations = self.silicon_detector.get_optimization_recommendations()
            recommendations.extend(silicon_recommendations)
            
            # Add model-specific recommendations
            for model_id, model_info in self.models.items():
                if model_info.performance_metrics:
                    metrics = model_info.performance_metrics
                    
                    # Slow inference recommendation
                    if metrics.inference_time_ms > 1000:  # > 1 second
                        recommendations.append({
                            'category': 'model_performance',
                            'priority': 'medium',
                            'title': f'Slow Inference: {model_info.name}',
                            'description': f'Model {model_id} has slow inference time ({metrics.inference_time_ms:.0f}ms)',
                            'actions': [
                                'Consider model quantization',
                                'Switch to Neural Engine',
                                'Optimize model architecture'
                            ]
                        })
                    
                    # Low utilization recommendation
                    if model_info.access_count < 5 and (time.time() - model_info.last_accessed) > 3600:  # Not used in last hour
                        recommendations.append({
                            'category': 'resource_management',
                            'priority': 'low',
                            'title': f'Unused Model: {model_info.name}',
                            'description': f'Model {model_id} has not been used recently',
                            'actions': [
                                'Consider unloading to free memory',
                                'Move to cold storage'
                            ]
                        })
            
        except Exception as e:
            self.logger.error(f"Failed to get optimization recommendations: {e}")
        
        return recommendations
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        
        try:
            if model_id not in self.models:
                return False
            
            # Check if it's a GGUF model
            cache_data = self.model_cache.get(model_id, {})
            if cache_data.get("loader") == "gguf":
                # Unload GGUF model from both loader and inference engine
                loader_success = self.gguf_loader.unload_model(model_id)
                inference_success = self.gguf_inference.unload_model(model_id)
                success = loader_success and inference_success
            else:
                # Unload from Apple frameworks
                success = False
                if model_id in self.apple_frameworks.coreml_manager.models:
                    success = self.apple_frameworks.coreml_manager.unload_model(model_id)
                elif model_id in self.apple_frameworks.mlx_manager.models:
                    del self.apple_frameworks.mlx_manager.models[model_id]
                    success = True
            
            if success:
                # Remove from our tracking
                del self.models[model_id]
                if model_id in self.model_cache:
                    del self.model_cache[model_id]
                if model_id in self.performance_history:
                    del self.performance_history[model_id]
                
                self.logger.info(f"Unloaded model: {model_id}")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload model {model_id}: {e}")
        
        return False
    
    def get_gguf_models(self) -> Dict[str, Any]:
        """Get all loaded GGUF models"""
        gguf_models = {}
        for model_id, cache_data in self.model_cache.items():
            if cache_data.get("loader") == "gguf":
                model_info = self.models.get(model_id)
                if model_info:
                    gguf_models[model_id] = {
                        'info': model_info,
                        'data': cache_data.get('data', {}),
                        'capabilities': cache_data.get('data', {}).get('capabilities', [])
                    }
        return gguf_models
    
    def get_loaded_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded models with their information"""
        loaded_models = {}
        for model_id, model_info in self.models.items():
            cache_data = self.model_cache.get(model_id, {})
            loaded_models[model_id] = {
                'name': model_info.name,
                'framework': model_info.framework.value,
                'quantization': model_info.quantization,
                'size_gb': model_info.size_bytes / (1024**3),
                'parameters': model_info.parameters,
                'loader': cache_data.get('loader', 'unknown'),
                'capabilities': cache_data.get('data', {}).get('capabilities', []),
                'optimization_level': model_info.optimization_level,
                'apple_silicon_optimized': model_info.apple_silicon_optimized,
                'compute_device': model_info.compute_device.value
            }
        return loaded_models
    
    def cleanup(self):
        """Clean up resources"""
        
        try:
            # Stop monitoring
            self.silicon_detector.stop_monitoring()
            
            # Unload all models
            for model_id in list(self.models.keys()):
                self.unload_model(model_id)
            
            # Clean up Apple frameworks
            self.apple_frameworks.cleanup()
            
            self.logger.info("Integrated MLX Manager cleaned up")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

def main():
    """Demonstration of Integrated MLX Manager"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🚀 Integrated MLX Manager with Apple Frameworks Demo")
    print("=" * 60)
    
    # Initialize manager
    manager = IntegratedMLXManager()
    
    # Show system status
    print("\n📊 System Status:")
    status = manager.get_system_status()
    
    apple_silicon = status.get('apple_silicon', {})
    if apple_silicon.get('detection', {}).get('is_apple_silicon'):
        chip_info = apple_silicon['detection']['chip_info']
        print(f"   Chip: {chip_info['chip_name']}")
        print(f"   Memory: {chip_info['detected_memory_gb']}GB")
    
    frameworks = status.get('frameworks', {})
    print(f"   Core ML: {'✅' if frameworks.get('coreml', {}).get('available') else '❌'}")
    print(f"   MLX: {'✅' if frameworks.get('mlx', {}).get('available') else '❌'}")
    print(f"   Metal: {'✅' if frameworks.get('metal', {}).get('available') else '❌'}")
    
    # Create demo models
    print("\n🔧 Creating demo models...")
    demo_models = manager.apple_frameworks.create_demo_models()
    
    for demo_name, model_id in demo_models.items():
        print(f"   Created {demo_name}: {model_id}")
        
        # Get model info
        model_info = manager.get_model_info(model_id)
        if model_info:
            print(f"      Framework: {model_info.framework.value}")
            print(f"      Device: {model_info.compute_device.value}")
            print(f"      Apple Silicon Optimized: {model_info.apple_silicon_optimized}")
    
    # Show optimization recommendations
    print("\n💡 Optimization Recommendations:")
    recommendations = manager.get_optimization_recommendations()
    
    for rec in recommendations[:5]:  # Show top 5
        priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(rec['priority'], '⚪')
        print(f"   {priority_emoji} {rec['title']}")
        print(f"      {rec['description']}")
    
    # Cleanup
    manager.cleanup()
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    main()
