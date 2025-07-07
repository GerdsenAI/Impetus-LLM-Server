"""
Test GGUF integration with IntegratedMLXManager
"""

import os
import tempfile
import struct
import pytest
from unittest.mock import Mock, patch

from gerdsen_ai_server.src.integrated_mlx_manager import IntegratedMLXManager
from gerdsen_ai_server.src.model_loaders.gguf_loader import GGUFValueType


class TestGGUFIntegration:
    """Test GGUF integration with MLX Manager"""
    
    @pytest.fixture
    def mock_apple_detector(self):
        """Mock Apple Silicon detector"""
        detector = Mock()
        detector.is_apple_silicon = True
        detector.get_system_metrics.return_value = {
            'memory': {'percent': 50.0}
        }
        detector.get_thermal_state.return_value = 'nominal'
        detector.start_monitoring = Mock()
        detector.stop_monitoring = Mock()
        detector.register_optimization_callback = Mock()
        detector.register_thermal_callback = Mock()
        detector.register_power_callback = Mock()
        return detector
    
    @pytest.fixture
    def mock_frameworks(self):
        """Mock Apple frameworks"""
        frameworks = Mock()
        frameworks.optimize_model = Mock(return_value=True)
        frameworks.cleanup = Mock()
        frameworks.coreml_manager = Mock()
        frameworks.coreml_manager.models = {}
        frameworks.mlx_manager = Mock()
        frameworks.mlx_manager.models = {}
        return frameworks
    
    @pytest.fixture
    def manager(self, mock_apple_detector, mock_frameworks):
        """Create MLX manager with mocks"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = IntegratedMLXManager(
                cache_dir=temp_dir,
                apple_detector=mock_apple_detector,
                frameworks=mock_frameworks
            )
            yield manager
            manager.cleanup()
    
    @pytest.fixture
    def mock_gguf_file(self):
        """Create a minimal mock GGUF file"""
        with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as f:
            # Write GGUF header
            f.write(b'GGUF')  # Magic
            f.write(struct.pack('<I', 3))  # Version
            f.write(struct.pack('<Q', 10))  # Tensor count
            f.write(struct.pack('<Q', 6))  # Metadata KV count
            
            # Write metadata
            metadata = [
                ("general.name", GGUFValueType.STRING, "test-gguf-model"),
                ("general.architecture", GGUFValueType.STRING, "llama"),
                ("general.file_type", GGUFValueType.UINT32, 15),  # Q4_K_M
                ("llama.context_length", GGUFValueType.UINT32, 2048),
                ("llama.embedding_length", GGUFValueType.UINT32, 4096),
                ("llama.block_count", GGUFValueType.UINT32, 32),
            ]
            
            for key, value_type, value in metadata:
                # Write key
                f.write(struct.pack('<Q', len(key)))
                f.write(key.encode())
                # Write value type
                f.write(struct.pack('<I', value_type.value))
                # Write value
                if value_type == GGUFValueType.STRING:
                    f.write(struct.pack('<Q', len(value)))
                    f.write(value.encode())
                elif value_type == GGUFValueType.UINT32:
                    f.write(struct.pack('<I', value))
            
            f.flush()
            yield f.name
        
        os.unlink(f.name)
    
    def test_load_gguf_model(self, manager, mock_gguf_file):
        """Test loading a GGUF model"""
        # Load the model
        model_id = manager.load_model(
            model_path=mock_gguf_file,
            model_name="test_gguf",
            framework="auto"
        )
        
        assert model_id is not None
        assert model_id in manager.models
        
        # Check model info
        model_info = manager.models[model_id]
        assert model_info.name == "test_gguf"
        assert model_info.framework.value == "mlx"  # GGUF uses MLX backend
        assert model_info.quantization == "Q4_K_M"
        
        # Check cache data
        cache_data = manager.model_cache.get(model_id)
        assert cache_data is not None
        assert cache_data['loader'] == 'gguf'
        assert 'data' in cache_data
    
    def test_get_gguf_models(self, manager, mock_gguf_file):
        """Test getting GGUF models specifically"""
        # Load a GGUF model
        model_id = manager.load_model(mock_gguf_file, "gguf_model")
        
        # Get GGUF models
        gguf_models = manager.get_gguf_models()
        assert len(gguf_models) == 1
        assert model_id in gguf_models
        assert 'capabilities' in gguf_models[model_id]
        assert 'text-generation' in gguf_models[model_id]['capabilities']
    
    def test_get_loaded_models_includes_gguf(self, manager, mock_gguf_file):
        """Test that get_loaded_models includes GGUF models"""
        # Load a GGUF model
        model_id = manager.load_model(mock_gguf_file, "test_model")
        
        # Get all loaded models
        loaded_models = manager.get_loaded_models()
        assert len(loaded_models) == 1
        assert model_id in loaded_models
        
        model_data = loaded_models[model_id]
        assert model_data['loader'] == 'gguf'
        assert model_data['quantization'] == 'Q4_K_M'
        assert model_data['framework'] == 'mlx'
        assert 'capabilities' in model_data
    
    def test_unload_gguf_model(self, manager, mock_gguf_file):
        """Test unloading a GGUF model"""
        # Load and then unload
        model_id = manager.load_model(mock_gguf_file, "test_model")
        assert model_id in manager.models
        
        # Unload
        success = manager.unload_model(model_id)
        assert success is True
        assert model_id not in manager.models
        assert model_id not in manager.model_cache
    
    def test_mixed_model_types(self, manager, mock_gguf_file):
        """Test loading both GGUF and dummy models"""
        # Load GGUF model
        gguf_id = manager.load_model(mock_gguf_file, "gguf_model")
        
        # Load dummy model
        with patch('gerdsen_ai_server.src.integrated_mlx_manager.load_dummy_model') as mock_load:
            mock_load.return_value = {
                "status": "loaded",
                "format": "mlx",
                "size_bytes": 1000000,
                "parameters": "7B"
            }
            dummy_id = manager.load_model("/fake/model.mlx", "dummy_model")
        
        # Check both are loaded
        all_models = manager.get_loaded_models()
        assert len(all_models) == 2
        assert all_models[gguf_id]['loader'] == 'gguf'
        assert all_models[dummy_id]['loader'] == 'dummy'
        
        # Check GGUF-specific method
        gguf_models = manager.get_gguf_models()
        assert len(gguf_models) == 1
        assert gguf_id in gguf_models
        assert dummy_id not in gguf_models