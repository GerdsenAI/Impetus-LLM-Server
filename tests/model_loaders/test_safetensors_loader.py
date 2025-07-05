"""
Test SafeTensors loader functionality
"""

import os
import tempfile
import pytest
import torch
import safetensors.torch
from gerdsen_ai_server.src.model_loaders.safetensors_loader import SafeTensorsLoader


class TestSafeTensorsLoader:
    @pytest.fixture
    def loader(self):
        return SafeTensorsLoader()
        
    @pytest.fixture
    def sample_model_file(self):
        """Create a sample safetensors file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.safetensors', delete=False) as f:
            # Create some sample tensors
            tensors = {
                'model.layers.0.weight': torch.randn(128, 512),
                'model.layers.0.bias': torch.randn(128),
                'model.layers.1.weight': torch.randn(64, 128),
                'model.layers.1.bias': torch.randn(64),
                'model.embed.weight': torch.randn(1000, 512),
            }
            
            # Save to safetensors format
            safetensors.torch.save_file(tensors, f.name)
            yield f.name
            
        # Cleanup
        if os.path.exists(f.name):
            os.unlink(f.name)
            
    def test_can_load(self, loader):
        """Test format detection"""
        assert loader.can_load("model.safetensors")
        assert loader.can_load("MODEL.SAFETENSORS")
        assert not loader.can_load("model.gguf")
        assert not loader.can_load("model.bin")
        
    def test_load_model(self, loader, sample_model_file):
        """Test loading a safetensors model"""
        model_info = loader.load_model(sample_model_file)
        
        assert model_info is not None
        assert model_info['format'] == 'safetensors'
        assert model_info['file_path'] == sample_model_file
        assert model_info['num_tensors'] == 5
        assert 'model.layers.0.weight' in model_info['tensor_names']
        assert model_info['total_parameters'] > 0
        assert model_info['architecture'] in ['transformer', 'cnn', 'rnn', 'unknown']
        
    def test_load_nonexistent_model(self, loader):
        """Test error handling for missing files"""
        with pytest.raises(FileNotFoundError):
            loader.load_model("/nonexistent/model.safetensors")
            
    def test_model_management(self, loader, sample_model_file):
        """Test model listing and unloading"""
        # Load a model
        loader.load_model(sample_model_file)
        model_id = os.path.splitext(os.path.basename(sample_model_file))[0]
        
        # Check it's listed
        loaded_models = loader.list_loaded_models()
        assert model_id in loaded_models
        
        # Get model info
        info = loader.get_model_info(model_id)
        assert info is not None
        assert info['format'] == 'safetensors'
        
        # Unload model
        success = loader.unload_model(model_id)
        assert success
        
        # Check it's no longer listed
        loaded_models = loader.list_loaded_models()
        assert model_id not in loaded_models
        
    def test_architecture_inference(self, loader):
        """Test architecture detection from tensor names"""
        # Test transformer detection
        tensors = {
            'transformer.h.0.attn.weight': torch.randn(10, 10),
            'transformer.h.0.attention.weight': torch.randn(10, 10),
        }
        with tempfile.NamedTemporaryFile(suffix='.safetensors', delete=False) as f:
            safetensors.torch.save_file(tensors, f.name)
            model_info = loader.load_model(f.name)
            assert model_info['architecture'] == 'transformer'
            os.unlink(f.name)
            
        # Test CNN detection
        tensors = {
            'conv1.weight': torch.randn(10, 10),
            'bn1.weight': torch.randn(10),
        }
        with tempfile.NamedTemporaryFile(suffix='.safetensors', delete=False) as f:
            safetensors.torch.save_file(tensors, f.name)
            model_info = loader.load_model(f.name)
            assert model_info['architecture'] == 'cnn'
            os.unlink(f.name)