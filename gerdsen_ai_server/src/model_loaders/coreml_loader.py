"""
CoreML model loader for iOS/macOS native models
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

try:
    import coremltools as ct
    COREML_AVAILABLE = True
except ImportError:
    COREML_AVAILABLE = False
    ct = None

logger = logging.getLogger(__name__)


class CoreMLLoader:
    """Loader for CoreML format models for Apple platforms"""
    
    def __init__(self):
        self.supported_extensions = ['.mlmodel', '.mlpackage']
        self.loaded_models = {}
        
        if not COREML_AVAILABLE:
            logger.warning("CoreMLTools not available - CoreML loader functionality will be limited")
            
    def can_load(self, file_path: str) -> bool:
        """Check if this loader can handle the given file"""
        return any(file_path.lower().endswith(ext) for ext in self.supported_extensions)
        
    def load_model(self, file_path: str, model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load a CoreML model
        
        Args:
            file_path: Path to the .mlmodel or .mlpackage file
            model_config: Optional configuration for the model
            
        Returns:
            Dictionary containing model information
        """
        try:
            logger.info(f"Loading CoreML model from: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Model file not found: {file_path}")
                
            if not COREML_AVAILABLE:
                raise RuntimeError("CoreMLTools is not available. Please install coremltools to use CoreML models.")
                
            # Load the CoreML model
            model = ct.models.MLModel(file_path)
            
            # Get model specification
            spec = model.get_spec()
            
            # Extract model information
            model_info = {
                'format': 'coreml',
                'file_path': file_path,
                'file_size': self._get_file_size(file_path),
                'model': model,
                'spec': spec,
                'metadata': self._extract_metadata(model, spec),
                'config': model_config or {},
                'compute_units': self._get_compute_units(model)
            }
            
            # Get model description
            model_info['description'] = self._get_model_description(spec)
            
            # Get input/output information
            model_info['inputs'] = self._get_input_info(spec)
            model_info['outputs'] = self._get_output_info(spec)
            
            # Try to determine model type
            model_info['model_type'] = self._infer_model_type(spec)
            
            # Get supported platforms
            model_info['supported_platforms'] = self._get_supported_platforms(model)
            
            logger.info(f"Successfully loaded CoreML model: {model_info['model_type']}")
            
            # Cache the loaded model
            model_id = Path(file_path).stem
            self.loaded_models[model_id] = model_info
            
            return model_info
            
        except Exception as e:
            logger.error(f"Failed to load CoreML model: {str(e)}")
            raise
            
    def _get_file_size(self, file_path: str) -> int:
        """Get the size of a file or directory"""
        path = Path(file_path)
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():  # .mlpackage is a directory
            total_size = 0
            for item in path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
            return total_size
        return 0
        
    def _extract_metadata(self, model: Any, spec: Any) -> Dict[str, Any]:
        """Extract metadata from CoreML model"""
        metadata = {}
        
        # Get model description
        if hasattr(spec, 'description'):
            desc = spec.description
            if hasattr(desc, 'metadata') and desc.metadata:
                # Safely extract user defined metadata
                if hasattr(desc.metadata, 'userDefined') and desc.metadata.userDefined:
                    try:
                        metadata['user_defined'] = dict(desc.metadata.userDefined)
                    except (TypeError, AttributeError):
                        # Handle mocking or missing userDefined
                        metadata['user_defined'] = None
                        
                metadata['author'] = getattr(desc.metadata, 'author', None)
                metadata['license'] = getattr(desc.metadata, 'license', None)
                metadata['version'] = getattr(desc.metadata, 'versionString', None)
            
        # Get model type
        if hasattr(spec, 'WhichOneof'):
            metadata['coreml_type'] = spec.WhichOneof('Type')
            
        return metadata
        
    def _get_compute_units(self, model: Any) -> List[str]:
        """Get available compute units for the model"""
        compute_units = ['cpu']  # CPU is always available
        
        try:
            # Check if GPU is available
            if hasattr(ct.ComputeUnit, 'CPU_AND_GPU'):
                compute_units.append('gpu')
                
            # Check if Neural Engine is available
            if hasattr(ct.ComputeUnit, 'ALL'):
                compute_units.append('neural_engine')
        except:
            pass
            
        return compute_units
        
    def _get_model_description(self, spec: Any) -> Dict[str, Any]:
        """Get model description information"""
        desc = {}
        
        if hasattr(spec, 'description'):
            model_desc = spec.description
            desc['inputs'] = len(model_desc.input)
            desc['outputs'] = len(model_desc.output)
            
        return desc
        
    def _get_input_info(self, spec: Any) -> List[Dict[str, Any]]:
        """Get information about model inputs"""
        inputs = []
        
        if hasattr(spec, 'description'):
            for input_desc in spec.description.input:
                input_info = {
                    'name': input_desc.name,
                    'type': str(input_desc.type.WhichOneof('Type'))
                }
                
                # Get shape information
                if hasattr(input_desc.type, 'multiArrayType'):
                    array_type = input_desc.type.multiArrayType
                    input_info['shape'] = list(array_type.shape)
                    input_info['dataType'] = str(array_type.dataType)
                elif hasattr(input_desc.type, 'imageType'):
                    image_type = input_desc.type.imageType
                    input_info['width'] = image_type.width
                    input_info['height'] = image_type.height
                    input_info['colorSpace'] = str(image_type.colorSpace)
                    
                inputs.append(input_info)
                
        return inputs
        
    def _get_output_info(self, spec: Any) -> List[Dict[str, Any]]:
        """Get information about model outputs"""
        outputs = []
        
        if hasattr(spec, 'description'):
            for output_desc in spec.description.output:
                output_info = {
                    'name': output_desc.name,
                    'type': str(output_desc.type.WhichOneof('Type'))
                }
                
                # Get shape information
                if hasattr(output_desc.type, 'multiArrayType'):
                    array_type = output_desc.type.multiArrayType
                    output_info['shape'] = list(array_type.shape)
                    output_info['dataType'] = str(array_type.dataType)
                    
                outputs.append(output_info)
                
        return outputs
        
    def _infer_model_type(self, spec: Any) -> str:
        """Try to infer the type of CoreML model"""
        if hasattr(spec, 'WhichOneof'):
            model_type = spec.WhichOneof('Type')
            
            if model_type == 'neuralNetwork':
                return 'neural_network'
            elif model_type == 'neuralNetworkClassifier':
                return 'classifier'
            elif model_type == 'neuralNetworkRegressor':
                return 'regressor'
            elif model_type == 'pipeline':
                return 'pipeline'
            elif model_type == 'treeEnsembleClassifier':
                return 'tree_classifier'
            elif model_type == 'treeEnsembleRegressor':
                return 'tree_regressor'
            else:
                return model_type
                
        return 'unknown'
        
    def _get_supported_platforms(self, model: Any) -> Dict[str, bool]:
        """Get supported platforms for the model"""
        platforms = {
            'macOS': True,  # Always supported on macOS
            'iOS': True,    # Usually supported
            'tvOS': False,  # Depends on model
            'watchOS': False  # Depends on model
        }
        
        # TODO: Add more specific platform detection based on model requirements
        
        return platforms
        
    def predict(self, model_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run prediction using a loaded CoreML model"""
        if model_id not in self.loaded_models:
            raise ValueError(f"Model {model_id} not loaded")
            
        model_info = self.loaded_models[model_id]
        model = model_info['model']
        
        try:
            # Run prediction
            output = model.predict(input_data)
            return dict(output)
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
            
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        return self.loaded_models.get(model_id)
        
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        if model_id in self.loaded_models:
            # Remove model reference
            if 'model' in self.loaded_models[model_id]:
                del self.loaded_models[model_id]['model']
            if 'spec' in self.loaded_models[model_id]:
                del self.loaded_models[model_id]['spec']
            del self.loaded_models[model_id]
            
            logger.info(f"Unloaded CoreML model: {model_id}")
            return True
        return False
        
    def list_loaded_models(self) -> List[str]:
        """List all currently loaded models"""
        return list(self.loaded_models.keys())
        
    def optimize_for_device(self, model_id: str, compute_unit: str = 'ALL') -> bool:
        """Optimize model for specific compute unit"""
        if model_id not in self.loaded_models:
            logger.warning(f"Model {model_id} not loaded")
            return False
            
        try:
            model_info = self.loaded_models[model_id]
            
            # Map compute unit string to CoreML compute unit
            compute_unit_map = {
                'CPU': ct.ComputeUnit.CPU_ONLY if ct else None,
                'GPU': ct.ComputeUnit.CPU_AND_GPU if ct else None,
                'ALL': ct.ComputeUnit.ALL if ct else None,
                'NEURAL_ENGINE': ct.ComputeUnit.ALL if ct else None
            }
            
            if compute_unit.upper() in compute_unit_map:
                model_info['preferred_compute_unit'] = compute_unit
                logger.info(f"Set preferred compute unit for {model_id} to {compute_unit}")
                return True
            else:
                logger.warning(f"Unknown compute unit: {compute_unit}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to optimize model: {e}")
            return False