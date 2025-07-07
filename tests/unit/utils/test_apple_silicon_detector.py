#!/usr/bin/env python3
"""
Unit tests for Apple Silicon detector functionality
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gerdsen_ai_server.src.enhanced_apple_silicon_detector import EnhancedAppleSiliconDetector

class TestAppleSiliconDetector(unittest.TestCase):
    """Test Apple Silicon detection functionality"""
    
    def setUp(self):
        self.detector = EnhancedAppleSiliconDetector()
    
    def test_initialization(self):
        """Test detector initialization"""
        self.assertIsNotNone(self.detector)
        self.assertTrue(hasattr(self.detector, 'get_chip_info'))
    
    def test_chip_info_structure(self):
        """Test chip info returns proper structure"""
        chip_info = self.detector.get_chip_info()
        
        self.assertIsInstance(chip_info, dict)
        
        # Check required fields exist
        required_fields = [
            'chip_name', 'architecture', 'process_node',
            'performance_cores', 'efficiency_cores', 'gpu_cores'
        ]
        
        for field in required_fields:
            self.assertIn(field, chip_info, f"Missing required field: {field}")
    
    def test_optimization_recommendations(self):
        """Test optimization recommendations"""
        recommendations = self.detector.get_optimization_recommendations()
        
        self.assertIsInstance(recommendations, dict)
        self.assertIn('recommendations', recommendations)
        self.assertIsInstance(recommendations['recommendations'], list)
    
    def test_capabilities_detection(self):
        """Test capabilities detection"""
        capabilities = self.detector.get_capabilities()
        
        self.assertIsInstance(capabilities, list)
        # Should have at least some basic capabilities
        self.assertGreater(len(capabilities), 0)


if __name__ == "__main__":
    unittest.main()
