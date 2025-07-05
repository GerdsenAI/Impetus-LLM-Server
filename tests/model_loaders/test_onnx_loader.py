"""
Test ONNX loader functionality with comprehensive coverage
"""

import os
import tempfile
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from gerdsen_ai_server.src.model_loaders.onnx_loader import ONNXLoader

# Mock ONNX imports for testing when ONNX is not available
try:
    import onnx
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    onnx = None
    ort = None


class TestONNXLoader:
    @pytest.fixture
    def loader(self):
        """Create an ONNX loader instance"""
        return ONNXLoader()
        
    @pytest.fixture
    def sample_onnx_model(self):
        """Create a sample ONNX model for testing"""
        if not ONNX_AVAILABLE:
            pytest.skip("ONNX not available")
            
        with tempfile.NamedTemporaryFile(suffix='.onnx', delete=False) as f:
            # Create a simple ONNX model
            from onnx import helper, TensorProto
            
            # Create input and output
            X = helper.make_tensor_value_info('X', TensorProto.FLOAT, [None, 3, 224, 224])
            Y = helper.make_tensor_value_info('Y', TensorProto.FLOAT, [None, 1000])
            
            # Create a weight tensor
            weight = helper.make_tensor(
                'weight',
                TensorProto.FLOAT,
                [1000, 3, 7, 7],
                np.random.randn(1000, 3, 7, 7).astype(np.float32).tobytes(),
                raw=True
            )
            
            # Create a bias tensor
            bias = helper.make_tensor(
                'bias',
                TensorProto.FLOAT,
                [1000],
                np.random.randn(1000).astype(np.float32).tobytes(),
                raw=True
            )
            
            # Create nodes
            conv_node = helper.make_node(
                'Conv',
                inputs=['X', 'weight', 'bias'],
                outputs=['conv_output'],
                kernel_shape=[7, 7],
                strides=[2, 2]
            )
            
            relu_node = helper.make_node(
                'Relu',
                inputs=['conv_output'],
                outputs=['relu_output']
            )
            
            pool_node = helper.make_node(
                'GlobalAveragePool',
                inputs=['relu_output'],
                outputs=['Y']
            )
            
            # Create the graph
            graph_def = helper.make_graph(
                [conv_node, relu_node, pool_node],
                'test_model',
                [X],
                [Y],
                [weight, bias]
            )
            
            # Create the model
            model_def = helper.make_model(graph_def, producer_name='test_producer')
            model_def.opset_import[0].version = 13
            
            # Add metadata
            model_def.metadata_props.append(
                helper.make_model_props('architecture', 'cnn')
            )
            model_def.metadata_props.append(
                helper.make_model_props('description', 'Test CNN model')
            )
            
            # Save the model
            onnx.save(model_def, f.name)
            yield f.name
            
        # Cleanup
        if os.path.exists(f.name):
            os.unlink(f.name)
            
    @pytest.fixture
    def transformer_onnx_model(self):
        """Create a transformer-style ONNX model for testing"""
        if not ONNX_AVAILABLE:
            pytest.skip("ONNX not available")
            
        with tempfile.NamedTemporaryFile(suffix='.onnx', delete=False) as f:
            from onnx import helper, TensorProto
            
            # Create input and output
            X = helper.make_tensor_value_info('input_ids', TensorProto.INT64, [None, None])
            Y = helper.make_tensor_value_info('logits', TensorProto.FLOAT, [None, None, 50257])
            
            # Create a simple attention node (simplified)
            attention_node = helper.make_node(
                'Attention',
                inputs=['input_ids'],
                outputs=['attention_output'],
                num_heads=12
            )
            
            # Create output projection
            matmul_node = helper.make_node(
                'MatMul',
                inputs=['attention_output', 'output_weight'],
                outputs=['logits']
            )
            
            # Create weight
            weight = helper.make_tensor(
                'output_weight',
                TensorProto.FLOAT,
                [768, 50257],
                np.random.randn(768, 50257).astype(np.float32).tobytes(),
                raw=True
            )
            
            # Create the graph
            graph_def = helper.make_graph(
                [attention_node, matmul_node],
                'transformer_model',
                [X],
                [Y],
                [weight]
            )
            
            # Create the model
            model_def = helper.make_model(graph_def, producer_name='test_transformer')
            model_def.opset_import[0].version = 13
            
            # Save the model
            onnx.save(model_def, f.name)
            yield f.name
            
        if os.path.exists(f.name):
            os.unlink(f.name)
            
    def test_initialization(self, loader):
        """Test loader initialization"""
        assert loader.supported_extensions == ['.onnx']
        assert isinstance(loader.loaded_models, dict)
        assert isinstance(loader.sessions, dict)
        assert isinstance(loader.providers, list)
        
    def test_can_load(self, loader):
        """Test format detection"""
        assert loader.can_load("model.onnx")
        assert loader.can_load("MODEL.ONNX")
        assert loader.can_load("/path/to/model.onnx")
        assert not loader.can_load("model.bin")
        assert not loader.can_load("model.safetensors")
        assert not loader.can_load("model.mlx")
        
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_load_model(self, loader, sample_onnx_model):
        """Test loading an ONNX model"""
        model_info = loader.load_model(sample_onnx_model)
        
        assert model_info is not None
        assert model_info['format'] == 'onnx'
        assert model_info['file_path'] == sample_onnx_model
        assert model_info['file_size'] > 0
        assert 'metadata' in model_info
        assert model_info['architecture'] == 'cnn'
        assert 'input_info' in model_info
        assert 'output_info' in model_info
        assert 'providers' in model_info
        assert model_info['total_parameters'] > 0
        assert model_info['graph_nodes'] == 3
        
        # Check that model is cached
        model_id = os.path.splitext(os.path.basename(sample_onnx_model))[0]
        assert model_id in loader.loaded_models
        assert model_id in loader.sessions
        
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_load_transformer_model(self, loader, transformer_onnx_model):
        """Test loading a transformer-style model"""
        model_info = loader.load_model(transformer_onnx_model)
        
        assert model_info['architecture'] == 'transformer'
        assert model_info['architecture_details']['type'] == 'transformer'
        
    def test_load_nonexistent_model(self, loader):
        """Test error handling for missing files"""
        with pytest.raises(FileNotFoundError):
            loader.load_model("/nonexistent/model.onnx")
            
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_metadata_extraction(self, loader, sample_onnx_model):
        """Test metadata extraction"""
        model_info = loader.load_model(sample_onnx_model)
        metadata = model_info['metadata']
        
        assert 'producer' in metadata
        assert metadata['producer'] == 'test_producer'
        assert 'custom' in metadata
        assert metadata['custom']['architecture'] == 'cnn'
        assert metadata['custom']['description'] == 'Test CNN model'
        
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_architecture_analysis(self, loader, sample_onnx_model):
        """Test architecture analysis"""
        model_info = loader.load_model(sample_onnx_model)
        arch_details = model_info['architecture_details']
        
        assert arch_details['type'] == 'cnn'
        assert 'operations' in arch_details
        assert 'Conv' in arch_details['operations']
        assert 'Relu' in arch_details['operations']
        assert arch_details['conv_layers'] == 1
        
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_input_output_info(self, loader, sample_onnx_model):
        """Test input/output information extraction"""
        model_info = loader.load_model(sample_onnx_model)
        
        # Check inputs
        assert len(model_info['input_info']) == 1
        input_info = model_info['input_info'][0]
        assert input_info['name'] == 'X'
        assert input_info['shape'] == [None, 3, 224, 224]
        assert 'float' in input_info['type']
        
        # Check outputs
        assert len(model_info['output_info']) == 1
        output_info = model_info['output_info'][0]
        assert output_info['name'] == 'Y'
        assert output_info['shape'] == [None, 1000]
        
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_model_management(self, loader, sample_onnx_model):
        """Test model listing and unloading"""
        # Load a model
        model_info = loader.load_model(sample_onnx_model)
        model_id = os.path.splitext(os.path.basename(sample_onnx_model))[0]
        
        # Check it's listed
        loaded_models = loader.list_loaded_models()
        assert model_id in loaded_models
        
        # Get model info
        info = loader.get_model_info(model_id)
        assert info is not None
        assert info['format'] == 'onnx'
        
        # Unload model
        success = loader.unload_model(model_id)
        assert success
        
        # Check it's no longer listed
        loaded_models = loader.list_loaded_models()
        assert model_id not in loaded_models
        assert model_id not in loader.sessions
        
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_optimize_for_device(self, loader, sample_onnx_model):
        """Test device optimization"""
        # Load model first
        model_info = loader.load_model(sample_onnx_model)
        model_id = os.path.splitext(os.path.basename(sample_onnx_model))[0]
        
        # Test Apple Silicon optimization
        device_profile = {
            'platform': 'darwin',
            'has_neural_engine': True,
            'neural_engine_cores': 16,
            'has_gpu': True
        }
        
        # Mock CoreML provider availability
        with patch('onnxruntime.get_available_providers', return_value=['CoreMLExecutionProvider', 'CPUExecutionProvider']):
            loader.providers = loader._get_providers()
            success = loader.optimize_for_device(model_id, device_profile)
            
            if 'CoreMLExecutionProvider' in loader.providers:
                assert success
                updated_info = loader.get_model_info(model_id)
                assert 'optimization_profile' in updated_info
                assert updated_info['optimized_for'] == 'apple_silicon'
                
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_run_inference(self, loader, sample_onnx_model):
        """Test running inference"""
        # Load model
        model_info = loader.load_model(sample_onnx_model)
        model_id = os.path.splitext(os.path.basename(sample_onnx_model))[0]
        
        # Prepare input
        inputs = {
            'X': np.random.randn(1, 3, 224, 224).astype(np.float32)
        }
        
        # Run inference
        outputs = loader.run_inference(model_id, inputs)
        
        assert 'Y' in outputs
        assert outputs['Y'].shape == (1, 1000)
        
    def test_run_inference_missing_model(self, loader):
        """Test inference with missing model"""
        with pytest.raises(ValueError, match="Model .* not loaded"):
            loader.run_inference("nonexistent_model", {})
            
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_run_inference_missing_input(self, loader, sample_onnx_model):
        """Test inference with missing input"""
        # Load model
        loader.load_model(sample_onnx_model)
        model_id = os.path.splitext(os.path.basename(sample_onnx_model))[0]
        
        # Try to run with missing input
        with pytest.raises(ValueError, match="Missing required input"):
            loader.run_inference(model_id, {})
            
    def test_get_device_info(self, loader):
        """Test device info retrieval"""
        device_info = loader.get_device_info()
        
        assert 'available' in device_info
        if ONNX_AVAILABLE:
            assert device_info['available'] is True
            assert 'version' in device_info
            assert 'providers' in device_info
            assert 'default_providers' in device_info
            assert device_info['device_type'] == 'multi_platform'
        else:
            assert device_info['available'] is False
            assert 'reason' in device_info
            
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_validate_model(self, loader, sample_onnx_model):
        """Test model validation"""
        is_valid, error = loader.validate_model(sample_onnx_model)
        assert is_valid is True
        assert error is None
        
    def test_validate_invalid_model(self, loader):
        """Test validation of invalid model"""
        with tempfile.NamedTemporaryFile(suffix='.onnx', delete=False) as f:
            f.write(b"invalid onnx data")
            f.flush()
            
            is_valid, error = loader.validate_model(f.name)
            assert is_valid is False
            assert error is not None
            
            os.unlink(f.name)
            
    def test_provider_selection(self):
        """Test provider selection logic"""
        loader = ONNXLoader()
        
        if ONNX_AVAILABLE:
            # Test with mocked providers
            with patch('gerdsen_ai_server.src.model_loaders.onnx_loader.ort.get_available_providers', return_value=['CUDAExecutionProvider', 'CPUExecutionProvider']):
                providers = loader._get_providers()
                assert 'CUDAExecutionProvider' in providers
                assert 'CPUExecutionProvider' in providers
        else:
            # When ONNX is not available, should return empty list
            providers = loader._get_providers()
            assert providers == []
            
    def test_optimization_target_detection(self, loader):
        """Test optimization target detection"""
        assert loader._get_optimization_target(['CoreMLExecutionProvider']) == 'apple_silicon'
        assert loader._get_optimization_target(['CUDAExecutionProvider']) == 'nvidia_gpu'
        assert loader._get_optimization_target(['DmlExecutionProvider']) == 'directml'
        assert loader._get_optimization_target(['CPUExecutionProvider']) == 'cpu'
        
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_memory_estimation(self, loader, sample_onnx_model):
        """Test memory usage estimation"""
        model_info = loader.load_model(sample_onnx_model)
        
        assert 'estimated_memory_mb' in model_info
        assert model_info['estimated_memory_mb'] > 0
        
        # Check that memory estimate is reasonable
        # Conv layer: 1000 * 3 * 7 * 7 + bias: 1000 = 147,000 + 1,000 = 148,000 params
        # At 4 bytes per param: 148,000 * 4 / (1024 * 1024) ≈ 0.56 MB
        assert 0.5 < model_info['estimated_memory_mb'] < 1.0
        
    def test_no_onnx_available(self):
        """Test behavior when ONNX is not available"""
        with patch('gerdsen_ai_server.src.model_loaders.onnx_loader.ONNX_AVAILABLE', False):
            loader = ONNXLoader()
            
            # Should still initialize
            assert loader.supported_extensions == ['.onnx']
            
            # Create a dummy file for testing
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.onnx', delete=False) as f:
                f.write(b'dummy content')
                temp_path = f.name
            
            try:
                # Should fail to load
                with pytest.raises(RuntimeError, match="ONNX/ONNXRuntime is not available"):
                    loader.load_model(temp_path)
            finally:
                os.unlink(temp_path)
                
            # Device info should indicate unavailable
            device_info = loader.get_device_info()
            assert device_info['available'] is False
            
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_edge_cases(self, loader):
        """Test edge cases and error handling"""
        # Test with empty model path
        with pytest.raises(FileNotFoundError):
            loader.load_model("")
            
        # Test unloading non-existent model
        assert loader.unload_model("nonexistent") is False
        
        # Test getting info for non-existent model
        assert loader.get_model_info("nonexistent") is None
        
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_concurrent_model_loading(self, loader, sample_onnx_model):
        """Test loading multiple models"""
        # Create a second model file
        with tempfile.NamedTemporaryFile(suffix='.onnx', delete=False) as f2:
            # Copy the first model
            with open(sample_onnx_model, 'rb') as f1:
                f2.write(f1.read())
            second_model = f2.name
            
        try:
            # Load both models
            info1 = loader.load_model(sample_onnx_model)
            info2 = loader.load_model(second_model)
            
            # Check both are loaded
            assert len(loader.list_loaded_models()) == 2
            
            # Unload first model
            model_id1 = os.path.splitext(os.path.basename(sample_onnx_model))[0]
            loader.unload_model(model_id1)
            
            # Check only second remains
            assert len(loader.list_loaded_models()) == 1
            
        finally:
            os.unlink(second_model)