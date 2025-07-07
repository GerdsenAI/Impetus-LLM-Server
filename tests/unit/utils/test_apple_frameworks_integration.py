#!/usr/bin/env python3
"""
Unit tests for Apple frameworks integration
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gerdsen_ai_server.src.apple_frameworks_integration import AppleFrameworksIntegration

class TestAppleFrameworksIntegration(unittest.TestCase):
    """Test Apple frameworks integration"""
    
    def setUp(self):
        self.frameworks = AppleFrameworksIntegration()
    
    def test_initialization(self):
        """Test frameworks initialization"""
        self.assertIsNotNone(self.frameworks)
        
        # Test availability checks don't crash
        try:
            coreml_available = self.frameworks.is_coreml_available()
            mlx_available = self.frameworks.is_mlx_available()
            metal_available = self.frameworks.is_metal_available()
            
            # These should return boolean values
            self.assertIsInstance(coreml_available, bool)
            self.assertIsInstance(mlx_available, bool)
            self.assertIsInstance(metal_available, bool)
            
        except Exception as e:
            self.fail(f"Framework availability check failed: {e}")
    
    def test_version_detection(self):
        """Test framework version detection"""
        try:
            coreml_version = self.frameworks.get_coreml_version()
            mlx_version = self.frameworks.get_mlx_version()
            metal_version = self.frameworks.get_metal_version()
            
            # If available, should return version strings
            if self.frameworks.is_coreml_available():
                self.assertIsInstance(coreml_version, str)
            
            if self.frameworks.is_mlx_available():
                self.assertIsInstance(mlx_version, str)
                
            if self.frameworks.is_metal_available():
                self.assertIsInstance(metal_version, str)
                
        except Exception as e:
            self.fail(f"Framework version detection failed: {e}")


if __name__ == "__main__":
    unittest.main()
