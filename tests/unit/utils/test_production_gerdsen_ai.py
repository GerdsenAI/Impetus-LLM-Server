#!/usr/bin/env python3
"""
Unit tests for production GerdsenAI application
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gerdsen_ai_server.src.production_gerdsen_ai import ProductionGerdsenAI, ProductionConfig

class TestProductionGerdsenAI(unittest.TestCase):
    """Test main production application"""
    
    def setUp(self):
        self.app = ProductionGerdsenAI()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "test_config.json")
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_initialization(self):
        """Test application initialization"""
        self.assertIsNotNone(self.app)
        self.assertIsNotNone(self.app.config)
        self.assertIsInstance(self.app.config, ProductionConfig)
        
        # Check that components are initialized
        self.assertIsNotNone(self.app.apple_detector)
        self.assertIsNotNone(self.app.frameworks)
        self.assertIsNotNone(self.app.mlx_manager)
    
    def test_config_loading_and_saving(self):
        """Test configuration loading and saving"""
        # Set some config values
        self.app.config.server_port = 9090
        self.app.config.log_level = "DEBUG"
        
        # Save config
        self.app.config_path = Path(self.config_path)
        self.app._save_config()
        
        # Check file exists
        self.assertTrue(os.path.exists(self.config_path))
        
        # Load config back and verify values
        new_app = ProductionGerdsenAI(self.config_path)
        self.assertEqual(new_app.config.server_port, 9090)
        self.assertEqual(new_app.config.log_level, "DEBUG")
    
    def test_system_initialization(self):
        """Test system initialization"""
        # Mock components to avoid actual hardware checks
        self.app.apple_detector = Mock()
        self.app.apple_detector.get_chip_info = Mock(return_value={'chip_name': 'Apple M1'})
        
        self.app.frameworks = Mock()
        self.app.frameworks.initialize = Mock()
        
        self.app.mlx_manager = Mock()
        self.app.mlx_manager.initialize = Mock()
        self.app.mlx_manager.apply_optimizations = Mock()
        
        # Set auto_optimize to True to test optimization path
        self.app.config.auto_optimize = True
        
        # Test initialization
        self.app.initialize_system()
        
        # Verify method calls
        self.app.apple_detector.get_chip_info.assert_called_once()
        self.app.frameworks.initialize.assert_called_once()
        self.app.mlx_manager.initialize.assert_called_once()
        self.app.mlx_manager.apply_optimizations.assert_called_once()


if __name__ == "__main__":
    unittest.main()
