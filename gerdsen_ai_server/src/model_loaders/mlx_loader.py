"""
MLX model loader for Apple Silicon optimized models
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import numpy as np

try:
    import mlx.core as mx
    import mlx.nn as nn
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    mx = None
    nn = None

logger = logging.getLogger(__name__)


class MLXLoader:
    """Loader for MLX format models optimized for Apple Silicon"""
    
    def __init__(self):
        self.supported_extensions = ['.mlx', '.npz']
        self.loaded_models = {}
        
        if not MLX_AVAILABLE:
            logger.warning("MLX not available - MLX loader functionality will be limited")
            
    def can_load(self, file_path: str) -> bool:
        """Check if this loader can handle the given file"""
        return any(file_path.lower().endswith(ext) for ext in self.supported_extensions)
        
    def load_model(self, file_path: str, model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load an MLX model
        
        Args:
            file_path: Path to the .mlx or .npz file
            model_config: Optional configuration for the model
            
        Returns:
            Dictionary containing model information and weights
        """
        try:
            logger.info(f"Loading MLX model from: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Model file not found: {file_path}")
                
            if not MLX_AVAILABLE:
                raise RuntimeError("MLX is not available. Please install mlx to use MLX models.")
                
            # Load the model weights
            if file_path.lower().endswith('.npz'):
                weights = self._load_npz_weights(file_path)
            else:
                weights = self._load_mlx_weights(file_path)
                
            # Try to load metadata if available
            metadata = self._load_metadata(file_path)
            
            # Get model info
            model_info = {
                'format': 'mlx',
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'num_arrays': len(weights),
                'array_names': list(weights.keys()),
                'metadata': metadata,
                'config': model_config or {},
                'weights': weights,
                'device': 'metal',  # MLX uses Metal on Apple Silicon
                'optimized_for': 'apple_silicon'
            }
            
            # Calculate total parameters
            total_params = 0
            for array in weights.values():
                if isinstance(array, mx.array):
                    total_params += array.size
                elif isinstance(array, np.ndarray):
                    total_params += array.size
            model_info['total_parameters'] = total_params
            
            # Try to determine model architecture
            model_info['architecture'] = self._infer_architecture(weights.keys())
            
            # Estimate memory usage
            model_info['estimated_memory_mb'] = (total_params * 4) / (1024 * 1024)  # Assuming float32
            
            logger.info(f"Successfully loaded MLX model with {len(weights)} arrays and {total_params:,} parameters")
            
            # Cache the loaded model
            model_id = Path(file_path).stem
            self.loaded_models[model_id] = model_info
            
            return model_info
            
        except Exception as e:
            logger.error(f"Failed to load MLX model: {str(e)}")
            raise
            
    def _load_npz_weights(self, file_path: str) -> Dict[str, mx.array]:
        """Load weights from NPZ file format"""
        weights = {}
        
        # Load numpy arrays
        np_weights = np.load(file_path)
        
        # Convert to MLX arrays
        for key in np_weights.files:
            array = np_weights[key]
            weights[key] = mx.array(array)
            
        return weights
        
    def _load_mlx_weights(self, file_path: str) -> Dict[str, mx.array]:
        """Load weights from MLX native format"""
        # For now, treat .mlx files as .npz
        # In the future, this could be a custom MLX format
        return self._load_npz_weights(file_path)
        
    def _load_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Try to load metadata from accompanying files"""
        metadata = {}
        
        # Check for config.json in the same directory
        config_path = Path(file_path).parent / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    metadata['config'] = json.load(f)
                logger.info(f"Loaded config.json from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config.json: {e}")
                
        # Check for model_config.json (MLX specific)
        model_config_path = Path(file_path).parent / "model_config.json"
        if model_config_path.exists():
            try:
                with open(model_config_path, 'r') as f:
                    metadata['model_config'] = json.load(f)
                logger.info(f"Loaded model_config.json from {model_config_path}")
            except Exception as e:
                logger.warning(f"Failed to load model_config.json: {e}")
                
        return metadata if metadata else None
        
    def _infer_architecture(self, array_names: List[str]) -> str:
        """Try to infer model architecture from array names"""
        array_names_str = ' '.join(array_names).lower()
        
        # Common MLX model patterns
        if 'transformer' in array_names_str or 'attention' in array_names_str:
            if 'llama' in array_names_str:
                return 'llama-mlx'
            elif 'mistral' in array_names_str:
                return 'mistral-mlx'
            elif 'gpt' in array_names_str:
                return 'gpt-mlx'
            else:
                return 'transformer-mlx'
        elif 'conv' in array_names_str:
            return 'cnn-mlx'
        elif 'lstm' in array_names_str or 'gru' in array_names_str:
            return 'rnn-mlx'
        else:
            return 'custom-mlx'
            
    def optimize_for_device(self, model_id: str, device_profile: Dict[str, Any]) -> bool:
        """Optimize model for specific Apple Silicon device profile"""
        if model_id not in self.loaded_models:
            logger.warning(f"Model {model_id} not loaded")
            return False
            
        try:
            model_info = self.loaded_models[model_id]
            
            # Apply device-specific optimizations
            if 'neural_engine_cores' in device_profile and device_profile['neural_engine_cores'] > 0:
                logger.info(f"Optimizing {model_id} for Neural Engine with {device_profile['neural_engine_cores']} cores")
                # Future: Apply Neural Engine optimizations
                
            if 'gpu_cores' in device_profile:
                logger.info(f"Optimizing {model_id} for GPU with {device_profile['gpu_cores']} cores")
                # MLX automatically uses Metal GPU
                
            model_info['optimization_profile'] = device_profile
            return True
            
        except Exception as e:
            logger.error(f"Failed to optimize model: {e}")
            return False
            
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        return self.loaded_models.get(model_id)
        
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        if model_id in self.loaded_models:
            # Clear weights from memory
            if 'weights' in self.loaded_models[model_id]:
                del self.loaded_models[model_id]['weights']
            del self.loaded_models[model_id]
            
            # MLX should automatically manage memory
            logger.info(f"Unloaded MLX model: {model_id}")
            return True
        return False
        
    def list_loaded_models(self) -> List[str]:
        """List all currently loaded models"""
        return list(self.loaded_models.keys())
        
    def get_device_info(self) -> Dict[str, Any]:
        """Get information about MLX device capabilities"""
        if not MLX_AVAILABLE:
            return {"available": False, "reason": "MLX not installed"}
            
        try:
            info = {
                "available": True,
                "backend": "metal",
                "device": "apple_silicon",
                "optimizations": ["metal_performance_shaders", "neural_engine"]
            }
            
            # Try to get memory limit if available
            if hasattr(mx, 'metal') and hasattr(mx.metal, 'get_memory_limit'):
                info["memory_limit"] = mx.metal.get_memory_limit()
                
            return info
        except Exception as e:
            return {"available": True, "backend": "metal", "device": "apple_silicon", "error": str(e)}