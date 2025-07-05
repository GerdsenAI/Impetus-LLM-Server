"""
Tests for GGUF model loader
"""

import os
import struct
import tempfile
import pytest
from pathlib import Path

from gerdsen_ai_server.src.model_loaders.gguf_loader import GGUFLoader, GGUFValueType, GGUFModelInfo


class TestGGUFLoader:
    """Test suite for GGUF loader"""
    
    @pytest.fixture
    def loader(self):
        """Create a GGUF loader instance"""
        return GGUFLoader()
    
    @pytest.fixture
    def mock_gguf_file(self):
        """Create a minimal mock GGUF file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as f:
            # Write GGUF header
            f.write(b'GGUF')  # Magic
            f.write(struct.pack('<I', 3))  # Version
            f.write(struct.pack('<Q', 10))  # Tensor count
            f.write(struct.pack('<Q', 5))  # Metadata KV count
            
            # Write some metadata
            # Key: "general.name"
            f.write(struct.pack('<Q', len("general.name")))
            f.write(b"general.name")
            f.write(struct.pack('<I', GGUFValueType.STRING.value))
            f.write(struct.pack('<Q', len("test-model")))
            f.write(b"test-model")
            
            # Key: "general.architecture"
            f.write(struct.pack('<Q', len("general.architecture")))
            f.write(b"general.architecture")
            f.write(struct.pack('<I', GGUFValueType.STRING.value))
            f.write(struct.pack('<Q', len("llama")))
            f.write(b"llama")
            
            # Key: "llama.context_length"
            f.write(struct.pack('<Q', len("llama.context_length")))
            f.write(b"llama.context_length")
            f.write(struct.pack('<I', GGUFValueType.UINT32.value))
            f.write(struct.pack('<I', 4096))
            
            # Key: "llama.embedding_length"
            f.write(struct.pack('<Q', len("llama.embedding_length")))
            f.write(b"llama.embedding_length")
            f.write(struct.pack('<I', GGUFValueType.UINT32.value))
            f.write(struct.pack('<I', 4096))
            
            # Key: "llama.block_count"
            f.write(struct.pack('<Q', len("llama.block_count")))
            f.write(b"llama.block_count")
            f.write(struct.pack('<I', GGUFValueType.UINT32.value))
            f.write(struct.pack('<I', 32))
            
            f.flush()
            yield f.name
        
        # Cleanup
        os.unlink(f.name)
    
    def test_validate_file_valid(self, loader, mock_gguf_file):
        """Test validation of valid GGUF file"""
        assert loader.validate_file(mock_gguf_file) is True
    
    def test_validate_file_invalid(self, loader):
        """Test validation of invalid file"""
        with tempfile.NamedTemporaryFile() as f:
            f.write(b"NOT_GGUF")
            f.flush()
            assert loader.validate_file(f.name) is False
    
    def test_validate_file_nonexistent(self, loader):
        """Test validation of non-existent file"""
        assert loader.validate_file("/path/to/nonexistent.gguf") is False
    
    def test_read_metadata(self, loader, mock_gguf_file):
        """Test reading metadata from GGUF file"""
        model_info = loader.read_metadata(mock_gguf_file)
        
        assert isinstance(model_info, GGUFModelInfo)
        assert model_info.name == "test-model"
        assert model_info.architecture == "llama"
        assert model_info.context_length == 4096
        assert model_info.embedding_length == 4096
        assert model_info.n_layers == 32
        assert model_info.tensor_count == 10
    
    def test_load_model(self, loader, mock_gguf_file):
        """Test loading a model"""
        model_data = loader.load_model(mock_gguf_file, "test_model")
        
        assert model_data['id'] == "test_model"
        assert model_data['format'] == 'gguf'
        assert model_data['loaded'] is True
        assert 'text-generation' in model_data['capabilities']
        assert 'chat' in model_data['capabilities']
    
    def test_load_model_auto_id(self, loader, mock_gguf_file):
        """Test loading a model with auto-generated ID"""
        model_data = loader.load_model(mock_gguf_file)
        
        assert model_data['id'].startswith('gguf_')
        assert model_data['format'] == 'gguf'
    
    def test_load_nonexistent_model(self, loader):
        """Test loading non-existent model raises error"""
        with pytest.raises(FileNotFoundError):
            loader.load_model("/path/to/nonexistent.gguf")
    
    def test_unload_model(self, loader, mock_gguf_file):
        """Test unloading a model"""
        loader.load_model(mock_gguf_file, "test_model")
        assert loader.unload_model("test_model") is True
        assert loader.get_model_info("test_model") is None
    
    def test_list_loaded_models(self, loader, mock_gguf_file):
        """Test listing loaded models"""
        loader.load_model(mock_gguf_file, "model1")
        
        models = loader.list_loaded_models()
        assert len(models) == 1
        assert "model1" in models
    
    def test_get_model_size_gb(self, loader, mock_gguf_file):
        """Test getting model size in GB"""
        loader.load_model(mock_gguf_file, "test_model")
        size_gb = loader.get_model_size_gb("test_model")
        assert size_gb > 0
    
    def test_estimate_memory_usage(self, loader, mock_gguf_file):
        """Test memory usage estimation"""
        loader.load_model(mock_gguf_file, "test_model")
        memory_estimate = loader.estimate_memory_usage("test_model")
        
        assert 'model_size_gb' in memory_estimate
        assert 'estimated_ram_gb' in memory_estimate
        assert 'context_buffer_gb' in memory_estimate
        assert memory_estimate['estimated_ram_gb'] >= memory_estimate['model_size_gb']
    
    def test_quantization_name_mapping(self, loader):
        """Test quantization name mapping"""
        assert loader._get_quantization_name(0) == "F32"
        assert loader._get_quantization_name(1) == "F16"
        assert loader._get_quantization_name(15) == "Q4_K_M"
        assert loader._get_quantization_name(999) == "Unknown_999"
    
    def test_infer_capabilities(self, loader):
        """Test capability inference"""
        # Test llama model
        model_info = GGUFModelInfo(
            name="llama-7b",
            architecture="llama",
            quantization="Q4_K_M",
            context_length=4096,
            embedding_length=4096,
            n_layers=32,
            n_heads=32,
            n_vocab=32000,
            file_type="Q4_K_M",
            model_size=1000000,
            tensor_count=100,
            metadata={}
        )
        capabilities = loader._infer_capabilities(model_info)
        assert 'text-generation' in capabilities
        assert 'chat' in capabilities
        assert 'completion' in capabilities
        
        # Test code model
        model_info.name = "codellama-7b"
        capabilities = loader._infer_capabilities(model_info)
        assert 'code-generation' in capabilities