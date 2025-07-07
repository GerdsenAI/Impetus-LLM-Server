#!/usr/bin/env python3
"""
Unit tests for integrated MLX manager
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gerdsen_ai_server.src.integrated_mlx_manager import IntegratedMLXManager

class TestIntegratedMLXManager(unittest.TestCase):
    """Test integrated MLX manager functionality"""
    
    def setUp(self):
        self.manager = IntegratedMLXManager()
    
    def test_initialization(self):
        """Test MLX manager initialization"""
        self.assertIsNotNone(self.manager)
        self.assertTrue(hasattr(self.manager, 'get_loaded_models'))
    
    def test_loaded_models_structure(self):
        """Test loaded models returns proper structure"""
        models = self.manager.get_loaded_models()
        
        self.assertIsInstance(models, list)
        
        # If any models are loaded, check their structure
        if models:
            model = models[0]
            self.assertIsInstance(model, dict)
            
            required_fields = ['name', 'path', 'size', 'loaded_at', 'status']
            for field in required_fields:
                self.assertIn(field, model, f"Missing required field in model: {field}")
    
    def test_performance_metrics(self):
        """Test performance metrics"""
        metrics = self.manager.get_performance_metrics()
        
        self.assertIsInstance(metrics, dict)
        required_fields = ['throughput', 'latency', 'memory_usage']
        
        for field in required_fields:
            self.assertIn(field, metrics, f"Missing required performance metric: {field}")
    
    def test_auto_optimization_toggle(self):
        """Test auto optimization toggle"""
        # Test enabling auto-optimization
        self.manager.set_auto_optimization(True)
        self.assertTrue(self.manager.is_auto_optimization_enabled())
        
        # Test disabling auto-optimization
        self.manager.set_auto_optimization(False)
        self.assertFalse(self.manager.is_auto_optimization_enabled())


if __name__ == "__main__":
    unittest.main()
