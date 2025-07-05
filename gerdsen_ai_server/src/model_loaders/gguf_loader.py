"""
GGUF Model Loader for Impetus-LLM-Server
Supports loading and managing GGUF format models
"""

import os
import json
import struct
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import mmap

logger = logging.getLogger(__name__)

class GGUFValueType(Enum):
    """GGUF value types as defined in the format specification"""
    UINT8 = 0
    INT8 = 1
    UINT16 = 2
    INT16 = 3
    UINT32 = 4
    INT32 = 5
    FLOAT32 = 6
    BOOL = 7
    STRING = 8
    ARRAY = 9
    UINT64 = 10
    INT64 = 11
    FLOAT64 = 12

@dataclass
class GGUFModelInfo:
    """Model information extracted from GGUF file"""
    name: str
    architecture: str
    quantization: str
    context_length: int
    embedding_length: int
    n_layers: int
    n_heads: int
    n_vocab: int
    file_type: str
    model_size: int  # in bytes
    tensor_count: int
    metadata: Dict[str, Any]

class GGUFLoader:
    """Loader for GGUF format models"""
    
    # GGUF magic number
    GGUF_MAGIC = b'GGUF'
    GGUF_VERSION = 3
    
    def __init__(self):
        self.logger = logger
        self._loaded_models: Dict[str, Dict[str, Any]] = {}
        
    def validate_file(self, file_path: str) -> bool:
        """Validate if file is a valid GGUF file"""
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                if magic != self.GGUF_MAGIC:
                    return False
                
                # Read version
                version = struct.unpack('<I', f.read(4))[0]
                if version != self.GGUF_VERSION:
                    self.logger.warning(f"GGUF version {version} may not be fully supported")
                
                return True
        except Exception as e:
            self.logger.error(f"Error validating GGUF file: {e}")
            return False
    
    def _read_string(self, f) -> str:
        """Read a GGUF string from file"""
        length = struct.unpack('<Q', f.read(8))[0]
        return f.read(length).decode('utf-8')
    
    def _read_value(self, f, value_type: GGUFValueType) -> Any:
        """Read a typed value from GGUF file"""
        if value_type == GGUFValueType.UINT8:
            return struct.unpack('B', f.read(1))[0]
        elif value_type == GGUFValueType.INT8:
            return struct.unpack('b', f.read(1))[0]
        elif value_type == GGUFValueType.UINT16:
            return struct.unpack('<H', f.read(2))[0]
        elif value_type == GGUFValueType.INT16:
            return struct.unpack('<h', f.read(2))[0]
        elif value_type == GGUFValueType.UINT32:
            return struct.unpack('<I', f.read(4))[0]
        elif value_type == GGUFValueType.INT32:
            return struct.unpack('<i', f.read(4))[0]
        elif value_type == GGUFValueType.FLOAT32:
            return struct.unpack('<f', f.read(4))[0]
        elif value_type == GGUFValueType.BOOL:
            return struct.unpack('?', f.read(1))[0]
        elif value_type == GGUFValueType.STRING:
            return self._read_string(f)
        elif value_type == GGUFValueType.ARRAY:
            array_type = GGUFValueType(struct.unpack('<I', f.read(4))[0])
            length = struct.unpack('<Q', f.read(8))[0]
            return [self._read_value(f, array_type) for _ in range(length)]
        elif value_type == GGUFValueType.UINT64:
            return struct.unpack('<Q', f.read(8))[0]
        elif value_type == GGUFValueType.INT64:
            return struct.unpack('<q', f.read(8))[0]
        elif value_type == GGUFValueType.FLOAT64:
            return struct.unpack('<d', f.read(8))[0]
        else:
            raise ValueError(f"Unknown value type: {value_type}")
    
    def read_metadata(self, file_path: str) -> GGUFModelInfo:
        """Read model metadata from GGUF file"""
        metadata = {}
        
        with open(file_path, 'rb') as f:
            # Skip magic and version
            f.seek(8)
            
            # Read tensor count and metadata key-value count
            tensor_count = struct.unpack('<Q', f.read(8))[0]
            metadata_kv_count = struct.unpack('<Q', f.read(8))[0]
            
            # Read metadata key-value pairs
            for _ in range(metadata_kv_count):
                key = self._read_string(f)
                value_type = GGUFValueType(struct.unpack('<I', f.read(4))[0])
                value = self._read_value(f, value_type)
                metadata[key] = value
        
        # Extract common metadata
        model_info = GGUFModelInfo(
            name=metadata.get('general.name', 'Unknown'),
            architecture=metadata.get('general.architecture', 'llama'),
            quantization=metadata.get('general.file_type', 'unknown'),
            context_length=metadata.get('llama.context_length', 2048),
            embedding_length=metadata.get('llama.embedding_length', 4096),
            n_layers=metadata.get('llama.block_count', 32),
            n_heads=metadata.get('llama.attention.head_count', 32),
            n_vocab=metadata.get('llama.vocab_size', 32000),
            file_type=self._get_quantization_name(metadata.get('general.file_type', 0)),
            model_size=os.path.getsize(file_path),
            tensor_count=tensor_count,
            metadata=metadata
        )
        
        return model_info
    
    def _get_quantization_name(self, file_type: int) -> str:
        """Convert GGUF file type to quantization name"""
        quantization_map = {
            0: "F32",
            1: "F16",
            2: "Q4_0",
            3: "Q4_1",
            4: "Q4_1_F16",
            7: "Q8_0",
            8: "Q5_0",
            9: "Q5_1",
            10: "Q2_K",
            11: "Q3_K_S",
            12: "Q3_K_M",
            13: "Q3_K_L",
            14: "Q4_K_S",
            15: "Q4_K_M",
            16: "Q5_K_S",
            17: "Q5_K_M",
            18: "Q6_K",
            19: "Q8_K",
        }
        return quantization_map.get(file_type, f"Unknown_{file_type}")
    
    def load_model(self, model_path: str, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Load a GGUF model and return model information"""
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        if not self.validate_file(model_path):
            raise ValueError(f"Invalid GGUF file: {model_path}")
        
        # Read model metadata
        model_info = self.read_metadata(model_path)
        
        # Generate model ID if not provided
        if not model_id:
            model_id = f"gguf_{Path(model_path).stem}"
        
        # Store model information
        model_data = {
            'id': model_id,
            'path': model_path,
            'format': 'gguf',
            'info': model_info,
            'loaded': True,
            'capabilities': self._infer_capabilities(model_info),
            'memory_mapped': None  # Will be set when actually loading for inference
        }
        
        self._loaded_models[model_id] = model_data
        
        self.logger.info(f"Loaded GGUF model: {model_id}")
        self.logger.info(f"  - Architecture: {model_info.architecture}")
        self.logger.info(f"  - Quantization: {model_info.file_type}")
        self.logger.info(f"  - Context Length: {model_info.context_length}")
        self.logger.info(f"  - Model Size: {model_info.model_size / (1024**3):.2f} GB")
        
        return model_data
    
    def _infer_capabilities(self, model_info: GGUFModelInfo) -> List[str]:
        """Infer model capabilities from metadata"""
        capabilities = ['text-generation']
        
        # Check for chat template
        if 'tokenizer.chat_template' in model_info.metadata:
            capabilities.append('chat')
        
        # Check for specific architectures
        arch = model_info.architecture.lower()
        if 'llama' in arch or 'mistral' in arch:
            capabilities.append('chat')
            capabilities.append('completion')
        
        if 'code' in model_info.name.lower():
            capabilities.append('code-generation')
        
        return capabilities
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        if model_id in self._loaded_models:
            model_data = self._loaded_models[model_id]
            
            # Close memory mapped file if exists
            if model_data.get('memory_mapped'):
                model_data['memory_mapped'].close()
            
            del self._loaded_models[model_id]
            self.logger.info(f"Unloaded model: {model_id}")
            return True
        
        return False
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        return self._loaded_models.get(model_id)
    
    def list_loaded_models(self) -> Dict[str, Dict[str, Any]]:
        """List all loaded models"""
        return self._loaded_models.copy()
    
    def memory_map_model(self, model_id: str) -> Optional[mmap.mmap]:
        """Memory map a model file for efficient access"""
        if model_id not in self._loaded_models:
            return None
        
        model_data = self._loaded_models[model_id]
        
        # If already mapped, return existing mapping
        if model_data.get('memory_mapped'):
            return model_data['memory_mapped']
        
        try:
            # Open file and create memory mapping
            f = open(model_data['path'], 'rb')
            mmapped = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            
            model_data['memory_mapped'] = mmapped
            model_data['file_handle'] = f
            
            return mmapped
        except Exception as e:
            self.logger.error(f"Failed to memory map model {model_id}: {e}")
            return None
    
    def get_model_size_gb(self, model_id: str) -> float:
        """Get model size in GB"""
        if model_id not in self._loaded_models:
            return 0.0
        
        model_info = self._loaded_models[model_id]['info']
        return model_info.model_size / (1024**3)
    
    def estimate_memory_usage(self, model_id: str) -> Dict[str, float]:
        """Estimate memory usage for a model"""
        if model_id not in self._loaded_models:
            return {}
        
        model_info = self._loaded_models[model_id]['info']
        model_size_gb = self.get_model_size_gb(model_id)
        
        # Rough estimates based on quantization
        overhead_factor = {
            'F32': 1.2,
            'F16': 1.15,
            'Q8_0': 1.1,
            'Q6_K': 1.08,
            'Q5_K_M': 1.07,
            'Q4_K_M': 1.05,
            'Q4_0': 1.05,
            'Q3_K_M': 1.04,
            'Q2_K': 1.03,
        }
        
        factor = overhead_factor.get(model_info.file_type, 1.1)
        
        return {
            'model_size_gb': model_size_gb,
            'estimated_ram_gb': model_size_gb * factor,
            'context_buffer_gb': (model_info.context_length * model_info.embedding_length * 2) / (1024**3),
        }