"""
Unit tests for MLX model loader
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

from src.model_loaders.mlx_loader import MLXModel, MLXModelLoader
from src.model_loaders.base import ModelLoadError, ModelNotFoundError, InferenceError


class TestMLXModel:
    """Test MLX model class"""
    
    @pytest.fixture
    def mlx_model(self, tmp_path):
        """Create test MLX model instance"""
        model_path = tmp_path / "test-model"
        model_path.mkdir()
        return MLXModel("test-model", model_path)
    
    def test_mlx_model_init(self, mlx_model):
        """Test MLX model initialization"""
        assert mlx_model.model_id == "test-model"
        assert mlx_model.model_path.name == "test-model"
        assert mlx_model.device == "gpu"
        assert mlx_model.model_instance is None
        assert mlx_model.tokenizer_instance is None
        assert mlx_model.supports_kv_cache
        assert not mlx_model.loaded
    
    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', False)
    def test_load_without_mlx(self, mlx_model):
        """Test loading when MLX is not available"""
        with pytest.raises(ModelLoadError) as exc_info:
            mlx_model.load()
        assert "MLX is not installed" in str(exc_info.value)
    
    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', True)
    @patch('src.model_loaders.mlx_loader.load')
    def test_load_from_local_path(self, mock_load, mlx_model):
        """Test loading model from local path"""
        # Mock MLX load function
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer)
        
        # Create config file
        config = {"model_type": "llama", "hidden_size": 4096}
        config_path = mlx_model.model_path / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        # Load model
        mlx_model.load()
        
        # Verify loading
        assert mlx_model.loaded
        assert mlx_model.model_instance == mock_model
        assert mlx_model.tokenizer_instance == mock_tokenizer
        assert mlx_model.config == config
        assert mlx_model.model_config == config
        
        # Verify MLX was called correctly
        mock_load.assert_called_once_with(
            str(mlx_model.model_path),
            tokenizer_config={},
            model_config={},
            adapter_path=None,
            lazy=True
        )
    
    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', True)
    @patch('src.model_loaders.mlx_loader.load')
    def test_load_from_huggingface(self, mock_load, tmp_path):
        """Test loading model from HuggingFace"""
        # Create model with HF ID
        model = MLXModel("mlx-community/test-model", tmp_path / "nonexistent")
        
        # Mock MLX load
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer)
        
        # Load model
        model.load()
        
        # Should use HF ID directly
        mock_load.assert_called_once_with(
            "mlx-community/test-model",
            tokenizer_config={},
            model_config={},
            adapter_path=None,
            lazy=True
        )
    
    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', True)
    @patch('src.model_loaders.mlx_loader.load')
    def test_load_with_custom_config(self, mock_load, mlx_model):
        """Test loading with custom configuration"""
        mock_load.return_value = (MagicMock(), MagicMock())
        
        # Load with custom config
        mlx_model.load(
            tokenizer_config={"padding_side": "left"},
            model_config={"max_length": 4096},
            adapter_path="/path/to/adapter",
            lazy=False
        )
        
        # Verify custom config was passed
        mock_load.assert_called_once_with(
            str(mlx_model.model_path),
            tokenizer_config={"padding_side": "left"},
            model_config={"max_length": 4096},
            adapter_path="/path/to/adapter",
            lazy=False
        )
    
    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', True)
    @patch('src.model_loaders.mlx_loader.mx.metal.clear_cache')
    def test_unload(self, mock_clear_cache, mlx_model):
        """Test model unloading"""
        # Set up loaded model
        mlx_model.loaded = True
        mlx_model.model_instance = MagicMock()
        mlx_model.tokenizer_instance = MagicMock()
        
        # Unload
        mlx_model.unload()
        
        # Verify unloading
        assert not mlx_model.loaded
        assert mlx_model.model_instance is None
        assert mlx_model.tokenizer_instance is None
        mock_clear_cache.assert_called_once()
    
    def test_generate_not_loaded(self, mlx_model):
        """Test generation when model not loaded"""
        with pytest.raises(InferenceError) as exc_info:
            mlx_model.generate("test prompt")
        assert "Model is not loaded" in str(exc_info.value)
    
    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', True)
    @patch('src.model_loaders.mlx_loader.generate')
    def test_generate_basic(self, mock_generate, mlx_model):
        """Test basic text generation"""
        # Set up loaded model
        mlx_model.loaded = True
        mlx_model.model_instance = MagicMock()
        mlx_model.tokenizer_instance = MagicMock()
        mlx_model.tokenizer_instance.encode.return_value = [1, 2, 3]
        mlx_model.config = {"max_position_embeddings": 2048}
        
        # Mock generate
        mock_generate.return_value = "Generated response"
        
        # Generate
        response = mlx_model.generate(
            "Test prompt",
            max_tokens=50,
            temperature=0.8,
            top_p=0.95
        )
        
        assert response == "Generated response"
        
        # Verify generate was called correctly
        mock_generate.assert_called_once_with(
            mlx_model.model_instance,
            mlx_model.tokenizer_instance,
            prompt="Test prompt",
            max_tokens=50,
            temperature=0.8,
            top_p=0.95,
            repetition_penalty=1.1,
            verbose=False
        )
    
    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', True)
    def test_generate_context_limit(self, mlx_model):
        """Test generation with context window limit"""
        # Set up model with small context
        mlx_model.loaded = True
        mlx_model.model_instance = MagicMock()
        mlx_model.tokenizer_instance = MagicMock()
        mlx_model.tokenizer_instance.encode.return_value = list(range(3000))  # Too many tokens
        mlx_model.config = {"max_position_embeddings": 2048}
        
        # Should raise error
        with pytest.raises(InferenceError) as exc_info:
            mlx_model.generate("Very long prompt")
        assert "exceeds context window" in str(exc_info.value)
    
    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', True)
    @patch('src.model_loaders.mlx_loader.generate')
    def test_generate_with_kv_cache(self, mock_generate, mlx_model):
        """Test generation with KV cache parameters"""
        # Set up model
        mlx_model.loaded = True
        mlx_model.model_instance = MagicMock()
        mlx_model.tokenizer_instance = MagicMock()
        mlx_model.tokenizer_instance.encode.return_value = [1, 2, 3]
        mlx_model.config = {}
        
        mock_generate.return_value = "Cached response"
        
        # Generate with cache params
        response = mlx_model.generate(
            "Test",
            use_cache=True,
            conversation_id="test-conv"
        )
        
        assert response == "Cached response"
    
    def test_tokenize(self, mlx_model):
        """Test tokenization"""
        # Not loaded
        with pytest.raises(InferenceError):
            mlx_model.tokenize("test")
        
        # Set up loaded model
        mlx_model.loaded = True
        mlx_model.tokenizer_instance = MagicMock()
        mlx_model.tokenizer_instance.encode.return_value = [101, 102, 103]
        
        tokens = mlx_model.tokenize("test text")
        assert tokens == [101, 102, 103]
        mlx_model.tokenizer_instance.encode.assert_called_once_with("test text")
    
    def test_detokenize(self, mlx_model):
        """Test detokenization"""
        # Not loaded
        with pytest.raises(InferenceError):
            mlx_model.detokenize([1, 2, 3])
        
        # Set up loaded model
        mlx_model.loaded = True
        mlx_model.tokenizer_instance = MagicMock()
        mlx_model.tokenizer_instance.decode.return_value = "decoded text"
        
        text = mlx_model.detokenize([101, 102, 103])
        assert text == "decoded text"
        mlx_model.tokenizer_instance.decode.assert_called_once_with([101, 102, 103])
    
    def test_get_model_dimensions(self, mlx_model):
        """Test getting model dimensions"""
        # No config - should return defaults
        dims = mlx_model.get_model_dimensions()
        assert dims == {
            'num_layers': 32,
            'num_heads': 32,
            'head_dim': 128,
            'hidden_size': 4096
        }
        
        # With config
        mlx_model.model_config = {
            'num_hidden_layers': 40,
            'num_attention_heads': 40,
            'hidden_size': 5120
        }
        
        dims = mlx_model.get_model_dimensions()
        assert dims == {
            'num_layers': 40,
            'num_heads': 40,
            'head_dim': 128,  # 5120 / 40
            'hidden_size': 5120
        }
    
    @patch('src.model_loaders.mlx_loader.kv_cache_manager')
    def test_clear_conversation_cache(self, mock_cache_manager, mlx_model):
        """Test clearing conversation cache"""
        mock_cache_manager.enabled = True
        mock_cache_manager.clear_cache.return_value = True
        
        result = mlx_model.clear_conversation_cache("test-conv")
        assert result
        mock_cache_manager.clear_cache.assert_called_once_with("test-model", "test-conv")


class TestMLXModelLoader:
    """Test MLX model loader"""
    
    @pytest.fixture
    def loader(self):
        """Create test loader"""
        return MLXModelLoader()
    
    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', False)
    def test_loader_init_without_mlx(self):
        """Test loader initialization without MLX"""
        with patch('src.model_loaders.mlx_loader.logger.warning') as mock_warning:
            loader = MLXModelLoader()
            mock_warning.assert_called_once()
            assert "MLX is not available" in mock_warning.call_args[0][0]
    
    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', True)
    @patch('src.model_loaders.mlx_loader.load')
    @patch('src.model_loaders.mlx_loader.model_warmup_service')
    def test_load_model_basic(self, mock_warmup_service, mock_load, loader, tmp_path):
        """Test basic model loading"""
        # Mock MLX load
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer)
        
        # Mock settings
        with patch('src.model_loaders.mlx_loader.settings') as mock_settings:
            mock_settings.model.models_dir = tmp_path
            
            # Load model
            model = loader.load_model("test-model")
            
            assert isinstance(model, MLXModel)
            assert model.model_id == "test-model"
            assert loader.is_model_loaded("test-model")
            assert loader.loaded_models["test-model"] == model
    
    def test_load_model_already_loaded(self, loader):
        """Test loading already loaded model"""
        # Add to loaded models
        existing_model = MagicMock()
        loader.loaded_models["test-model"] = existing_model
        
        # Try to load again
        model = loader.load_model("test-model")
        
        assert model == existing_model
    
    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', True)
    @patch('src.model_loaders.mlx_loader.load')
    @patch('src.model_loaders.mlx_loader.model_warmup_service')
    def test_load_model_with_warmup(self, mock_warmup_service, mock_load, loader, tmp_path):
        """Test model loading with auto warmup"""
        mock_load.return_value = (MagicMock(), MagicMock())
        
        with patch('src.model_loaders.mlx_loader.settings') as mock_settings:
            mock_settings.model.models_dir = tmp_path
            
            # Load with warmup
            model = loader.load_model(
                "test-model",
                auto_warmup=True,
                warmup_prompts=2,
                warmup_async=False
            )
            
            # Verify warmup was called
            mock_warmup_service.warmup_model.assert_called_once_with(
                model,
                "test-model",
                num_prompts=2,
                async_warmup=False
            )
    
    def test_unload_model(self, loader):
        """Test model unloading"""
        # Add mock model
        mock_model = MagicMock()
        loader.loaded_models["test-model"] = mock_model
        loader.model_configs["test-model"] = {}
        
        # Unload
        result = loader.unload_model("test-model")
        
        assert result
        assert "test-model" not in loader.loaded_models
        assert "test-model" not in loader.model_configs
        mock_model.unload.assert_called_once()
    
    def test_unload_model_not_loaded(self, loader):
        """Test unloading non-existent model"""
        result = loader.unload_model("unknown-model")
        assert not result
    
    def test_list_available_models(self, loader, tmp_path):
        """Test listing available models"""
        with patch('src.model_loaders.mlx_loader.settings') as mock_settings:
            mock_settings.model.models_dir = tmp_path
            
            # Create test model directory
            model_dir = tmp_path / "test-model"
            model_dir.mkdir()
            
            # Create config
            config = {"name": "Test Model", "model_type": "llama"}
            with open(model_dir / "config.json", 'w') as f:
                json.dump(config, f)
            
            # Create some files
            (model_dir / "model.safetensors").write_text("dummy")
            
            # List models
            models = loader.list_available_models()
            
            assert len(models) == 1
            assert models[0]["id"] == "test-model"
            assert models[0]["name"] == "Test Model"
            assert models[0]["type"] == "mlx"
            assert models[0]["loaded"] is False
            assert models[0]["size_gb"] > 0
    
    def test_list_models_with_loaded(self, loader, tmp_path):
        """Test listing models including loaded ones"""
        with patch('src.model_loaders.mlx_loader.settings') as mock_settings:
            mock_settings.model.models_dir = tmp_path
            
            # Add loaded HF model
            mock_model = MagicMock()
            loader.loaded_models["mlx-community/test-model"] = mock_model
            
            models = loader.list_available_models()
            
            # Should include the loaded HF model
            hf_models = [m for m in models if m["id"] == "mlx-community/test-model"]
            assert len(hf_models) == 1
            assert hf_models[0]["loaded"] is True
            assert hf_models[0]["path"] == "huggingface"
    
    @patch('src.model_loaders.mlx_loader.model_warmup_service')
    def test_get_model_info_loaded(self, mock_warmup_service, loader):
        """Test getting info for loaded model"""
        # Set up loaded model
        mock_model = MagicMock()
        mock_model.get_info.return_value = {
            "model_id": "test-model",
            "loaded": True
        }
        loader.loaded_models["test-model"] = mock_model
        
        # Mock warmup status
        mock_status = MagicMock()
        mock_status.is_warmed = True
        mock_status.warmup_time_ms = 150.0
        mock_warmup_service.get_warmup_status.return_value = mock_status
        
        # Get info
        info = loader.get_model_info("test-model")
        
        assert info["model_id"] == "test-model"
        assert info["loaded"] is True
        assert info["warmup"]["is_warmed"] is True
        assert info["warmup"]["warmup_time_ms"] == 150.0
    
    def test_get_model_info_not_found(self, loader, tmp_path):
        """Test getting info for non-existent model"""
        with patch('src.model_loaders.mlx_loader.settings') as mock_settings:
            mock_settings.model.models_dir = tmp_path
            
            with pytest.raises(ModelNotFoundError):
                loader.get_model_info("unknown-model")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])