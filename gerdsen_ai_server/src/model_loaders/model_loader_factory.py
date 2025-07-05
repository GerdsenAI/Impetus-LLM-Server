"""
Model Loader Factory with automatic format detection
Provides a unified interface for loading various model formats
"""

import os
import json
import struct
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, Type, BinaryIO
from enum import Enum

# Import all model loaders
from .gguf_loader import GGUFLoader
from .safetensors_loader import SafeTensorsLoader
from .mlx_loader import MLXLoader
from .coreml_loader import CoreMLLoader
from .pytorch_loader import PyTorchLoader
from .onnx_loader import ONNXLoader

logger = logging.getLogger(__name__)


class ModelFormat(Enum):
    """Supported model formats"""
    GGUF = "gguf"
    SAFETENSORS = "safetensors"
    MLX = "mlx"
    COREML = "coreml"
    PYTORCH = "pytorch"
    ONNX = "onnx"
    UNKNOWN = "unknown"


class ModelLoaderFactory:
    """
    Factory for creating appropriate model loaders based on file format detection.
    Provides automatic format detection and unified interface for all model types.
    """
    
    # Magic bytes/signatures for different formats
    FORMAT_SIGNATURES = {
        ModelFormat.GGUF: b'GGUF',
        ModelFormat.ONNX: b'\x08\x01\x12',  # ONNX protobuf header
    }
    
    # File extension mappings
    EXTENSION_MAPPINGS = {
        '.gguf': ModelFormat.GGUF,
        '.safetensors': ModelFormat.SAFETENSORS,
        '.mlx': ModelFormat.MLX,
        '.mlmodel': ModelFormat.COREML,
        '.pth': ModelFormat.PYTORCH,
        '.pt': ModelFormat.PYTORCH,
        '.bin': ModelFormat.PYTORCH,  # Common for HuggingFace models
        '.onnx': ModelFormat.ONNX,
        '.ort': ModelFormat.ONNX,  # ONNX Runtime optimized format
    }
    
    # Loader class mappings
    LOADER_CLASSES = {
        ModelFormat.GGUF: GGUFLoader,
        ModelFormat.SAFETENSORS: SafeTensorsLoader,
        ModelFormat.MLX: MLXLoader,
        ModelFormat.COREML: CoreMLLoader,
        ModelFormat.PYTORCH: PyTorchLoader,
        ModelFormat.ONNX: ONNXLoader,
    }
    
    def __init__(self):
        self.loaders: Dict[ModelFormat, Any] = {}
        self.logger = logger
        
    def detect_format_from_file(self, file_path: Union[str, Path]) -> ModelFormat:
        """
        Detect model format from file path using both extension and content inspection.
        
        Args:
            file_path: Path to the model file
            
        Returns:
            Detected ModelFormat
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Model file not found: {file_path}")
            
        # First try extension-based detection
        format_from_ext = self._detect_from_extension(file_path)
        
        # Then try content-based detection for validation
        format_from_content = self._detect_from_content(file_path)
        
        # If content detection found something, prioritize it
        if format_from_content != ModelFormat.UNKNOWN:
            if format_from_ext != ModelFormat.UNKNOWN and format_from_ext != format_from_content:
                self.logger.warning(
                    f"Extension suggests {format_from_ext.value} but content indicates {format_from_content.value}. "
                    f"Using content-based detection."
                )
            return format_from_content
            
        # Otherwise use extension-based detection
        if format_from_ext != ModelFormat.UNKNOWN:
            return format_from_ext
            
        # Special cases - check for directory-based formats
        if file_path.is_dir():
            return self._detect_directory_format(file_path)
            
        return ModelFormat.UNKNOWN
        
    def _detect_from_extension(self, file_path: Path) -> ModelFormat:
        """Detect format from file extension"""
        extension = file_path.suffix.lower()
        return self.EXTENSION_MAPPINGS.get(extension, ModelFormat.UNKNOWN)
        
    def _detect_from_content(self, file_path: Path) -> ModelFormat:
        """Detect format from file content by checking magic bytes"""
        try:
            with open(file_path, 'rb') as f:
                # Read first 16 bytes for signature detection
                header = f.read(16)
                
                # Check each known signature
                for format_type, signature in self.FORMAT_SIGNATURES.items():
                    if header.startswith(signature):
                        return format_type
                        
                # Special detection for SafeTensors (JSON header)
                if self._is_safetensors_file(file_path, header):
                    return ModelFormat.SAFETENSORS
                    
                # Special detection for PyTorch (pickle format)
                if self._is_pytorch_file(header):
                    return ModelFormat.PYTORCH
                    
        except Exception as e:
            self.logger.debug(f"Content detection failed: {e}")
            
        return ModelFormat.UNKNOWN
        
    def _is_safetensors_file(self, file_path: Path, header: bytes) -> bool:
        """Check if file is a SafeTensors file"""
        try:
            # SafeTensors starts with a little-endian uint64 indicating header size
            if len(header) >= 8:
                header_size = struct.unpack('<Q', header[:8])[0]
                # Reasonable header size check
                if 0 < header_size < 100000:  # Max 100KB header
                    with open(file_path, 'rb') as f:
                        f.seek(8)
                        json_header = f.read(header_size)
                        # Try to parse as JSON
                        json.loads(json_header)
                        return True
        except:
            pass
        return False
        
    def _is_pytorch_file(self, header: bytes) -> bool:
        """Check if file is a PyTorch file (pickle format)"""
        # PyTorch files typically start with pickle protocol markers
        pickle_markers = [b'\x80\x02', b'\x80\x03', b'\x80\x04', b'\x80\x05']
        return any(header.startswith(marker) for marker in pickle_markers)
        
    def _detect_directory_format(self, dir_path: Path) -> ModelFormat:
        """Detect format for directory-based models"""
        # Check for MLX models (directory with model.safetensors and config.json)
        if (dir_path / 'model.safetensors').exists() and (dir_path / 'config.json').exists():
            # Could be MLX or HuggingFace - check for MLX-specific files
            if (dir_path / 'model.safetensors.index.json').exists():
                return ModelFormat.MLX
                
        # Check for CoreML models (.mlmodel is actually a directory)
        if dir_path.suffix == '.mlmodel':
            return ModelFormat.COREML
            
        return ModelFormat.UNKNOWN
        
    def create_loader(self, format_type: ModelFormat) -> Optional[Any]:
        """
        Create or get a loader instance for the specified format.
        
        Args:
            format_type: The model format type
            
        Returns:
            Loader instance or None if format not supported
        """
        if format_type == ModelFormat.UNKNOWN:
            return None
            
        # Return existing loader if already created
        if format_type in self.loaders:
            return self.loaders[format_type]
            
        # Create new loader
        loader_class = self.LOADER_CLASSES.get(format_type)
        if loader_class:
            try:
                loader = loader_class()
                self.loaders[format_type] = loader
                self.logger.info(f"Created {format_type.value} loader")
                return loader
            except Exception as e:
                self.logger.error(f"Failed to create {format_type.value} loader: {e}")
                return None
                
        self.logger.error(f"No loader available for format: {format_type.value}")
        return None
        
    def load_model(self, file_path: Union[str, Path], 
                   model_id: Optional[str] = None,
                   format_hint: Optional[ModelFormat] = None,
                   **kwargs) -> Dict[str, Any]:
        """
        Load a model with automatic format detection.
        
        Args:
            file_path: Path to the model file
            model_id: Optional model identifier
            format_hint: Optional format hint to skip detection
            **kwargs: Additional arguments passed to the specific loader
            
        Returns:
            Dictionary containing model information and data
        """
        file_path = Path(file_path)
        
        # Detect format if not provided
        if format_hint:
            format_type = format_hint
            self.logger.info(f"Using provided format hint: {format_type.value}")
        else:
            format_type = self.detect_format_from_file(file_path)
            self.logger.info(f"Detected format: {format_type.value}")
            
        if format_type == ModelFormat.UNKNOWN:
            raise ValueError(f"Unable to detect model format for: {file_path}")
            
        # Get appropriate loader
        loader = self.create_loader(format_type)
        if not loader:
            raise RuntimeError(f"No loader available for format: {format_type.value}")
            
        # Load the model
        try:
            self.logger.info(f"Loading model with {format_type.value} loader")
            
            # Call the appropriate load method based on loader interface
            if hasattr(loader, 'load_model'):
                # Most loaders use load_model(file_path, ...)
                if format_type == ModelFormat.GGUF:
                    result = loader.load_model(str(file_path), model_id)
                else:
                    result = loader.load_model(str(file_path), **kwargs)
            else:
                raise AttributeError(f"Loader {format_type.value} missing load_model method")
                
            # Ensure consistent result format
            if 'format' not in result:
                result['format'] = format_type.value
            if 'loader' not in result:
                result['loader'] = format_type.value
            if model_id and 'id' not in result:
                result['id'] = model_id
                
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise
            
    def validate_model_file(self, file_path: Union[str, Path], 
                           format_hint: Optional[ModelFormat] = None) -> Dict[str, Any]:
        """
        Validate a model file without fully loading it.
        
        Args:
            file_path: Path to the model file
            format_hint: Optional format hint
            
        Returns:
            Validation results including format, size, and basic metadata
        """
        file_path = Path(file_path)
        
        validation_result = {
            'valid': False,
            'format': ModelFormat.UNKNOWN.value,
            'file_path': str(file_path),
            'exists': file_path.exists(),
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        if not file_path.exists():
            validation_result['errors'].append(f"File not found: {file_path}")
            return validation_result
            
        try:
            # Get file stats
            stats = file_path.stat()
            validation_result['metadata']['size_bytes'] = stats.st_size
            validation_result['metadata']['size_mb'] = stats.st_size / (1024 * 1024)
            validation_result['metadata']['modified'] = stats.st_mtime
            
            # Detect format
            format_type = format_hint or self.detect_format_from_file(file_path)
            validation_result['format'] = format_type.value
            
            if format_type == ModelFormat.UNKNOWN:
                validation_result['errors'].append("Unable to detect model format")
                return validation_result
                
            # Get loader and validate if it has a validation method
            loader = self.create_loader(format_type)
            if loader and hasattr(loader, 'validate_file'):
                try:
                    is_valid = loader.validate_file(str(file_path))
                    validation_result['valid'] = is_valid
                    if not is_valid:
                        validation_result['errors'].append(f"File validation failed for {format_type.value} format")
                except Exception as e:
                    validation_result['errors'].append(f"Validation error: {str(e)}")
            else:
                # Basic validation passed if format was detected
                validation_result['valid'] = True
                validation_result['warnings'].append("Full validation not available for this format")
                
        except Exception as e:
            validation_result['errors'].append(f"Validation failed: {str(e)}")
            
        return validation_result
        
    def get_supported_formats(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all supported formats"""
        formats = {}
        
        for format_type in ModelFormat:
            if format_type == ModelFormat.UNKNOWN:
                continue
                
            extensions = [ext for ext, fmt in self.EXTENSION_MAPPINGS.items() if fmt == format_type]
            
            formats[format_type.value] = {
                'name': format_type.value,
                'extensions': extensions,
                'has_loader': format_type in self.LOADER_CLASSES,
                'description': self._get_format_description(format_type)
            }
            
        return formats
        
    def _get_format_description(self, format_type: ModelFormat) -> str:
        """Get a description for each format type"""
        descriptions = {
            ModelFormat.GGUF: "GGML Universal Format - Optimized for CPU/GPU inference",
            ModelFormat.SAFETENSORS: "Safe Tensors format - Secure and fast tensor serialization",
            ModelFormat.MLX: "Apple MLX format - Optimized for Apple Silicon",
            ModelFormat.COREML: "Apple CoreML format - iOS/macOS deployment",
            ModelFormat.PYTORCH: "PyTorch format - Standard PyTorch model files",
            ModelFormat.ONNX: "Open Neural Network Exchange - Cross-platform deployment"
        }
        return descriptions.get(format_type, "")
        
    def unload_model(self, model_id: str, format_type: Optional[ModelFormat] = None) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_id: Model identifier
            format_type: Optional format type hint
            
        Returns:
            True if successfully unloaded
        """
        # If format type provided, try that loader first
        if format_type and format_type in self.loaders:
            loader = self.loaders[format_type]
            if hasattr(loader, 'unload_model'):
                return loader.unload_model(model_id)
                
        # Otherwise try all loaders
        for loader in self.loaders.values():
            if hasattr(loader, 'unload_model'):
                try:
                    if loader.unload_model(model_id):
                        return True
                except:
                    continue
                    
        self.logger.warning(f"Model {model_id} not found in any loader")
        return False
        
    def get_loaded_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded models across all loaders"""
        all_models = {}
        
        for format_type, loader in self.loaders.items():
            if hasattr(loader, 'list_loaded_models'):
                try:
                    models = loader.list_loaded_models()
                    if isinstance(models, dict):
                        for model_id, model_info in models.items():
                            # Add format info if not present
                            if 'format' not in model_info:
                                model_info['format'] = format_type.value
                            all_models[model_id] = model_info
                    elif isinstance(models, list):
                        # Some loaders return just a list of IDs
                        for model_id in models:
                            all_models[model_id] = {
                                'id': model_id,
                                'format': format_type.value
                            }
                except Exception as e:
                    self.logger.error(f"Error listing models from {format_type.value} loader: {e}")
                    
        return all_models
        
    def clear_loaders(self):
        """Clear all loader instances and free memory"""
        for format_type, loader in self.loaders.items():
            # Unload all models if possible
            if hasattr(loader, 'list_loaded_models'):
                try:
                    models = loader.list_loaded_models()
                    model_ids = models.keys() if isinstance(models, dict) else models
                    for model_id in model_ids:
                        if hasattr(loader, 'unload_model'):
                            loader.unload_model(model_id)
                except:
                    pass
                    
        self.loaders.clear()
        self.logger.info("Cleared all model loaders")


# Convenience functions
_factory_instance = None


def get_factory() -> ModelLoaderFactory:
    """Get singleton factory instance"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ModelLoaderFactory()
    return _factory_instance


def load_model(file_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
    """Convenience function to load a model using the factory"""
    return get_factory().load_model(file_path, **kwargs)


def detect_format(file_path: Union[str, Path]) -> str:
    """Convenience function to detect model format"""
    format_type = get_factory().detect_format_from_file(file_path)
    return format_type.value


def validate_model(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Convenience function to validate a model file"""
    return get_factory().validate_model_file(file_path)