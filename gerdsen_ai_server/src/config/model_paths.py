"""
Dynamic model directory configuration
Automatically uses the current user's home directory for model storage
"""

import os
from pathlib import Path
from typing import Dict, List, Optional


class ModelPaths:
    """Centralized model path configuration for dynamic user directories"""
    
    def __init__(self):
        # Get current user's home directory dynamically
        self.user_home = Path.home()
        self.models_base_dir = self.user_home / "Models"
        
        # Define model format directories
        self.format_dirs = {
            'gguf': self.models_base_dir / 'GGUF',
            'safetensors': self.models_base_dir / 'SafeTensors',
            'mlx': self.models_base_dir / 'MLX',
            'coreml': self.models_base_dir / 'CoreML',
            'pytorch': self.models_base_dir / 'PyTorch',
            'onnx': self.models_base_dir / 'ONNX',
            'universal': self.models_base_dir / 'Universal'
        }
        
        # Define capability subdirectories
        self.capabilities = ['chat', 'completion', 'embedding', 'vision', 'audio', 'multimodal']
        
        # Utility directories
        self.downloads_dir = self.models_base_dir / 'Downloads'
        self.cache_dir = self.models_base_dir / 'Cache'
        self.converted_dir = self.models_base_dir / 'Converted'
        self.custom_dir = self.models_base_dir / 'Custom'
        
        # Legacy paths for backward compatibility
        self.legacy_cache_dir = self.user_home / '.gerdsen_ai' / 'model_cache'
        self.legacy_huggingface_dir = self.user_home / '.cache' / 'huggingface'
        
    def ensure_directories(self):
        """Create all model directories if they don't exist"""
        # Create base directory
        self.models_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create format directories with capability subdirectories
        for format_name, format_dir in self.format_dirs.items():
            for capability in self.capabilities:
                capability_dir = format_dir / capability
                capability_dir.mkdir(parents=True, exist_ok=True)
        
        # Create utility directories
        for util_dir in [self.downloads_dir, self.cache_dir, self.converted_dir, self.custom_dir]:
            util_dir.mkdir(parents=True, exist_ok=True)
            
    def get_model_search_paths(self, format_type: Optional[str] = None, 
                              capability: Optional[str] = None) -> List[Path]:
        """
        Get list of directories to search for models
        
        Args:
            format_type: Specific format to search (e.g., 'gguf', 'safetensors')
            capability: Specific capability to search (e.g., 'chat', 'embedding')
            
        Returns:
            List of paths to search for models
        """
        search_paths = []
        
        # Add format-specific paths
        if format_type and format_type.lower() in self.format_dirs:
            format_dir = self.format_dirs[format_type.lower()]
            if capability and capability in self.capabilities:
                # Specific format and capability
                search_paths.append(format_dir / capability)
            else:
                # All capabilities for this format
                for cap in self.capabilities:
                    search_paths.append(format_dir / cap)
        elif capability:
            # Specific capability across all formats
            for format_dir in self.format_dirs.values():
                search_paths.append(format_dir / capability)
        else:
            # All directories
            for format_dir in self.format_dirs.values():
                for cap in self.capabilities:
                    search_paths.append(format_dir / cap)
        
        # Add utility directories
        search_paths.extend([
            self.custom_dir,
            self.downloads_dir,
            self.cache_dir,
            self.converted_dir
        ])
        
        # Add legacy directories for backward compatibility
        if self.legacy_cache_dir.exists():
            search_paths.append(self.legacy_cache_dir)
        if self.legacy_huggingface_dir.exists():
            search_paths.append(self.legacy_huggingface_dir)
            
        # Filter out non-existent paths
        return [p for p in search_paths if p.exists()]
        
    def scan_for_models(self, extensions: Optional[List[str]] = None) -> Dict[str, List[Path]]:
        """
        Scan all model directories for available models
        
        Args:
            extensions: List of file extensions to look for (e.g., ['.gguf', '.safetensors'])
            
        Returns:
            Dictionary mapping model paths to their locations
        """
        if extensions is None:
            extensions = ['.gguf', '.safetensors', '.mlx', '.mlmodel', '.mlpackage', 
                         '.pt', '.pth', '.bin', '.onnx', '.ort', '.npz']
            
        models_found = {}
        search_paths = self.get_model_search_paths()
        
        for search_path in search_paths:
            try:
                for file_path in search_path.rglob('*'):
                    if file_path.is_file() and file_path.suffix.lower() in extensions:
                        model_name = file_path.stem
                        if model_name not in models_found:
                            models_found[model_name] = []
                        models_found[model_name].append(file_path)
            except Exception as e:
                # Handle permission errors or other issues
                continue
                
        return models_found
        
    def get_model_save_path(self, model_name: str, format_type: str, 
                           capability: str = 'chat') -> Path:
        """
        Get the appropriate path for saving a new model
        
        Args:
            model_name: Name of the model
            format_type: Format type (e.g., 'gguf', 'safetensors')
            capability: Model capability (default: 'chat')
            
        Returns:
            Path where the model should be saved
        """
        if format_type.lower() not in self.format_dirs:
            # Use Universal directory for unknown formats
            format_dir = self.format_dirs['universal']
        else:
            format_dir = self.format_dirs[format_type.lower()]
            
        if capability not in self.capabilities:
            capability = 'chat'  # Default to chat
            
        save_dir = format_dir / capability
        save_dir.mkdir(parents=True, exist_ok=True)
        
        return save_dir / model_name
        
    def get_download_path(self, filename: str) -> Path:
        """Get path for downloading a model"""
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        return self.downloads_dir / filename
        
    def get_cache_path(self, model_id: str) -> Path:
        """Get cache path for a model"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir / model_id
        
    def __str__(self) -> str:
        """String representation of model paths"""
        return f"ModelPaths(base={self.models_base_dir})"


# Singleton instance
_model_paths = None


def get_model_paths() -> ModelPaths:
    """Get singleton ModelPaths instance"""
    global _model_paths
    if _model_paths is None:
        _model_paths = ModelPaths()
        _model_paths.ensure_directories()
    return _model_paths


# Convenience functions
def get_models_base_dir() -> Path:
    """Get the base models directory for the current user"""
    return get_model_paths().models_base_dir


def get_model_search_paths(format_type: Optional[str] = None, 
                          capability: Optional[str] = None) -> List[Path]:
    """Get model search paths"""
    return get_model_paths().get_model_search_paths(format_type, capability)


def scan_for_models(extensions: Optional[List[str]] = None) -> Dict[str, List[Path]]:
    """Scan for available models"""
    return get_model_paths().scan_for_models(extensions)