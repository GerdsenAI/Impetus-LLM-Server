"""
PyTorch model loader for standard deep learning models
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import pickle

try:
    import torch
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    torch = None

logger = logging.getLogger(__name__)


class PyTorchLoader:
    """Loader for PyTorch format models"""
    
    def __init__(self):
        self.supported_extensions = ['.pt', '.pth', '.bin']
        self.loaded_models = {}
        
        if not PYTORCH_AVAILABLE:
            logger.warning("PyTorch not available - PyTorch loader functionality will be limited")
            
    def can_load(self, file_path: str) -> bool:
        """Check if this loader can handle the given file"""
        return any(file_path.lower().endswith(ext) for ext in self.supported_extensions)
        
    def load_model(self, file_path: str, model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load a PyTorch model
        
        Args:
            file_path: Path to the .pt, .pth, or .bin file
            model_config: Optional configuration for the model
            
        Returns:
            Dictionary containing model information and state dict
        """
        try:
            logger.info(f"Loading PyTorch model from: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Model file not found: {file_path}")
                
            if not PYTORCH_AVAILABLE:
                raise RuntimeError("PyTorch is not available. Please install torch to use PyTorch models.")
                
            # Determine device
            device = self._get_device()
            
            # Load the model state dict or full model
            try:
                # Try loading as state dict first
                state_dict = torch.load(file_path, map_location=device, weights_only=True)
                model_type = 'state_dict'
            except Exception:
                # If that fails, try loading as full model (with pickle)
                try:
                    state_dict = torch.load(file_path, map_location=device, weights_only=False)
                    model_type = 'full_model'
                except Exception as e:
                    # Last resort - try loading with pickle directly
                    with open(file_path, 'rb') as f:
                        state_dict = pickle.load(f)
                    model_type = 'pickle'
            
            # Try to load metadata if available
            metadata = self._load_metadata(file_path)
            
            # Analyze the loaded content
            model_info = self._analyze_model_content(state_dict, model_type)
            
            # Get model info
            model_info.update({
                'format': 'pytorch',
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'device': str(device),
                'metadata': metadata,
                'config': model_config or {},
                'model_type': model_type,
                'state_dict': state_dict if model_type == 'state_dict' else None,
                'model_object': state_dict if model_type != 'state_dict' else None
            })
            
            # Try to determine model architecture
            model_info['architecture'] = self._infer_architecture(model_info)
            
            logger.info(f"Successfully loaded PyTorch model: {model_type} with {model_info.get('num_parameters', 0):,} parameters")
            
            # Cache the loaded model
            model_id = Path(file_path).stem
            self.loaded_models[model_id] = model_info
            
            return model_info
            
        except Exception as e:
            logger.error(f"Failed to load PyTorch model: {str(e)}")
            raise
            
    def _get_device(self) -> torch.device:
        """Get the appropriate device for PyTorch"""
        if not PYTORCH_AVAILABLE:
            return "cpu"
            
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return torch.device("mps")  # Apple Silicon GPU
        else:
            return torch.device("cpu")
            
    def _analyze_model_content(self, content: Any, model_type: str) -> Dict[str, Any]:
        """Analyze the loaded model content"""
        info = {}
        
        if model_type == 'state_dict' and isinstance(content, dict):
            # Analyze state dict
            info['num_layers'] = len(content)
            info['layer_names'] = list(content.keys())
            
            # Calculate total parameters
            total_params = 0
            param_shapes = {}
            for name, tensor in content.items():
                if hasattr(tensor, 'numel'):
                    total_params += tensor.numel()
                    param_shapes[name] = list(tensor.shape) if hasattr(tensor, 'shape') else None
                    
            info['num_parameters'] = total_params
            info['parameter_shapes'] = param_shapes
            
        elif model_type == 'full_model':
            # Try to extract information from full model
            if hasattr(content, 'state_dict'):
                state_dict = content.state_dict()
                return self._analyze_model_content(state_dict, 'state_dict')
            else:
                info['model_class'] = type(content).__name__
                info['model_modules'] = [name for name, _ in content.named_modules()] if hasattr(content, 'named_modules') else []
                
        return info
        
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
                
        # Check for model_info.json
        model_info_path = Path(file_path).parent / "model_info.json"
        if model_info_path.exists():
            try:
                with open(model_info_path, 'r') as f:
                    metadata['model_info'] = json.load(f)
                logger.info(f"Loaded model_info.json from {model_info_path}")
            except Exception as e:
                logger.warning(f"Failed to load model_info.json: {e}")
                
        return metadata if metadata else None
        
    def _infer_architecture(self, model_info: Dict[str, Any]) -> str:
        """Try to infer model architecture from layer names or structure"""
        if 'layer_names' in model_info:
            layer_names_str = ' '.join(model_info['layer_names']).lower()
            
            # Common architectures based on layer naming patterns
            if 'transformer' in layer_names_str or 'attention' in layer_names_str:
                if 'bert' in layer_names_str:
                    return 'bert'
                elif 'gpt' in layer_names_str:
                    return 'gpt'
                elif 't5' in layer_names_str:
                    return 't5'
                elif 'llama' in layer_names_str:
                    return 'llama'
                else:
                    return 'transformer'
            elif 'conv' in layer_names_str:
                if 'resnet' in layer_names_str:
                    return 'resnet'
                elif 'vgg' in layer_names_str:
                    return 'vgg'
                elif 'efficientnet' in layer_names_str:
                    return 'efficientnet'
                else:
                    return 'cnn'
            elif 'lstm' in layer_names_str:
                return 'lstm'
            elif 'gru' in layer_names_str:
                return 'gru'
                
        return 'unknown'
        
    def create_model_from_state_dict(self, model_id: str, model_class: Any) -> Any:
        """Create a model instance from a loaded state dict"""
        if model_id not in self.loaded_models:
            raise ValueError(f"Model {model_id} not loaded")
            
        model_info = self.loaded_models[model_id]
        if model_info['model_type'] != 'state_dict':
            raise ValueError(f"Model {model_id} is not a state dict")
            
        # Create model instance
        model = model_class()
        
        # Load state dict
        model.load_state_dict(model_info['state_dict'])
        
        # Move to appropriate device
        device = torch.device(model_info['device'])
        model = model.to(device)
        
        return model
        
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        return self.loaded_models.get(model_id)
        
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        if model_id in self.loaded_models:
            # Clear model data from memory
            if 'state_dict' in self.loaded_models[model_id]:
                del self.loaded_models[model_id]['state_dict']
            if 'model_object' in self.loaded_models[model_id]:
                del self.loaded_models[model_id]['model_object']
            del self.loaded_models[model_id]
            
            # Force garbage collection
            import gc
            gc.collect()
            
            if PYTORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            logger.info(f"Unloaded PyTorch model: {model_id}")
            return True
        return False
        
    def list_loaded_models(self) -> List[str]:
        """List all currently loaded models"""
        return list(self.loaded_models.keys())
        
    def optimize_for_device(self, model_id: str, device_type: str = 'auto') -> bool:
        """Optimize model for specific device"""
        if model_id not in self.loaded_models:
            logger.warning(f"Model {model_id} not loaded")
            return False
            
        if not PYTORCH_AVAILABLE:
            logger.warning("PyTorch not available for optimization")
            return False
            
        try:
            model_info = self.loaded_models[model_id]
            
            # Determine target device
            if device_type == 'auto':
                device = self._get_device()
            elif device_type == 'gpu' and torch.cuda.is_available():
                device = torch.device('cuda')
            elif device_type == 'mps' and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = torch.device('mps')
            else:
                device = torch.device('cpu')
                
            model_info['optimized_device'] = str(device)
            logger.info(f"Optimized {model_id} for device: {device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to optimize model: {e}")
            return False