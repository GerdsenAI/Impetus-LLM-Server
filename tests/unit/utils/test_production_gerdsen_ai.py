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
        self.app.save_config(self.config_path)
        
        # Check file exists
        self.assertTrue(os.path.exists(self.config_path))
        
        # Create a new app and load config
        new_app = ProductionGerdsenAI()
        new_app.load_config(self.config_path)
        
        # Check values match
        self.assertEqual(new_app.config.server_port, 9090)
        self.assertEqual(new_app.config.log_level, "DEBUG")
    
    def test_system_initialization(self):
        """Test system initialization"""
        # Mock components to avoid actual hardware checks
        self.app.apple_detector = Mock()
        self.app.frameworks = Mock()
        self.app.mlx_manager = Mock()
        
        # Test initialization
        result = self.app.initialize_system()
        self.assertTrue(result)
        
        # Check that component initializations were called
        self.app.apple_detector.initialize.assert_called_once()
        self.app.frameworks.initialize.assert_called_once()


if __name__ == "__main__":
    unittest.main()
