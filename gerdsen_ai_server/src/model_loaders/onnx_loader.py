"""
ONNX model loader for cross-platform model support
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import numpy as np

try:
    import onnx
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    onnx = None
    ort = None

logger = logging.getLogger(__name__)


class ONNXLoader:
    """Loader for ONNX format models with cross-platform support"""
    
    def __init__(self):
        self.supported_extensions = ['.onnx']
        self.loaded_models = {}
        self.sessions = {}  # Store ONNX Runtime sessions
        
        if not ONNX_AVAILABLE:
            logger.warning("ONNX/ONNXRuntime not available - ONNX loader functionality will be limited")
            
        # Set up providers based on platform
        self.providers = self._get_providers()
        
    def _get_providers(self) -> List[str]:
        """Get available execution providers for ONNXRuntime"""
        if not ONNX_AVAILABLE:
            return []
            
        available_providers = []
        
        # Check for CoreML provider (Apple Silicon optimization)
        if 'CoreMLExecutionProvider' in ort.get_available_providers():
            available_providers.append('CoreMLExecutionProvider')
            logger.info("CoreML execution provider available for Apple Silicon optimization")
            
        # Check for CUDA provider
        if 'CUDAExecutionProvider' in ort.get_available_providers():
            available_providers.append('CUDAExecutionProvider')
            
        # Check for DirectML provider (Windows)
        if 'DmlExecutionProvider' in ort.get_available_providers():
            available_providers.append('DmlExecutionProvider')
            
        # Always include CPU provider as fallback
        available_providers.append('CPUExecutionProvider')
        
        logger.info(f"Available ONNX execution providers: {available_providers}")
        return available_providers
        
    def can_load(self, file_path: str) -> bool:
        """Check if this loader can handle the given file"""
        return any(file_path.lower().endswith(ext) for ext in self.supported_extensions)
        
    def load_model(self, file_path: str, model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load an ONNX model
        
        Args:
            file_path: Path to the .onnx file
            model_config: Optional configuration for the model
            
        Returns:
            Dictionary containing model information and session
        """
        try:
            logger.info(f"Loading ONNX model from: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Model file not found: {file_path}")
                
            if not ONNX_AVAILABLE:
                raise RuntimeError("ONNX/ONNXRuntime is not available. Please install onnx and onnxruntime to use ONNX models.")
                
            # Load and check the ONNX model
            onnx_model = onnx.load(file_path)
            onnx.checker.check_model(onnx_model)
            
            # Extract model metadata
            metadata = self._extract_metadata(onnx_model)
            
            # Get model architecture info
            architecture_info = self._analyze_architecture(onnx_model)
            
            # Create inference session
            session_options = ort.SessionOptions()
            
            # Apply optimizations
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # Create session with appropriate providers
            providers = model_config.get('providers', self.providers) if model_config else self.providers
            session = ort.InferenceSession(file_path, session_options, providers=providers)
            
            # Get input/output information
            input_info = self._get_input_info(session)
            output_info = self._get_output_info(session)
            
            # Calculate model size and parameters
            model_stats = self._calculate_model_stats(onnx_model)
            
            # Get model info
            model_info = {
                'format': 'onnx',
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'metadata': metadata,
                'config': model_config or {},
                'architecture': architecture_info['type'],
                'architecture_details': architecture_info,
                'input_info': input_info,
                'output_info': output_info,
                'providers': session.get_providers(),
                'opset_version': onnx_model.opset_import[0].version if onnx_model.opset_import else None,
                'total_parameters': model_stats['total_parameters'],
                'total_operations': model_stats['total_operations'],
                'estimated_memory_mb': model_stats['estimated_memory_mb'],
                'graph_nodes': len(onnx_model.graph.node),
                'optimized_for': self._get_optimization_target(session.get_providers())
            }
            
            logger.info(f"Successfully loaded ONNX model: {architecture_info['type']} with {model_stats['total_parameters']:,} parameters")
            logger.info(f"Using providers: {session.get_providers()}")
            
            # Cache the loaded model
            model_id = Path(file_path).stem
            self.loaded_models[model_id] = model_info
            self.sessions[model_id] = session
            
            return model_info
            
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {str(e)}")
            raise
            
    def _extract_metadata(self, onnx_model) -> Dict[str, Any]:
        """Extract metadata from ONNX model"""
        metadata = {}
        
        # Extract basic metadata
        if onnx_model.producer_name:
            metadata['producer'] = onnx_model.producer_name
        if onnx_model.producer_version:
            metadata['producer_version'] = onnx_model.producer_version
        if onnx_model.domain:
            metadata['domain'] = onnx_model.domain
        if onnx_model.model_version:
            metadata['model_version'] = onnx_model.model_version
        if onnx_model.doc_string:
            metadata['description'] = onnx_model.doc_string
            
        # Extract custom metadata
        custom_metadata = {}
        for prop in onnx_model.metadata_props:
            custom_metadata[prop.key] = prop.value
        if custom_metadata:
            metadata['custom'] = custom_metadata
            
        # Extract graph metadata
        graph_metadata = {}
        if onnx_model.graph.name:
            graph_metadata['name'] = onnx_model.graph.name
        if onnx_model.graph.doc_string:
            graph_metadata['description'] = onnx_model.graph.doc_string
        if graph_metadata:
            metadata['graph'] = graph_metadata
            
        return metadata
        
    def _analyze_architecture(self, onnx_model) -> Dict[str, Any]:
        """Analyze model architecture from ONNX graph"""
        op_types = {}
        for node in onnx_model.graph.node:
            op_type = node.op_type
            op_types[op_type] = op_types.get(op_type, 0) + 1
            
        # Determine architecture type based on operations
        architecture_type = 'unknown'
        architecture_details = {
            'operations': op_types,
            'total_ops': sum(op_types.values())
        }
        
        # Check for common patterns
        if 'Conv' in op_types or 'ConvTranspose' in op_types:
            if 'LSTM' in op_types or 'GRU' in op_types:
                architecture_type = 'hybrid_cnn_rnn'
            else:
                architecture_type = 'cnn'
            architecture_details['conv_layers'] = op_types.get('Conv', 0) + op_types.get('ConvTranspose', 0)
            
        elif 'LSTM' in op_types or 'GRU' in op_types or 'RNN' in op_types:
            architecture_type = 'rnn'
            architecture_details['rnn_layers'] = (op_types.get('LSTM', 0) + 
                                                op_types.get('GRU', 0) + 
                                                op_types.get('RNN', 0))
            
        elif 'Attention' in op_types or 'MultiHeadAttention' in op_types:
            architecture_type = 'transformer'
            architecture_details['attention_layers'] = (op_types.get('Attention', 0) + 
                                                      op_types.get('MultiHeadAttention', 0))
            
        elif 'MatMul' in op_types and 'Add' in op_types:
            # Simple feedforward network
            architecture_type = 'feedforward'
            architecture_details['matmul_ops'] = op_types.get('MatMul', 0)
            
        # Check for specific model types in metadata
        if hasattr(onnx_model, 'metadata_props'):
            for prop in onnx_model.metadata_props:
                if prop.key.lower() == 'architecture':
                    architecture_type = prop.value.lower()
                    break
                    
        architecture_details['type'] = architecture_type
        return architecture_details
        
    def _get_input_info(self, session: 'ort.InferenceSession') -> List[Dict[str, Any]]:
        """Get information about model inputs"""
        inputs = []
        for inp in session.get_inputs():
            input_info = {
                'name': inp.name,
                'shape': inp.shape,
                'type': inp.type,
            }
            
            # Calculate tensor size if shape is fully defined
            if all(isinstance(dim, int) for dim in inp.shape):
                input_info['size'] = np.prod(inp.shape)
                
            inputs.append(input_info)
            
        return inputs
        
    def _get_output_info(self, session: 'ort.InferenceSession') -> List[Dict[str, Any]]:
        """Get information about model outputs"""
        outputs = []
        for out in session.get_outputs():
            output_info = {
                'name': out.name,
                'shape': out.shape,
                'type': out.type,
            }
            
            # Calculate tensor size if shape is fully defined
            if all(isinstance(dim, int) for dim in out.shape):
                output_info['size'] = np.prod(out.shape)
                
            outputs.append(output_info)
            
        return outputs
        
    def _calculate_model_stats(self, onnx_model) -> Dict[str, Any]:
        """Calculate model statistics"""
        total_params = 0
        total_ops = 0
        
        # Count parameters from initializers
        for initializer in onnx_model.graph.initializer:
            if hasattr(initializer, 'dims'):
                param_count = 1
                for dim in initializer.dims:
                    param_count *= dim
                total_params += param_count
                
        # Count operations
        total_ops = len(onnx_model.graph.node)
        
        # Estimate memory usage (assuming float32)
        estimated_memory_mb = (total_params * 4) / (1024 * 1024)
        
        return {
            'total_parameters': total_params,
            'total_operations': total_ops,
            'estimated_memory_mb': estimated_memory_mb
        }
        
    def _get_optimization_target(self, providers: List[str]) -> str:
        """Determine optimization target based on providers"""
        if 'CoreMLExecutionProvider' in providers:
            return 'apple_silicon'
        elif 'CUDAExecutionProvider' in providers:
            return 'nvidia_gpu'
        elif 'DmlExecutionProvider' in providers:
            return 'directml'
        else:
            return 'cpu'
            
    def optimize_for_device(self, model_id: str, device_profile: Dict[str, Any]) -> bool:
        """Optimize model for specific device profile"""
        if model_id not in self.loaded_models:
            logger.warning(f"Model {model_id} not loaded")
            return False
            
        try:
            # Determine best providers based on device profile
            optimized_providers = []
            
            # Apple Silicon optimization
            if device_profile.get('platform') == 'darwin' and device_profile.get('has_neural_engine'):
                if 'CoreMLExecutionProvider' in self.providers:
                    optimized_providers.append('CoreMLExecutionProvider')
                    logger.info(f"Optimizing {model_id} for Apple Neural Engine")
                    
            # GPU optimization
            if device_profile.get('has_gpu'):
                if device_profile.get('gpu_vendor') == 'nvidia' and 'CUDAExecutionProvider' in self.providers:
                    optimized_providers.append('CUDAExecutionProvider')
                elif device_profile.get('platform') == 'win32' and 'DmlExecutionProvider' in self.providers:
                    optimized_providers.append('DmlExecutionProvider')
                    
            # Always include CPU as fallback
            optimized_providers.append('CPUExecutionProvider')
            
            # Recreate session with optimized providers
            model_info = self.loaded_models[model_id]
            file_path = model_info['file_path']
            
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # Add device-specific optimizations
            if device_profile.get('platform') == 'darwin':
                # Enable CoreML EP flags for better performance
                provider_options = [{
                    'CoreMLExecutionProvider': {
                        'CoreMLFlags': 'USE_CPU_ONLY=0'  # Use Neural Engine
                    }
                }]
                session = ort.InferenceSession(file_path, session_options, 
                                             providers=optimized_providers,
                                             provider_options=provider_options)
            else:
                session = ort.InferenceSession(file_path, session_options, 
                                             providers=optimized_providers)
                
            # Update session and model info
            self.sessions[model_id] = session
            model_info['providers'] = session.get_providers()
            model_info['optimization_profile'] = device_profile
            model_info['optimized_for'] = self._get_optimization_target(session.get_providers())
            
            logger.info(f"Successfully optimized {model_id} with providers: {session.get_providers()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to optimize model: {e}")
            return False
            
    def run_inference(self, model_id: str, inputs: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Run inference on a loaded model"""
        if model_id not in self.sessions:
            raise ValueError(f"Model {model_id} not loaded")
            
        session = self.sessions[model_id]
        
        # Prepare inputs
        ort_inputs = {}
        for inp in session.get_inputs():
            if inp.name in inputs:
                ort_inputs[inp.name] = inputs[inp.name]
            else:
                raise ValueError(f"Missing required input: {inp.name}")
                
        # Run inference
        outputs = session.run(None, ort_inputs)
        
        # Map outputs to names
        output_names = [out.name for out in session.get_outputs()]
        return dict(zip(output_names, outputs))
        
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        return self.loaded_models.get(model_id)
        
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        if model_id in self.loaded_models:
            # Clear session
            if model_id in self.sessions:
                del self.sessions[model_id]
                
            # Clear model info
            del self.loaded_models[model_id]
            
            # Force garbage collection
            import gc
            gc.collect()
            
            logger.info(f"Unloaded ONNX model: {model_id}")
            return True
        return False
        
    def list_loaded_models(self) -> List[str]:
        """List all currently loaded models"""
        return list(self.loaded_models.keys())
        
    def get_device_info(self) -> Dict[str, Any]:
        """Get information about ONNX Runtime device capabilities"""
        if not ONNX_AVAILABLE:
            return {"available": False, "reason": "ONNX/ONNXRuntime not installed"}
            
        try:
            info = {
                "available": True,
                "version": ort.__version__,
                "providers": ort.get_available_providers(),
                "default_providers": self.providers,
                "device_type": "multi_platform"
            }
            
            # Check for specific optimizations
            optimizations = []
            if 'CoreMLExecutionProvider' in info['providers']:
                optimizations.append('apple_neural_engine')
            if 'CUDAExecutionProvider' in info['providers']:
                optimizations.append('nvidia_cuda')
            if 'DmlExecutionProvider' in info['providers']:
                optimizations.append('directml')
            if 'OpenVINOExecutionProvider' in info['providers']:
                optimizations.append('intel_openvino')
                
            info['optimizations'] = optimizations
            
            return info
        except Exception as e:
            return {"available": True, "error": str(e)}
            
    def validate_model(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate an ONNX model file"""
        try:
            if not ONNX_AVAILABLE:
                return False, "ONNX not installed"
                
            onnx_model = onnx.load(file_path)
            onnx.checker.check_model(onnx_model)
            return True, None
            
        except Exception as e:
            return False, str(e)