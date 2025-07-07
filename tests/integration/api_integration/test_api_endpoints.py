#!/usr/bin/env python3
"""
Integration tests for API endpoints
"""

import os
import sys
import unittest
import json
import threading
import time
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gerdsen_ai_server.src.production_main import ProductionFlaskServer

class TestAPIEndpoints(unittest.TestCase):
    """Test API endpoints functionality"""
    
    def setUp(self):
        # Create server with test configuration
        self.server = ProductionFlaskServer()
        
        # Configure for testing
        self.server.app.config['TESTING'] = True
        self.client = self.server.app.test_client()
        
        # Start server in a separate thread for testing
        def run_server():
            self.server.start_server(host='127.0.0.1', port=8081, debug=False)
            
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Wait for server to start
        time.sleep(1)
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'ok')
    
    def test_hardware_detect_endpoint(self):
        """Test hardware detection endpoint"""
        response = self.client.get('/api/v1/hardware/detect')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('chip_info', data)
    
    def test_models_endpoint(self):
        """Test models listing endpoint"""
        response = self.client.get('/api/v1/models')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
    
    def test_openai_models_endpoint(self):
        """Test OpenAI compatible models endpoint"""
        response = self.client.get('/v1/models')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
    
    def test_chat_completions_endpoint(self):
        """Test chat completions endpoint"""
        payload = {
            "model": "test-model",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        # Mock the inference engine response
        with patch('gerdsen_ai_server.src.routes.openai_api.get_inference_engine') as mock_get_engine:
            mock_engine = Mock()
            mock_engine.create_chat_completion.return_value = {
                "id": "test-id",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "I'm doing well, thank you for asking!"
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": 10,
                    "total_tokens": 30
                }
            }
            mock_get_engine.return_value = mock_engine
            
            response = self.client.post(
                '/v1/chat/completions',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('choices', data)
            self.assertGreater(len(data['choices']), 0)
            self.assertIn('message', data['choices'][0])
            self.assertIn('content', data['choices'][0]['message'])


if __name__ == "__main__":
    unittest.main()
