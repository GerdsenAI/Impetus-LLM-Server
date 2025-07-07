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
        
        # Check that chip_name exists
        self.assertIn('chip_name', chip_info, "Missing required field: chip_name")
        
        # Check that specifications exist and contain expected fields
        self.assertIn('specifications', chip_info, "Missing specifications dictionary")
        specs = chip_info['specifications']
        
        required_spec_fields = [
            'chip_name', 'cpu_cores_performance', 'cpu_cores_efficiency', 'gpu_cores', 'process_node'
        ]
        
        for field in required_spec_fields:
            self.assertIn(field, specs, f"Missing required specification field: {field}")
    
    def test_optimization_recommendations(self):
        """Test optimization recommendations"""
        recommendations = self.detector.get_optimization_recommendations()
        
        self.assertIsInstance(recommendations, list)
        
        # If we have recommendations, check their structure
        if recommendations:
            recommendation = recommendations[0]
            self.assertIsInstance(recommendation, dict)
            
            required_fields = ['category', 'priority', 'title', 'description']
            for field in required_fields:
                self.assertIn(field, recommendation, f"Missing required recommendation field: {field}")
    
    def test_capabilities_detection(self):
        """Test capabilities detection"""
        capabilities = self.detector.get_capabilities()
        
        self.assertIsInstance(capabilities, list)
        # Should have at least some basic capabilities
        self.assertGreater(len(capabilities), 0)


if __name__ == "__main__":
    unittest.main()
