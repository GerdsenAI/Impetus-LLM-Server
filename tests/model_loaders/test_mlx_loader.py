"""
Test MLX loader functionality
"""

import os
import tempfile
import pytest
import numpy as np
from gerdsen_ai_server.src.model_loaders.mlx_loader import MLXLoader

# Check if MLX is available
try:
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False


class TestMLXLoader:
    @pytest.fixture
    def loader(self):
        return MLXLoader()
        
    @pytest.fixture
    def sample_npz_model(self):
        """Create a sample NPZ model file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as f:
            # Create some sample arrays
            arrays = {
                'transformer.h.0.attn.weight': np.random.randn(128, 512).astype(np.float32),
                'transformer.h.0.attn.bias': np.random.randn(128).astype(np.float32),
                'transformer.h.1.attn.weight': np.random.randn(128, 512).astype(np.float32),
                'transformer.h.1.attn.bias': np.random.randn(128).astype(np.float32),
                'embed.weight': np.random.randn(1000, 512).astype(np.float32),
            }
            
            # Save to NPZ format
            np.savez(f.name, **arrays)
            yield f.name
            
        # Cleanup
        if os.path.exists(f.name):
            os.unlink(f.name)
            
    @pytest.fixture
    def sample_mlx_model(self):
        """Create a sample MLX model file for testing"""
        # For MLX format, we need to ensure the file exists with proper content
        with tempfile.NamedTemporaryFile(suffix='.mlx', delete=False) as f:
            # Save as temporary file first
            temp_npz = f.name + '.npz'
            arrays = {
                'model.layers.0.weight': np.random.randn(64, 256).astype(np.float32),
                'model.layers.0.bias': np.random.randn(64).astype(np.float32),
            }
            np.savez(temp_npz, **arrays)
            
            # Copy content to MLX file
            import shutil
            shutil.move(temp_npz, f.name)
            
            yield f.name
            
        # Cleanup
        if os.path.exists(f.name):
            os.unlink(f.name)
            
    def test_can_load(self, loader):
        """Test format detection"""
        assert loader.can_load("model.mlx")
        assert loader.can_load("model.npz")
        assert loader.can_load("MODEL.MLX")
        assert loader.can_load("MODEL.NPZ")
        assert not loader.can_load("model.gguf")
        assert not loader.can_load("model.safetensors")
        
    @pytest.mark.skipif(not MLX_AVAILABLE, reason="MLX not available")
    def test_load_npz_model(self, loader, sample_npz_model):
        """Test loading an NPZ model"""
        model_info = loader.load_model(sample_npz_model)
        
        assert model_info is not None
        assert model_info['format'] == 'mlx'
        assert model_info['file_path'] == sample_npz_model
        assert model_info['num_arrays'] == 5
        assert 'transformer.h.0.attn.weight' in model_info['array_names']
        assert model_info['total_parameters'] > 0
        assert model_info['device'] == 'metal'
        assert model_info['optimized_for'] == 'apple_silicon'
        assert model_info['architecture'] == 'transformer-mlx'
        
    @pytest.mark.skipif(not MLX_AVAILABLE, reason="MLX not available")
    def test_load_mlx_model(self, loader, sample_mlx_model):
        """Test loading an MLX model"""
        model_info = loader.load_model(sample_mlx_model)
        
        assert model_info is not None
        assert model_info['format'] == 'mlx'
        assert model_info['num_arrays'] == 2
        assert model_info['total_parameters'] > 0
        
    def test_load_nonexistent_model(self, loader):
        """Test error handling for missing files"""
        with pytest.raises(FileNotFoundError):
            loader.load_model("/nonexistent/model.mlx")
            
    @pytest.mark.skipif(not MLX_AVAILABLE, reason="MLX not available")
    def test_model_management(self, loader, sample_npz_model):
        """Test model listing and unloading"""
        # Load a model
        loader.load_model(sample_npz_model)
        model_id = os.path.splitext(os.path.basename(sample_npz_model))[0]
        
        # Check it's listed
        loaded_models = loader.list_loaded_models()
        assert model_id in loaded_models
        
        # Get model info
        info = loader.get_model_info(model_id)
        assert info is not None
        assert info['format'] == 'mlx'
        
        # Unload model
        success = loader.unload_model(model_id)
        assert success
        
        # Check it's no longer listed
        loaded_models = loader.list_loaded_models()
        assert model_id not in loaded_models
        
    def test_device_info(self, loader):
        """Test device information retrieval"""
        device_info = loader.get_device_info()
        assert 'available' in device_info
        
        if MLX_AVAILABLE:
            assert device_info['available'] == True
            assert device_info['backend'] == 'metal'
            assert device_info['device'] == 'apple_silicon'
        else:
            assert device_info['available'] == False
            
    @pytest.mark.skipif(not MLX_AVAILABLE, reason="MLX not available")
    def test_architecture_inference(self, loader):
        """Test architecture detection from array names"""
        # Test transformer detection
        arrays = {'transformer.attention.weight': np.random.randn(10, 10).astype(np.float32)}
        with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as f:
            np.savez(f.name, **arrays)
            model_info = loader.load_model(f.name)
            assert 'transformer' in model_info['architecture']
            os.unlink(f.name)
            
        # Test CNN detection
        arrays = {'conv1.weight': np.random.randn(10, 10).astype(np.float32)}
        with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as f:
            np.savez(f.name, **arrays)
            model_info = loader.load_model(f.name)
            assert 'cnn' in model_info['architecture']
            os.unlink(f.name)
            
    @pytest.mark.skipif(not MLX_AVAILABLE, reason="MLX not available")
    def test_device_optimization(self, loader, sample_npz_model):
        """Test device-specific optimization"""
        loader.load_model(sample_npz_model)
        model_id = os.path.splitext(os.path.basename(sample_npz_model))[0]
        
        device_profile = {
            'gpu_cores': 32,
            'neural_engine_cores': 16,
            'memory_gb': 32
        }
        
        success = loader.optimize_for_device(model_id, device_profile)
        assert success
        
        # Check optimization was recorded
        model_info = loader.get_model_info(model_id)
        assert 'optimization_profile' in model_info
        assert model_info['optimization_profile'] == device_profile