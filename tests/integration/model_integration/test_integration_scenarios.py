#!/usr/bin/env python3
"""
Integration tests for full system workflow scenarios
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gerdsen_ai_server.src.production_gerdsen_ai import ProductionGerdsenAI
from gerdsen_ai_server.src.inference import get_inference_engine

class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios"""
    
    def test_full_system_workflow(self):
        """Test complete system workflow"""
        # Create a production app instance
        app = ProductionGerdsenAI()
        
        # Initialize with mocked hardware components to avoid actual hardware checks
        with patch.object(app, 'apple_detector') as mock_detector, \
             patch.object(app, 'frameworks') as mock_frameworks, \
             patch.object(app, 'mlx_manager') as mock_mlx:
            
            # Set up mocks
            mock_detector.initialize.return_value = True
            mock_detector.get_chip_info.return_value = {
                'chip_name': 'Apple M1',
                'architecture': 'arm64',
                'process_node': '5nm',
                'performance_cores': 4,
                'efficiency_cores': 4,
                'gpu_cores': 8
            }
            
            mock_frameworks.initialize.return_value = True
            mock_frameworks.is_mlx_available.return_value = True
            mock_frameworks.get_mlx_version.return_value = '0.5.0'
            
            mock_mlx.get_loaded_models.return_value = []
            
            # Initialize system
            result = app.initialize_system()
            self.assertTrue(result)
            
            # Mock model loading
            with patch('gerdsen_ai_server.src.inference.get_inference_engine') as mock_get_engine:
                mock_engine = Mock()
                mock_engine.load_model_for_inference.return_value = True
                mock_get_engine.return_value = mock_engine
                
                # Test model loading
                model_loaded = app.load_model('test-model', '/fake/path/model.gguf')
                self.assertTrue(model_loaded)
                
                # Test inference
                mock_engine.generate.return_value = "This is a test response"
                response = app.generate_text('test-model', "Hello, how are you?")
                self.assertEqual(response, "This is a test response")
                
                # Test model unloading
                mock_engine.unload_model.return_value = True
                unloaded = app.unload_model('test-model')
                self.assertTrue(unloaded)


if __name__ == "__main__":
    unittest.main()
