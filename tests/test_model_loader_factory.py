"""
Test suite for Model Loader Factory
"""

import os
import json
import struct
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gerdsen_ai_server.src.model_loaders.model_loader_factory import (
    ModelLoaderFactory, 
    ModelFormat, 
    get_factory,
    load_model,
    detect_format,
    validate_model
)


class TestModelLoaderFactory(unittest.TestCase):
    """Test cases for ModelLoaderFactory"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = ModelLoaderFactory()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_file(self, filename: str, content: bytes = b'') -> Path:
        """Create a test file with given content"""
        file_path = Path(self.temp_dir) / filename
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path
        
    def test_format_detection_by_extension(self):
        """Test format detection based on file extensions"""
        test_cases = [
            ('model.gguf', ModelFormat.GGUF),
            ('model.safetensors', ModelFormat.SAFETENSORS),
            ('model.mlx', ModelFormat.MLX),
            ('model.mlmodel', ModelFormat.COREML),
            ('model.pth', ModelFormat.PYTORCH),
            ('model.pt', ModelFormat.PYTORCH),
            ('model.bin', ModelFormat.PYTORCH),
            ('model.onnx', ModelFormat.ONNX),
            ('model.ort', ModelFormat.ONNX),
            ('model.txt', ModelFormat.UNKNOWN),
        ]
        
        for filename, expected_format in test_cases:
            file_path = self.create_test_file(filename)
            detected_format = self.factory.detect_format_from_file(file_path)
            self.assertEqual(detected_format, expected_format,
                           f"Failed to detect {expected_format} for {filename}")
                           
    def test_format_detection_by_content_gguf(self):
        """Test GGUF format detection by magic bytes"""
        # Create a file with GGUF magic bytes
        file_path = self.create_test_file('model.dat', b'GGUF' + b'\x00' * 12)
        detected_format = self.factory.detect_format_from_file(file_path)
        self.assertEqual(detected_format, ModelFormat.GGUF)
        
    def test_format_detection_by_content_onnx(self):
        """Test ONNX format detection by magic bytes"""
        # Create a file with ONNX magic bytes
        file_path = self.create_test_file('model.dat', b'\x08\x01\x12' + b'\x00' * 13)
        detected_format = self.factory.detect_format_from_file(file_path)
        self.assertEqual(detected_format, ModelFormat.ONNX)
        
    def test_format_detection_by_content_safetensors(self):
        """Test SafeTensors format detection"""
        # Create a mock SafeTensors file with JSON header
        header_data = json.dumps({"test": "data"}).encode()
        header_size = len(header_data)
        content = struct.pack('<Q', header_size) + header_data + b'\x00' * 100
        
        file_path = self.create_test_file('model.dat', content)
        detected_format = self.factory.detect_format_from_file(file_path)
        self.assertEqual(detected_format, ModelFormat.SAFETENSORS)
        
    def test_format_detection_by_content_pytorch(self):
        """Test PyTorch format detection by pickle protocol"""
        # Create a file with PyTorch pickle header
        file_path = self.create_test_file('model.dat', b'\x80\x04' + b'\x00' * 14)
        detected_format = self.factory.detect_format_from_file(file_path)
        self.assertEqual(detected_format, ModelFormat.PYTORCH)
        
    def test_content_detection_overrides_extension(self):
        """Test that content detection overrides extension detection"""
        # Create a file with .txt extension but GGUF content
        file_path = self.create_test_file('model.txt', b'GGUF' + b'\x00' * 12)
        detected_format = self.factory.detect_format_from_file(file_path)
        self.assertEqual(detected_format, ModelFormat.GGUF)
        
    def test_create_loader(self):
        """Test loader creation for each format"""
        for format_type in ModelFormat:
            if format_type == ModelFormat.UNKNOWN:
                continue
                
            with patch(f'gerdsen_ai_server.src.model_loaders.model_loader_factory.{format_type.name}Loader') as mock_loader_class:
                mock_loader_instance = Mock()
                mock_loader_class.return_value = mock_loader_instance
                
                loader = self.factory.create_loader(format_type)
                
                if format_type in self.factory.LOADER_CLASSES:
                    self.assertIsNotNone(loader)
                    self.assertEqual(self.factory.loaders[format_type], mock_loader_instance)
                    
    def test_create_loader_unknown_format(self):
        """Test that creating loader for unknown format returns None"""
        loader = self.factory.create_loader(ModelFormat.UNKNOWN)
        self.assertIsNone(loader)
        
    def test_loader_caching(self):
        """Test that loaders are cached and reused"""
        with patch('gerdsen_ai_server.src.model_loaders.model_loader_factory.GGUFLoader') as mock_loader_class:
            mock_instance = Mock()
            mock_loader_class.return_value = mock_instance
            
            # First call creates loader
            loader1 = self.factory.create_loader(ModelFormat.GGUF)
            self.assertEqual(mock_loader_class.call_count, 1)
            
            # Second call returns cached loader
            loader2 = self.factory.create_loader(ModelFormat.GGUF)
            self.assertEqual(mock_loader_class.call_count, 1)
            self.assertIs(loader1, loader2)
            
    def test_load_model_with_auto_detection(self):
        """Test loading a model with automatic format detection"""
        # Create a test GGUF file
        file_path = self.create_test_file('model.gguf', b'GGUF' + b'\x00' * 12)
        
        with patch('gerdsen_ai_server.src.model_loaders.model_loader_factory.GGUFLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_model.return_value = {
                'id': 'test_model',
                'path': str(file_path),
                'info': {'test': 'data'}
            }
            mock_loader_class.return_value = mock_loader
            
            result = self.factory.load_model(file_path, model_id='test_model')
            
            mock_loader.load_model.assert_called_once_with(str(file_path), 'test_model')
            self.assertEqual(result['format'], 'gguf')
            self.assertEqual(result['loader'], 'gguf')
            self.assertEqual(result['id'], 'test_model')
            
    def test_load_model_with_format_hint(self):
        """Test loading a model with format hint"""
        file_path = self.create_test_file('model.bin')
        
        with patch('gerdsen_ai_server.src.model_loaders.model_loader_factory.PyTorchLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_model.return_value = {'data': 'test'}
            mock_loader_class.return_value = mock_loader
            
            # Load with format hint
            result = self.factory.load_model(file_path, format_hint=ModelFormat.PYTORCH)
            
            mock_loader.load_model.assert_called_once()
            self.assertEqual(result['format'], 'pytorch')
            
    def test_load_model_file_not_found(self):
        """Test loading non-existent file raises error"""
        with self.assertRaises(FileNotFoundError):
            self.factory.load_model('/non/existent/file.gguf')
            
    def test_load_model_unknown_format(self):
        """Test loading file with unknown format raises error"""
        file_path = self.create_test_file('model.xyz')
        
        with self.assertRaises(ValueError) as cm:
            self.factory.load_model(file_path)
            
        self.assertIn("Unable to detect model format", str(cm.exception))
        
    def test_validate_model_file(self):
        """Test model file validation"""
        # Create a test GGUF file
        file_path = self.create_test_file('model.gguf', b'GGUF' + b'\x00' * 100)
        
        with patch('gerdsen_ai_server.src.model_loaders.model_loader_factory.GGUFLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.validate_file.return_value = True
            mock_loader_class.return_value = mock_loader
            
            result = self.factory.validate_model_file(file_path)
            
            self.assertTrue(result['valid'])
            self.assertEqual(result['format'], 'gguf')
            self.assertTrue(result['exists'])
            self.assertIn('size_bytes', result['metadata'])
            self.assertIn('size_mb', result['metadata'])
            
    def test_validate_model_file_not_found(self):
        """Test validation of non-existent file"""
        result = self.factory.validate_model_file('/non/existent/file.gguf')
        
        self.assertFalse(result['valid'])
        self.assertFalse(result['exists'])
        self.assertIn("File not found", result['errors'][0])
        
    def test_validate_model_without_validator_method(self):
        """Test validation when loader lacks validate_file method"""
        file_path = self.create_test_file('model.safetensors')
        
        with patch('gerdsen_ai_server.src.model_loaders.model_loader_factory.SafeTensorsLoader') as mock_loader_class:
            mock_loader = Mock(spec=[])  # No validate_file method
            mock_loader_class.return_value = mock_loader
            
            result = self.factory.validate_model_file(file_path)
            
            self.assertTrue(result['valid'])  # Basic validation passes
            self.assertIn("Full validation not available", result['warnings'][0])
            
    def test_get_supported_formats(self):
        """Test getting supported formats information"""
        formats = self.factory.get_supported_formats()
        
        # Check all formats except UNKNOWN are included
        expected_formats = [fmt.value for fmt in ModelFormat if fmt != ModelFormat.UNKNOWN]
        self.assertEqual(set(formats.keys()), set(expected_formats))
        
        # Check format info structure
        for format_name, info in formats.items():
            self.assertIn('name', info)
            self.assertIn('extensions', info)
            self.assertIn('has_loader', info)
            self.assertIn('description', info)
            self.assertIsInstance(info['extensions'], list)
            
    def test_unload_model_with_format_hint(self):
        """Test unloading model with format hint"""
        with patch('gerdsen_ai_server.src.model_loaders.model_loader_factory.GGUFLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.unload_model.return_value = True
            mock_loader_class.return_value = mock_loader
            
            # Create loader first
            self.factory.create_loader(ModelFormat.GGUF)
            
            # Unload with format hint
            result = self.factory.unload_model('test_model', ModelFormat.GGUF)
            
            mock_loader.unload_model.assert_called_once_with('test_model')
            self.assertTrue(result)
            
    def test_unload_model_search_all_loaders(self):
        """Test unloading model searches all loaders"""
        # Create multiple mock loaders
        mock_loaders = {}
        for format_type in [ModelFormat.GGUF, ModelFormat.SAFETENSORS, ModelFormat.PYTORCH]:
            mock_loader = Mock()
            mock_loader.unload_model.return_value = False
            mock_loaders[format_type] = mock_loader
            self.factory.loaders[format_type] = mock_loader
            
        # Make PyTorch loader return True
        mock_loaders[ModelFormat.PYTORCH].unload_model.return_value = True
        
        result = self.factory.unload_model('test_model')
        
        # Check all loaders were tried until success
        mock_loaders[ModelFormat.GGUF].unload_model.assert_called_once_with('test_model')
        mock_loaders[ModelFormat.SAFETENSORS].unload_model.assert_called_once_with('test_model')
        mock_loaders[ModelFormat.PYTORCH].unload_model.assert_called_once_with('test_model')
        self.assertTrue(result)
        
    def test_get_loaded_models(self):
        """Test getting all loaded models across loaders"""
        # Set up mock loaders with different return formats
        mock_gguf_loader = Mock()
        mock_gguf_loader.list_loaded_models.return_value = {
            'model1': {'id': 'model1', 'path': '/path/to/model1.gguf'},
            'model2': {'id': 'model2', 'path': '/path/to/model2.gguf'}
        }
        
        mock_st_loader = Mock()
        mock_st_loader.list_loaded_models.return_value = ['model3', 'model4']
        
        self.factory.loaders[ModelFormat.GGUF] = mock_gguf_loader
        self.factory.loaders[ModelFormat.SAFETENSORS] = mock_st_loader
        
        all_models = self.factory.get_loaded_models()
        
        # Check all models are included
        self.assertEqual(len(all_models), 4)
        self.assertIn('model1', all_models)
        self.assertIn('model2', all_models)
        self.assertIn('model3', all_models)
        self.assertIn('model4', all_models)
        
        # Check format info is added
        self.assertEqual(all_models['model1']['format'], 'gguf')
        self.assertEqual(all_models['model3']['format'], 'safetensors')
        
    def test_clear_loaders(self):
        """Test clearing all loaders"""
        # Create mock loaders
        mock_loader = Mock()
        mock_loader.list_loaded_models.return_value = {'model1': {}}
        mock_loader.unload_model.return_value = True
        
        self.factory.loaders[ModelFormat.GGUF] = mock_loader
        
        self.factory.clear_loaders()
        
        mock_loader.unload_model.assert_called_once_with('model1')
        self.assertEqual(len(self.factory.loaders), 0)
        
    def test_singleton_factory(self):
        """Test singleton factory pattern"""
        factory1 = get_factory()
        factory2 = get_factory()
        self.assertIs(factory1, factory2)
        
    def test_convenience_functions(self):
        """Test convenience functions"""
        file_path = self.create_test_file('model.gguf', b'GGUF' + b'\x00' * 12)
        
        # Test detect_format
        detected = detect_format(file_path)
        self.assertEqual(detected, 'gguf')
        
        # Test validate_model
        with patch('gerdsen_ai_server.src.model_loaders.model_loader_factory.GGUFLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.validate_file.return_value = True
            mock_loader_class.return_value = mock_loader
            
            result = validate_model(file_path)
            self.assertTrue(result['valid'])
            
        # Test load_model
        with patch('gerdsen_ai_server.src.model_loaders.model_loader_factory.GGUFLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_model.return_value = {'id': 'test'}
            mock_loader_class.return_value = mock_loader
            
            result = load_model(file_path)
            self.assertIn('format', result)
            
    def test_directory_format_detection_mlx(self):
        """Test MLX format detection for directories"""
        # Create MLX directory structure
        mlx_dir = Path(self.temp_dir) / 'mlx_model'
        mlx_dir.mkdir()
        (mlx_dir / 'model.safetensors').touch()
        (mlx_dir / 'config.json').touch()
        (mlx_dir / 'model.safetensors.index.json').touch()
        
        format_type = self.factory.detect_format_from_file(mlx_dir)
        self.assertEqual(format_type, ModelFormat.MLX)
        
    def test_directory_format_detection_coreml(self):
        """Test CoreML format detection for directories"""
        # Create CoreML directory
        coreml_dir = Path(self.temp_dir) / 'model.mlmodel'
        coreml_dir.mkdir()
        
        format_type = self.factory.detect_format_from_file(coreml_dir)
        self.assertEqual(format_type, ModelFormat.COREML)


class TestModelFormatEnum(unittest.TestCase):
    """Test ModelFormat enum"""
    
    def test_enum_values(self):
        """Test enum has expected values"""
        expected_values = ['gguf', 'safetensors', 'mlx', 'coreml', 'pytorch', 'onnx', 'unknown']
        actual_values = [fmt.value for fmt in ModelFormat]
        self.assertEqual(set(actual_values), set(expected_values))


if __name__ == '__main__':
    unittest.main()