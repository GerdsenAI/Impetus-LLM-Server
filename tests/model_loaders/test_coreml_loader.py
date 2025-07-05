"""
Test CoreML loader functionality
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from gerdsen_ai_server.src.model_loaders.coreml_loader import CoreMLLoader, COREML_AVAILABLE


class TestCoreMLLoader:
    @pytest.fixture
    def loader(self):
        return CoreMLLoader()
        
    def test_can_load(self, loader):
        """Test format detection"""
        assert loader.can_load("model.mlmodel")
        assert loader.can_load("model.mlpackage")
        assert loader.can_load("MODEL.MLMODEL")
        assert loader.can_load("MODEL.MLPACKAGE")
        assert not loader.can_load("model.gguf")
        assert not loader.can_load("model.safetensors")
        assert not loader.can_load("model.pth")
        
    @pytest.mark.skipif(not COREML_AVAILABLE, reason="CoreMLTools not available")
    def test_load_model_mock(self, loader):
        """Test loading a CoreML model with mocked coremltools"""
        with tempfile.NamedTemporaryFile(suffix='.mlmodel', delete=False) as f:
            # Write some dummy content
            f.write(b"dummy coreml model")
            f.flush()
            
            # Mock the coremltools components
            with patch('gerdsen_ai_server.src.model_loaders.coreml_loader.ct.models.MLModel') as mock_mlmodel:
                # Create mock model and spec
                mock_model = Mock()
                mock_spec = Mock()
                
                # Configure spec
                mock_spec.WhichOneof.return_value = 'neuralNetwork'
                
                # Configure input/output mocks
                mock_input = Mock()
                mock_input.name = 'input'
                mock_input.type.WhichOneof.return_value = 'multiArrayType'
                mock_input.type.multiArrayType.shape = [224, 224, 3]
                mock_input.type.multiArrayType.dataType = 'FLOAT32'
                
                mock_output = Mock()
                mock_output.name = 'output'
                mock_output.type.WhichOneof.return_value = 'multiArrayType'
                mock_output.type.multiArrayType.shape = [1000]
                mock_output.type.multiArrayType.dataType = 'FLOAT32'
                
                mock_spec.description.input = [mock_input]
                mock_spec.description.output = [mock_output]
                
                # Configure metadata - make it None to avoid dict conversion issues
                mock_spec.description.metadata = Mock()
                mock_spec.description.metadata.userDefined = None
                mock_spec.description.metadata.author = 'test_author'
                mock_spec.description.metadata.license = 'MIT'
                mock_spec.description.metadata.versionString = '1.0'
                
                # Configure model
                mock_model.get_spec.return_value = mock_spec
                mock_mlmodel.return_value = mock_model
                
                # Load model
                model_info = loader.load_model(f.name)
                
                assert model_info is not None
                assert model_info['format'] == 'coreml'
                assert model_info['file_path'] == f.name
                assert model_info['model_type'] == 'neural_network'
                assert len(model_info['inputs']) == 1
                assert len(model_info['outputs']) == 1
                assert 'cpu' in model_info['compute_units']
                
            os.unlink(f.name)
            
    def test_load_nonexistent_model(self, loader):
        """Test error handling for missing files"""
        with pytest.raises(FileNotFoundError):
            loader.load_model("/nonexistent/model.mlmodel")
            
    @pytest.mark.skipif(not COREML_AVAILABLE, reason="CoreMLTools not available")
    def test_model_management(self, loader):
        """Test model listing and unloading"""
        with tempfile.NamedTemporaryFile(suffix='.mlmodel', delete=False) as f:
            f.write(b"dummy model")
            f.flush()
            
            with patch('gerdsen_ai_server.src.model_loaders.coreml_loader.ct.models.MLModel') as mock_mlmodel:
                # Setup mock
                mock_model = Mock()
                mock_spec = Mock()
                mock_spec.WhichOneof.return_value = 'neuralNetwork'
                mock_spec.description.input = []
                mock_spec.description.output = []
                mock_model.get_spec.return_value = mock_spec
                mock_mlmodel.return_value = mock_model
                
                # Load model
                loader.load_model(f.name)
                model_id = os.path.splitext(os.path.basename(f.name))[0]
                
                # Check it's listed
                loaded_models = loader.list_loaded_models()
                assert model_id in loaded_models
                
                # Get model info
                info = loader.get_model_info(model_id)
                assert info is not None
                assert info['format'] == 'coreml'
                
                # Unload model
                success = loader.unload_model(model_id)
                assert success
                
                # Check it's no longer listed
                loaded_models = loader.list_loaded_models()
                assert model_id not in loaded_models
                
            os.unlink(f.name)
            
    @pytest.mark.skipif(not COREML_AVAILABLE, reason="CoreMLTools not available")
    def test_model_type_inference(self, loader):
        """Test model type detection"""
        test_cases = [
            ('neuralNetwork', 'neural_network'),
            ('neuralNetworkClassifier', 'classifier'),
            ('neuralNetworkRegressor', 'regressor'),
            ('pipeline', 'pipeline'),
            ('treeEnsembleClassifier', 'tree_classifier'),
            ('treeEnsembleRegressor', 'tree_regressor'),
            ('customType', 'customType')
        ]
        
        for spec_type, expected_type in test_cases:
            with tempfile.NamedTemporaryFile(suffix='.mlmodel', delete=False) as f:
                f.write(b"dummy")
                f.flush()
                
                with patch('gerdsen_ai_server.src.model_loaders.coreml_loader.ct.models.MLModel') as mock_mlmodel:
                    mock_model = Mock()
                    mock_spec = Mock()
                    mock_spec.WhichOneof.return_value = spec_type
                    mock_spec.description.input = []
                    mock_spec.description.output = []
                    mock_model.get_spec.return_value = mock_spec
                    mock_mlmodel.return_value = mock_model
                    
                    model_info = loader.load_model(f.name)
                    assert model_info['model_type'] == expected_type
                    
                os.unlink(f.name)
                
    @pytest.mark.skipif(not COREML_AVAILABLE, reason="CoreMLTools not available")
    def test_compute_unit_optimization(self, loader):
        """Test compute unit optimization"""
        with tempfile.NamedTemporaryFile(suffix='.mlmodel', delete=False) as f:
            f.write(b"dummy")
            f.flush()
            
            with patch('gerdsen_ai_server.src.model_loaders.coreml_loader.ct.models.MLModel') as mock_mlmodel:
                mock_model = Mock()
                mock_spec = Mock()
                mock_spec.WhichOneof.return_value = 'neuralNetwork'
                mock_spec.description.input = []
                mock_spec.description.output = []
                mock_model.get_spec.return_value = mock_spec
                mock_mlmodel.return_value = mock_model
                
                loader.load_model(f.name)
                model_id = os.path.splitext(os.path.basename(f.name))[0]
                
                # Test optimization for different compute units
                assert loader.optimize_for_device(model_id, 'CPU')
                assert loader.optimize_for_device(model_id, 'GPU')
                assert loader.optimize_for_device(model_id, 'ALL')
                assert loader.optimize_for_device(model_id, 'NEURAL_ENGINE')
                
                # Test invalid compute unit
                assert not loader.optimize_for_device(model_id, 'INVALID')
                
            os.unlink(f.name)
            
    def test_get_file_size(self, loader):
        """Test file size calculation"""
        # Test with regular file
        with tempfile.NamedTemporaryFile() as f:
            test_data = b"test data" * 100
            f.write(test_data)
            f.flush()
            
            size = loader._get_file_size(f.name)
            assert size == len(test_data)
            
        # Test with directory (simulating .mlpackage)
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files in the directory
            file1 = os.path.join(tmpdir, 'file1.bin')
            file2 = os.path.join(tmpdir, 'subdir', 'file2.bin')
            os.makedirs(os.path.dirname(file2))
            
            with open(file1, 'wb') as f:
                f.write(b"data1" * 10)
            with open(file2, 'wb') as f:
                f.write(b"data2" * 20)
                
            size = loader._get_file_size(tmpdir)
            assert size == 50 + 100  # Total size of both files