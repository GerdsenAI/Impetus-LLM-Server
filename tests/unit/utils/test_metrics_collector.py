#!/usr/bin/env python3
"""
Unit tests for real-time metrics collector
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gerdsen_ai_server.src.production_gerdsen_ai import RealTimeMetricsCollector

class TestRealTimeMetricsCollector(unittest.TestCase):
    """Test real-time metrics collection"""
    
    def setUp(self):
        self.collector = RealTimeMetricsCollector()
    
    def test_cpu_metrics(self):
        """Test CPU metrics collection"""
        cpu_metrics = self.collector.get_cpu_metrics()
        
        self.assertIsInstance(cpu_metrics, dict)
        required_fields = ['usage_percent', 'core_usage', 'temperature']
        
        for field in required_fields:
            self.assertIn(field, cpu_metrics, f"Missing required CPU metric: {field}")
    
    def test_memory_metrics(self):
        """Test memory metrics collection"""
        memory_metrics = self.collector.get_memory_metrics()
        
        self.assertIsInstance(memory_metrics, dict)
        required_fields = ['total', 'available', 'used', 'percent']
        
        for field in required_fields:
            self.assertIn(field, memory_metrics, f"Missing required memory metric: {field}")
    
    def test_thermal_metrics(self):
        """Test thermal metrics collection"""
        thermal_metrics = self.collector.get_thermal_metrics()
        
        self.assertIsInstance(thermal_metrics, dict)
        self.assertIn('sensors', thermal_metrics)
        self.assertIsInstance(thermal_metrics['sensors'], list)
    
    def test_gpu_metrics(self):
        """Test GPU metrics collection"""
        gpu_metrics = self.collector.get_gpu_metrics()
        
        self.assertIsInstance(gpu_metrics, dict)
        required_fields = ['utilization', 'memory_used', 'temperature']
        
        for field in required_fields:
            self.assertIn(field, gpu_metrics, f"Missing required GPU metric: {field}")
    
    def test_network_metrics(self):
        """Test network metrics collection"""
        network_metrics = self.collector.get_network_metrics()
        
        self.assertIsInstance(network_metrics, dict)
        required_fields = ['bytes_sent', 'bytes_recv', 'packets_sent', 'packets_recv']
        
        for field in required_fields:
            self.assertIn(field, network_metrics, f"Missing required network metric: {field}")


if __name__ == "__main__":
    unittest.main()
