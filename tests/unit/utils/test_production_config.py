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
        self.assertIsNotNone(config.theme)
        self.assertIsNotNone(config.auto_optimize)
        
        # Default values should be reasonable
        self.assertGreater(config.server_port, 0)
        self.assertEqual(config.server_port, 8080)
        self.assertIn(config.log_level.lower(), ['debug', 'info', 'warning', 'error', 'critical'])
        self.assertEqual(config.theme, "dark")
        self.assertTrue(config.auto_optimize)
    
    def test_config_attributes(self):
        """Test configuration attributes"""
        config = ProductionConfig()
        config.server_port = 9090
        config.log_level = "DEBUG"
        config.theme = "light"
        config.auto_optimize = False
        
        # Verify attribute assignment works
        self.assertEqual(config.server_port, 9090)
        self.assertEqual(config.log_level, "DEBUG")
        self.assertEqual(config.theme, "light")
        self.assertFalse(config.auto_optimize)
        
        # Test that we can convert to dict using vars
        config_dict = vars(config)
        self.assertEqual(config_dict['server_port'], 9090)
        self.assertEqual(config_dict['log_level'], "DEBUG")
        self.assertEqual(config_dict['theme'], "light")
        self.assertFalse(config_dict['auto_optimize'])


if __name__ == "__main__":
    unittest.main()
