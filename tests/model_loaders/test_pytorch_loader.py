"""
Test PyTorch loader functionality
"""

import os
import tempfile
import pytest
import torch
from gerdsen_ai_server.src.model_loaders.pytorch_loader import PyTorchLoader


class TestPyTorchLoader:
    @pytest.fixture
    def loader(self):
        return PyTorchLoader()
        
    @pytest.fixture
    def sample_state_dict(self):
        """Create a sample PyTorch state dict"""
        return {
            'model.layers.0.weight': torch.randn(128, 512),
            'model.layers.0.bias': torch.randn(128),
            'model.layers.1.weight': torch.randn(64, 128),
            'model.layers.1.bias': torch.randn(64),
            'model.embed.weight': torch.randn(1000, 512),
            'model.transformer.attention.weight': torch.randn(512, 512),
        }
        
    @pytest.fixture
    def sample_pt_file(self, sample_state_dict):
        """Create a sample .pt file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
            torch.save(sample_state_dict, f.name)
            yield f.name
            
        # Cleanup
        if os.path.exists(f.name):
            os.unlink(f.name)
            
    @pytest.fixture
    def sample_pth_file(self, sample_state_dict):
        """Create a sample .pth file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.pth', delete=False) as f:
            torch.save(sample_state_dict, f.name)
            yield f.name
            
        # Cleanup
        if os.path.exists(f.name):
            os.unlink(f.name)
            
    def test_can_load(self, loader):
        """Test format detection"""
        assert loader.can_load("model.pt")
        assert loader.can_load("model.pth")
        assert loader.can_load("model.bin")
        assert loader.can_load("MODEL.PT")
        assert not loader.can_load("model.gguf")
        assert not loader.can_load("model.safetensors")
        
    def test_load_state_dict(self, loader, sample_pt_file):
        """Test loading a PyTorch state dict"""
        model_info = loader.load_model(sample_pt_file)
        
        assert model_info is not None
        assert model_info['format'] == 'pytorch'
        assert model_info['file_path'] == sample_pt_file
        assert model_info['model_type'] == 'state_dict'
        assert model_info['num_parameters'] > 0
        assert model_info['num_layers'] == 6
        assert 'model.layers.0.weight' in model_info['layer_names']
        assert model_info['architecture'] == 'transformer'
        
    def test_load_nonexistent_model(self, loader):
        """Test error handling for missing files"""
        with pytest.raises(FileNotFoundError):
            loader.load_model("/nonexistent/model.pt")
            
    def test_model_management(self, loader, sample_pth_file):
        """Test model listing and unloading"""
        # Load a model
        loader.load_model(sample_pth_file)
        model_id = os.path.splitext(os.path.basename(sample_pth_file))[0]
        
        # Check it's listed
        loaded_models = loader.list_loaded_models()
        assert model_id in loaded_models
        
        # Get model info
        info = loader.get_model_info(model_id)
        assert info is not None
        assert info['format'] == 'pytorch'
        
        # Unload model
        success = loader.unload_model(model_id)
        assert success
        
        # Check it's no longer listed
        loaded_models = loader.list_loaded_models()
        assert model_id not in loaded_models
        
    def test_architecture_inference(self, loader):
        """Test architecture detection from layer names"""
        # Test transformer detection
        state_dict = {
            'transformer.h.0.attn.weight': torch.randn(10, 10),
            'transformer.h.0.attention.weight': torch.randn(10, 10),
        }
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
            torch.save(state_dict, f.name)
            model_info = loader.load_model(f.name)
            assert model_info['architecture'] == 'transformer'
            os.unlink(f.name)
            
        # Test CNN detection
        state_dict = {
            'conv1.weight': torch.randn(10, 10),
            'conv2.weight': torch.randn(10, 10),
        }
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
            torch.save(state_dict, f.name)
            model_info = loader.load_model(f.name)
            assert model_info['architecture'] == 'cnn'
            os.unlink(f.name)
            
        # Test BERT detection
        state_dict = {
            'bert.encoder.layer.0.attention.self.query.weight': torch.randn(10, 10),
            'bert.embeddings.word_embeddings.weight': torch.randn(100, 10),
        }
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
            torch.save(state_dict, f.name)
            model_info = loader.load_model(f.name)
            assert model_info['architecture'] == 'bert'
            os.unlink(f.name)
            
    def test_device_detection(self, loader):
        """Test device selection"""
        device = loader._get_device()
        
        # Should be one of cpu, cuda, or mps
        assert str(device) in ['cpu', 'cuda', 'mps']
        
    def test_device_optimization(self, loader, sample_pt_file):
        """Test device optimization"""
        loader.load_model(sample_pt_file)
        model_id = os.path.splitext(os.path.basename(sample_pt_file))[0]
        
        # Test optimization
        assert loader.optimize_for_device(model_id, 'auto')
        assert loader.optimize_for_device(model_id, 'cpu')
        
        # MPS optimization (Apple Silicon)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            assert loader.optimize_for_device(model_id, 'mps')
            
    def test_full_model_loading(self, loader):
        """Test loading a full PyTorch model (not just state dict)"""
        # Instead of a full model, we'll test with a dict that simulates a full model
        # This is because pickling locally defined classes doesn't work well in tests
        model_dict = {
            '_metadata': {'': {'version': 1}},
            'model': torch.nn.Linear(10, 5),
            'optimizer': None,
            'epoch': 10,
            'loss': 0.5
        }
        
        with tempfile.NamedTemporaryFile(suffix='.pth', delete=False) as f:
            # Save model dict (common pattern for full model saves)
            torch.save(model_dict, f.name, _use_new_zipfile_serialization=False)
            
            # Load it
            model_info = loader.load_model(f.name)
            
            assert model_info is not None
            assert model_info['format'] == 'pytorch'
            assert model_info['model_type'] in ['full_model', 'pickle']
            
            os.unlink(f.name)
            
    def test_bin_file_loading(self, loader):
        """Test loading .bin files (common for Hugging Face models)"""
        state_dict = {
            'model.layers.0.self_attn.q_proj.weight': torch.randn(128, 512),
            'model.layers.0.self_attn.k_proj.weight': torch.randn(128, 512),
            'model.layers.0.self_attn.v_proj.weight': torch.randn(128, 512),
        }
        
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            torch.save(state_dict, f.name)
            
            model_info = loader.load_model(f.name)
            
            assert model_info is not None
            assert model_info['format'] == 'pytorch'
            assert model_info['model_type'] == 'state_dict'
            
            os.unlink(f.name)