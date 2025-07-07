#!/usr/bin/env python3
"""
Unit tests for production configuration
"""

import os
import sys
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gerdsen_ai_server.src.production_gerdsen_ai import ProductionConfig

class TestProductionConfig(unittest.TestCase):
    """Test production configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ProductionConfig()
        
        # Check that default values are set
        self.assertIsNotNone(config.server_port)
        self.assertIsNotNone(config.log_level)
        self.assertIsNotNone(config.models_directory)
        self.assertIsNotNone(config.max_concurrent_models)
        
        # Default values should be reasonable
        self.assertGreater(config.server_port, 0)
        self.assertGreater(config.max_concurrent_models, 0)
        self.assertIn(config.log_level.lower(), ['debug', 'info', 'warning', 'error', 'critical'])
    
    def test_config_serialization(self):
        """Test configuration serialization"""
        config = ProductionConfig()
        config.server_port = 8080
        config.log_level = "INFO"
        config.models_directory = "/path/to/models"
        config.max_concurrent_models = 3
        
        # Test to_dict method
        config_dict = config.to_dict()
        self.assertEqual(config_dict['server_port'], 8080)
        self.assertEqual(config_dict['log_level'], "INFO")
        self.assertEqual(config_dict['models_directory'], "/path/to/models")
        self.assertEqual(config_dict['max_concurrent_models'], 3)
        
        # Test to_json method
        config_json = config.to_json()
        self.assertIsInstance(config_json, str)
        
        # Should be valid JSON
        parsed_json = json.loads(config_json)
        self.assertEqual(parsed_json['server_port'], 8080)
        
        # Test from_dict method
        new_config = ProductionConfig.from_dict(config_dict)
        self.assertEqual(new_config.server_port, 8080)
        self.assertEqual(new_config.log_level, "INFO")
        
        # Test from_json method
        new_config_from_json = ProductionConfig.from_json(config_json)
        self.assertEqual(new_config_from_json.server_port, 8080)
        self.assertEqual(new_config_from_json.log_level, "INFO")


if __name__ == "__main__":
    unittest.main()
