"""
SafeTensors model loader for Hugging Face models
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import safetensors.torch
import torch

logger = logging.getLogger(__name__)


class SafeTensorsLoader:
    """Loader for SafeTensors format models"""
    
    def __init__(self):
        self.supported_extensions = ['.safetensors']
        self.loaded_models = {}
        
    def can_load(self, file_path: str) -> bool:
        """Check if this loader can handle the given file"""
        return any(file_path.lower().endswith(ext) for ext in self.supported_extensions)
        
    def load_model(self, file_path: str, model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load a SafeTensors model
        
        Args:
            file_path: Path to the .safetensors file
            model_config: Optional configuration for the model
            
        Returns:
            Dictionary containing model information and tensors
        """
        try:
            logger.info(f"Loading SafeTensors model from: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Model file not found: {file_path}")
                
            # Load the safetensors file
            tensors = safetensors.torch.load_file(file_path)
            
            # Try to load metadata if available
            metadata = self._load_metadata(file_path)
            
            # Get model info
            model_info = {
                'format': 'safetensors',
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'num_tensors': len(tensors),
                'tensor_names': list(tensors.keys()),
                'metadata': metadata,
                'config': model_config or {},
                'tensors': tensors
            }
            
            # Estimate model parameters
            total_params = 0
            for tensor in tensors.values():
                total_params += tensor.numel()
            model_info['total_parameters'] = total_params
            
            # Try to determine model architecture from tensor names
            model_info['architecture'] = self._infer_architecture(tensors.keys())
            
            logger.info(f"Successfully loaded SafeTensors model with {len(tensors)} tensors and {total_params:,} parameters")
            
            # Cache the loaded model
            model_id = Path(file_path).stem
            self.loaded_models[model_id] = model_info
            
            return model_info
            
        except Exception as e:
            logger.error(f"Failed to load SafeTensors model: {str(e)}")
            raise
            
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
                
        # Check for tokenizer config
        tokenizer_path = Path(file_path).parent / "tokenizer_config.json"
        if tokenizer_path.exists():
            try:
                with open(tokenizer_path, 'r') as f:
                    metadata['tokenizer_config'] = json.load(f)
                logger.info(f"Loaded tokenizer_config.json from {tokenizer_path}")
            except Exception as e:
                logger.warning(f"Failed to load tokenizer_config.json: {e}")
                
        return metadata if metadata else None
        
    def _infer_architecture(self, tensor_names: List[str]) -> str:
        """Try to infer model architecture from tensor names"""
        tensor_names_str = ' '.join(tensor_names).lower()
        
        # Common architectures based on layer naming patterns
        if 'transformer' in tensor_names_str and 'attention' in tensor_names_str:
            if 'llama' in tensor_names_str:
                return 'llama'
            elif 'mistral' in tensor_names_str:
                return 'mistral'
            elif 'gpt' in tensor_names_str:
                return 'gpt'
            elif 'bert' in tensor_names_str:
                return 'bert'
            elif 't5' in tensor_names_str:
                return 't5'
            else:
                return 'transformer'
        elif 'conv' in tensor_names_str and 'bn' in tensor_names_str:
            return 'cnn'
        elif 'lstm' in tensor_names_str or 'gru' in tensor_names_str:
            return 'rnn'
        else:
            return 'unknown'
            
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        return self.loaded_models.get(model_id)
        
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        if model_id in self.loaded_models:
            # Clear tensors from memory
            if 'tensors' in self.loaded_models[model_id]:
                del self.loaded_models[model_id]['tensors']
            del self.loaded_models[model_id]
            
            # Force garbage collection
            import gc
            gc.collect()
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            logger.info(f"Unloaded model: {model_id}")
            return True
        return False
        
    def list_loaded_models(self) -> List[str]:
        """List all currently loaded models"""
        return list(self.loaded_models.keys())