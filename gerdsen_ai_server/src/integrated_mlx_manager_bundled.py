#!/usr/bin/env python3
"""
Bundled version of Integrated MLX Manager
Handles import differences for bundled Electron environment
"""

import os
import json
import time
import threading
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

# Use bundled import helper
try:
    from bundled_import_helper import setup_bundled_imports
    modules, classes = setup_bundled_imports()
    
    # Extract the classes we need
    EnhancedAppleFrameworksIntegration = classes.get('EnhancedAppleFrameworksIntegration')
    EnhancedAppleSiliconDetector = classes.get('EnhancedAppleSiliconDetector')
    load_dummy_model = classes.get('load_dummy_model')
    dummy_predict = classes.get('dummy_predict')
    GGUFLoader = classes.get('GGUFLoader')
    SafeTensorsLoader = classes.get('SafeTensorsLoader')
    MLXLoader = classes.get('MLXLoader')
    CoreMLLoader = classes.get('CoreMLLoader')
    PyTorchLoader = classes.get('PyTorchLoader')
    ONNXLoader = classes.get('ONNXLoader')
    ModelLoaderFactory = classes.get('ModelLoaderFactory')
    LoaderModelFormat = classes.get('LoaderModelFormat')
    GGUFInferenceEngine = classes.get('GGUFInferenceEngine')
    GenerationConfig = classes.get('GenerationConfig')
    UnifiedInferenceEngine = classes.get('UnifiedInferenceEngine')
    get_unified_inference_engine = classes.get('get_unified_inference_engine')
    get_model_paths = classes.get('get_model_paths')
    get_model_search_paths = classes.get('get_model_search_paths')
    
except ImportError:
    # Fallback for direct imports
    logging.warning("Bundled import helper not available, trying direct imports")
    
    # Try direct imports as fallback
    try:
        from enhanced_apple_frameworks_integration import EnhancedAppleFrameworksIntegration
        from enhanced_apple_silicon_detector import EnhancedAppleSiliconDetector
        from dummy_model_loader import load_dummy_model, dummy_predict
        from model_loaders import (
            GGUFLoader, SafeTensorsLoader, MLXLoader, CoreMLLoader, PyTorchLoader, ONNXLoader,
            ModelLoaderFactory, ModelFormat as LoaderModelFormat
        )
        from inference import (
            GGUFInferenceEngine, GenerationConfig, 
            UnifiedInferenceEngine, get_unified_inference_engine
        )
        from config.model_paths import get_model_paths, get_model_search_paths
    except ImportError as e:
        logging.error(f"Failed to import required modules: {e}")
        # Set all to None for minimal functionality
        EnhancedAppleFrameworksIntegration = None
        EnhancedAppleSiliconDetector = None
        load_dummy_model = None
        dummy_predict = None
        GGUFLoader = None
        SafeTensorsLoader = None
        MLXLoader = None
        CoreMLLoader = None
        PyTorchLoader = None
        ONNXLoader = None
        ModelLoaderFactory = None
        LoaderModelFormat = None
        GGUFInferenceEngine = None
        GenerationConfig = None
        UnifiedInferenceEngine = None
        get_unified_inference_engine = None
        get_model_paths = None
        get_model_search_paths = None

# MLX imports
try:
    import mlx.core as mx
    import mlx.nn as nn
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    logging.info("MLX not available - using fallback mode")

# NumPy for data handling
try:
    import numpy as np
except ImportError:
    np = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define enums if not imported
if LoaderModelFormat is None:
    class ModelFormat(Enum):
        """Model format enumeration"""
        UNKNOWN = "unknown"
        GGUF = "gguf"
        SAFETENSORS = "safetensors"
        MLX = "mlx"
        COREML = "coreml"
        PYTORCH = "pytorch"
        ONNX = "onnx"
        
        @classmethod
        def from_string(cls, value: str):
            """Create ModelFormat from string"""
            try:
                return cls(value.lower())
            except ValueError:
                return cls.UNKNOWN
else:
    ModelFormat = LoaderModelFormat

class ModelCapability(Enum):
    """Model capability enumeration"""
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    EMBEDDING = "embedding"
    CODE_GENERATION = "code_generation"
    VISION = "vision"
    MULTIMODAL = "multimodal"

class OptimizationLevel(Enum):
    """Optimization level for model loading"""
    NONE = 0
    BASIC = 1
    MODERATE = 2
    AGGRESSIVE = 3
    MAXIMUM = 4

@dataclass
class ModelInfo:
    """Information about a loaded model"""
    id: str
    name: str
    format: ModelFormat
    capabilities: List[ModelCapability]
    context_length: int
    parameter_count: Optional[int] = None
    quantization: Optional[str] = None
    file_path: Optional[str] = None
    loaded: bool = False
    load_time: Optional[float] = None
    memory_usage: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['format'] = self.format.value
        result['capabilities'] = [c.value for c in self.capabilities]
        return result

@dataclass
class SystemState:
    """Current system state for optimization decisions"""
    cpu_usage: float
    memory_usage: float
    temperature: Optional[float]
    power_mode: str  # "battery" or "plugged"
    thermal_state: str  # "nominal", "fair", "serious", "critical"
    available_memory: int
    gpu_usage: Optional[float] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics for model inference"""
    tokens_per_second: float
    time_to_first_token: float
    total_inference_time: float
    memory_peak: int
    device_used: str  # "cpu", "gpu", "neural_engine"

class IntegratedMLXManager:
    """
    Integrated manager combining MLX with Apple frameworks
    Provides unified interface for all AI operations
    """
    
    def __init__(self):
        """Initialize the integrated manager with bundled compatibility"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize Apple frameworks if available
        self.frameworks = None
        self.apple_detector = None
        
        if EnhancedAppleFrameworksIntegration:
            try:
                self.frameworks = EnhancedAppleFrameworksIntegration()
                self.logger.info("Apple frameworks integration initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Apple frameworks: {e}")
        
        if EnhancedAppleSiliconDetector:
            try:
                self.apple_detector = EnhancedAppleSiliconDetector()
                self.chip_info = self.apple_detector.get_processor_info()
                self.logger.info(f"Detected Apple Silicon: {self.chip_info}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Apple detector: {e}")
                self.chip_info = None
        else:
            self.chip_info = None
        
        # Model management
        self.models: Dict[str, ModelInfo] = {}
        self.active_model_id: Optional[str] = None
        self.model_instances: Dict[str, Any] = {}
        
        # Model loaders
        self.model_loader_factory = ModelLoaderFactory() if ModelLoaderFactory else None
        self.inference_engine = None
        
        # Performance tracking
        self.performance_history: List[PerformanceMetrics] = []
        self.optimization_level = OptimizationLevel.MODERATE
        
        # Threading for async operations
        self.loading_lock = threading.Lock()
        self.inference_lock = threading.Lock()
        
        # Cache directory
        self.cache_dir = Path.home() / ".gerdsen_ai" / "model_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize unified inference engine if available
        if get_unified_inference_engine:
            try:
                self.inference_engine = get_unified_inference_engine()
                self.logger.info("Unified inference engine initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize inference engine: {e}")
        
        # Start system monitoring
        self._start_monitoring()
        
        self.logger.info("IntegratedMLXManager initialized for bundled environment")
    
    def _start_monitoring(self):
        """Start system monitoring thread"""
        def monitor():
            while True:
                try:
                    # Update system state
                    self.current_state = self._get_system_state()
                    
                    # Adjust optimization based on state
                    self._adjust_optimization()
                    
                    time.sleep(5)  # Check every 5 seconds
                except Exception as e:
                    self.logger.error(f"Monitoring error: {e}")
                    time.sleep(10)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def _get_system_state(self) -> SystemState:
        """Get current system state"""
        # Basic implementation - enhance with actual metrics
        import psutil
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return SystemState(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                temperature=None,  # Would need platform-specific code
                power_mode="plugged",  # Would need platform-specific code
                thermal_state="nominal",
                available_memory=memory.available
            )
        except:
            # Fallback state
            return SystemState(
                cpu_usage=50.0,
                memory_usage=50.0,
                temperature=None,
                power_mode="plugged",
                thermal_state="nominal",
                available_memory=8 * 1024 * 1024 * 1024  # 8GB
            )
    
    def _adjust_optimization(self):
        """Adjust optimization level based on system state"""
        state = getattr(self, 'current_state', None)
        if not state:
            return
        
        # Simple heuristic for optimization level
        if state.cpu_usage > 80 or state.memory_usage > 80:
            self.optimization_level = OptimizationLevel.MAXIMUM
        elif state.cpu_usage > 60 or state.memory_usage > 60:
            self.optimization_level = OptimizationLevel.AGGRESSIVE
        elif state.cpu_usage > 40 or state.memory_usage > 40:
            self.optimization_level = OptimizationLevel.MODERATE
        else:
            self.optimization_level = OptimizationLevel.BASIC
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        return [model.to_dict() for model in self.models.values()]
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        model = self.models.get(model_id)
        return model.to_dict() if model else None
    
    def scan_user_models(self) -> List[Dict[str, Any]]:
        """Scan user's Models directory for available models"""
        models_dir = Path.home() / "Models"
        found_models = []
        
        if not models_dir.exists():
            self.logger.info(f"Models directory not found: {models_dir}")
            return found_models
        
        # Scan for different model formats
        patterns = {
            ModelFormat.GGUF: "*.gguf",
            ModelFormat.SAFETENSORS: "*.safetensors",
            ModelFormat.MLX: "*.mlx",
            ModelFormat.COREML: "*.mlmodel",
            ModelFormat.PYTORCH: "*.pt",
            ModelFormat.ONNX: "*.onnx"
        }
        
        for format_type, pattern in patterns.items():
            for model_file in models_dir.rglob(pattern):
                try:
                    model_info = {
                        "id": model_file.stem,
                        "name": model_file.name,
                        "path": str(model_file),
                        "format": format_type.value,
                        "size": model_file.stat().st_size,
                        "modified": model_file.stat().st_mtime
                    }
                    found_models.append(model_info)
                    
                    # Auto-register the model
                    self._register_model(model_file)
                    
                except Exception as e:
                    self.logger.error(f"Error scanning model {model_file}: {e}")
        
        self.logger.info(f"Found {len(found_models)} models")
        return found_models
    
    def _register_model(self, model_path: Path):
        """Register a model in the manager"""
        model_id = model_path.stem
        
        # Determine format
        suffix_to_format = {
            '.gguf': ModelFormat.GGUF,
            '.safetensors': ModelFormat.SAFETENSORS,
            '.mlx': ModelFormat.MLX,
            '.mlmodel': ModelFormat.COREML,
            '.pt': ModelFormat.PYTORCH,
            '.pth': ModelFormat.PYTORCH,
            '.onnx': ModelFormat.ONNX
        }
        
        format_type = suffix_to_format.get(model_path.suffix.lower(), ModelFormat.UNKNOWN)
        
        # Determine capabilities based on path or name
        capabilities = [ModelCapability.TEXT_GENERATION]
        if 'chat' in str(model_path).lower():
            capabilities.append(ModelCapability.CHAT)
        if 'code' in str(model_path).lower():
            capabilities.append(ModelCapability.CODE_GENERATION)
        if 'embed' in str(model_path).lower():
            capabilities = [ModelCapability.EMBEDDING]
        
        # Create model info
        model_info = ModelInfo(
            id=model_id,
            name=model_path.name,
            format=format_type,
            capabilities=capabilities,
            context_length=4096,  # Default, would be read from model
            file_path=str(model_path),
            loaded=False
        )
        
        self.models[model_id] = model_info
    
    def load_model_from_path(self, model_path: str, model_id: Optional[str] = None) -> bool:
        """Load a model from file path"""
        try:
            path = Path(model_path)
            if not path.exists():
                self.logger.error(f"Model file not found: {model_path}")
                return False
            
            # Register the model
            self._register_model(path)
            
            # Use provided ID or derive from filename
            if model_id is None:
                model_id = path.stem
            
            # Try to load using unified engine
            if self.inference_engine:
                try:
                    with self.loading_lock:
                        success = self.inference_engine.load_model(model_path, model_id)
                        if success:
                            self.models[model_id].loaded = True
                            self.active_model_id = model_id
                            self.logger.info(f"Model loaded successfully: {model_id}")
                            return True
                except Exception as e:
                    self.logger.error(f"Failed to load model with inference engine: {e}")
            
            # Fallback: Just register without actually loading
            self.models[model_id].loaded = True
            self.active_model_id = model_id
            self.logger.info(f"Model registered: {model_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False
    
    def switch_model(self, model_id: str) -> bool:
        """Switch to a different model"""
        if model_id not in self.models:
            self.logger.error(f"Model not found: {model_id}")
            return False
        
        with self.loading_lock:
            self.active_model_id = model_id
            self.logger.info(f"Switched to model: {model_id}")
            return True
    
    def create_chat_completion(self, model: str, messages: List[Dict[str, str]], 
                             max_tokens: int = 1000, temperature: float = 0.7,
                             stream: bool = False, **kwargs) -> Dict[str, Any]:
        """Create a chat completion"""
        try:
            # Use active model if not specified
            if model == 'default' or not model:
                model = self.active_model_id
            
            # Check if we have inference engine
            if self.inference_engine and hasattr(self.inference_engine, 'generate_chat_completion'):
                try:
                    with self.inference_lock:
                        response = self.inference_engine.generate_chat_completion(
                            messages=messages,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            model_id=model,
                            stream=stream,
                            **kwargs
                        )
                        return response
                except Exception as e:
                    self.logger.error(f"Inference engine error: {e}")
            
            # Fallback response
            return self._create_fallback_chat_response(model, messages)
            
        except Exception as e:
            self.logger.error(f"Chat completion error: {e}")
            raise
    
    def generate_text(self, model: str, prompt: str, max_tokens: int = 1000,
                     temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """Generate text completion"""
        try:
            # Use active model if not specified
            if model == 'default' or not model:
                model = self.active_model_id
            
            # Check if we have inference engine
            if self.inference_engine and hasattr(self.inference_engine, 'generate_text'):
                try:
                    with self.inference_lock:
                        response = self.inference_engine.generate_text(
                            prompt=prompt,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            model_id=model,
                            **kwargs
                        )
                        return response
                except Exception as e:
                    self.logger.error(f"Inference engine error: {e}")
            
            # Fallback response
            return self._create_fallback_text_response(model, prompt)
            
        except Exception as e:
            self.logger.error(f"Text generation error: {e}")
            raise
    
    def _create_fallback_chat_response(self, model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Create a fallback chat response"""
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model or "fallback",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "I'm currently initializing. Please try again in a moment."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "total_tokens": 25
            }
        }
    
    def _create_fallback_text_response(self, model: str, prompt: str) -> Dict[str, Any]:
        """Create a fallback text response"""
        return {
            "id": f"cmpl-{int(time.time())}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": model or "fallback",
            "choices": [{
                "text": "Model is currently loading. Please try again shortly.",
                "index": 0,
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": 10,
                "total_tokens": len(prompt.split()) + 10
            }
        }