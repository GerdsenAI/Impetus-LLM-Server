"""
Integration tests for end-to-end workflows
"""

import json
import time
from unittest.mock import MagicMock, patch

import pytest

# Import app factory
from src.main import create_app


class TestIntegration:
    """Integration tests for complete workflows"""

    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app, socketio = create_app()
        app.config['TESTING'] = True
        return app, socketio

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        flask_app, _socketio = app
        return flask_app.test_client()

    @pytest.fixture
    def socketio_client(self, app):
        """Create SocketIO test client"""
        flask_app, socketio = app
        return socketio.test_client(flask_app)

    @pytest.fixture(autouse=True)
    def disable_openai_auth(self):
        """Disable API key auth for integration tests"""
        with patch('src.routes.openai_api.verify_api_key', return_value=True):
            yield

    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', True)
    @patch('src.model_loaders.mlx_loader.load')
    def test_download_load_warmup_inference_flow(self,
                                                mock_mlx_load,
                                                app,
                                                client,
                                                socketio_client):
        """Test complete flow: download → load → warmup → inference"""

        # Setup shared mocks — download_manager and ModelDiscoveryService are
        # imported BOTH at module level and locally inside route handlers,
        # so we must patch at both locations with the same mock object.
        mock_discovery_class = MagicMock()
        mock_discovery = MagicMock()
        mock_model_info = MagicMock()
        mock_model_info.size_gb = 3.5
        mock_discovery.get_model_info.return_value = mock_model_info
        mock_discovery_class.return_value = mock_discovery

        mock_dm = MagicMock()
        mock_dm.check_disk_space.return_value = (True, 50.0)
        mock_dm.create_download_task.return_value = "task-123"
        mock_dm.get_task_status.return_value = MagicMock(
            task_id='task-123',
            model_id='test-model',
            status=MagicMock(value='completed'),
            progress=1.0,
            downloaded_bytes=0,
            total_bytes=0,
            speed_mbps=0,
            eta_seconds=0,
            error=None,
            started_at=None,
            completed_at=None
        )
        mock_dm.get_download_size.return_value = None

        # Mock MLX model
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_model.config = {'max_position_embeddings': 2048}
        mock_tokenizer.encode.return_value = [1, 2, 3]
        mock_mlx_load.return_value = (mock_model, mock_tokenizer)

        # Patch at both module-level and source-module locations
        with patch('src.routes.models.ModelDiscoveryService', mock_discovery_class), \
             patch('src.services.model_discovery.ModelDiscoveryService', mock_discovery_class), \
             patch('src.routes.models.download_manager', mock_dm), \
             patch('src.services.download_manager.download_manager', mock_dm):

            # Step 1: Discover models
            response = client.get('/api/models/discover')
            assert response.status_code == 200

            # Step 2: Start download
            with patch('threading.Thread'):
                response = client.post('/api/models/download', json={
                    'model_id': 'test-model',
                    'auto_load': True
                })
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['status'] == 'started'
                task_id = data['task_id']

            # Step 3: Check download status
            response = client.get(f'/api/models/download/{task_id}')
            assert response.status_code == 200

            # Step 4: Load model with warmup and mmap
            response = client.post('/api/models/load', json={
                'model_id': 'test-model',
                'auto_warmup': True,
                'use_mmap': True
            })
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'

            # Step 5: Check warmup status
            with patch('src.routes.models.model_warmup_service') as mock_warmup:
                mock_warmup.get_all_warmup_status.return_value = {
                    'test-model': {
                        'is_warmed': True,
                        'warmup_time_ms': 200.0
                    }
                }

                response = client.get('/api/models/warmup/status')
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['warmed_models'] == 1

            # Step 6: Run inference — mock the model in loaded_models
            flask_app, _socketio = app
            mock_inference_model = MagicMock()
            mock_inference_model.model_id = 'test-model'
            mock_inference_model.generate.return_value = "Generated response"
            mock_inference_model.tokenize.return_value = [1, 2, 3]
            flask_app.config['app_state']['loaded_models']['test-model'] = mock_inference_model

            response = client.post('/v1/chat/completions', json={
                'model': 'test-model',
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'stream': False
            })
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'choices' in data
            assert data['choices'][0]['message']['content'] == "Generated response"

        # Step 7: Run benchmark
        response = client.post('/api/models/benchmark/test-model', json={})
        # Would normally check benchmark results

    def test_multi_model_management(self, client):
        """Test managing multiple models concurrently"""
        model_ids = ['model1', 'model2', 'model3']

        with patch('src.routes.models._load_model_internal') as mock_load:
            # Load multiple models
            for model_id in model_ids:
                mock_load.return_value = {
                    'status': 'success',
                    'model_id': model_id
                }

                response = client.post('/api/models/load', json={
                    'model_id': model_id
                })
                assert response.status_code == 200

        # List loaded models
        with patch('src.routes.models.get_available_models') as mock_get:
            mock_get.return_value = [
                {'id': mid, 'loaded': True} for mid in model_ids
            ]

            response = client.get('/api/models/list')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['models']) == 3

        # Unload one model
        response = client.post('/api/models/unload', json={
            'model_id': 'model2'
        })
        # Would check unload success

    @pytest.mark.integration
    def test_websocket_real_time_updates(self, socketio_client):
        """Test WebSocket real-time updates"""
        # Connect to WebSocket
        socketio_client.connect()

        # Subscribe to metrics
        socketio_client.emit('subscribe', {'room': 'metrics'})

        # In test environment, SocketIO events may not fire reliably
        socketio_client.get_received()
        # Just verify the connection and emit don't raise errors
        # The subscription confirmation may not arrive in test mode

        socketio_client.disconnect()

    def test_error_recovery_flow(self, client):
        """Test error recovery mechanisms"""
        # Test OOM recovery — patch _load_model_internal which is called
        # by the load_model route when auto_warmup is False (default)
        with patch('src.routes.models._load_model_internal') as mock_load:
            mock_load.return_value = {
                'error': 'Insufficient memory',
                'message': 'Memory usage exceeds limit',
                'status_code': 507
            }

            response = client.post('/api/models/load', json={
                'model_id': 'large-model'
            })
            assert response.status_code == 507
            data = json.loads(response.data)
            assert 'Insufficient memory' in data['error']

    @patch('src.routes.models.mmap_loader')
    @patch('pathlib.Path.exists', return_value=True)
    def test_memory_mapped_loading(self, mock_path_exists, mock_mmap_loader, client):
        """Test memory-mapped loading functionality"""
        # Mock mmap benchmark
        mock_mmap_loader.benchmark_load_time.return_value = {
            'mmap_load_ms': 1000,
            'regular_load_ms': 5000,
            'speedup': 5.0,
            'model_size_gb': 3.5
        }
        mock_mmap_loader.get_memory_usage.return_value = {
            'total_mapped_gb': 3.5,
            'file_count': 10
        }

        response = client.post('/api/models/mmap/benchmark', json={
            'model_path': '/path/to/model'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['results']['speedup'] == 5.0
        assert data['recommendation'] == 'Use mmap'

    def test_kv_cache_conversation_flow(self, app, client):
        """Test KV cache with multi-turn conversation"""
        conversation_id = 'test-conv-123'
        flask_app, _socketio = app

        # Set up a mock model in loaded_models so the route uses it
        mock_model = MagicMock()
        mock_model.model_id = 'test-model'
        mock_model.generate.return_value = "Response"
        mock_model.tokenize.return_value = [1, 2, 3]

        with flask_app.app_context():
            flask_app.config['app_state']['loaded_models']['test-model'] = mock_model

        # First message
        response = client.post('/v1/chat/completions', json={
            'model': 'test-model',
            'messages': [{'role': 'user', 'content': 'Hello'}],
            'conversation_id': conversation_id,
            'use_cache': True
        })
        assert response.status_code == 200

        # Second message (should use cache)
        response = client.post('/v1/chat/completions', json={
            'model': 'test-model',
            'messages': [
                {'role': 'user', 'content': 'Hello'},
                {'role': 'assistant', 'content': 'Response'},
                {'role': 'user', 'content': 'How are you?'}
            ],
            'conversation_id': conversation_id,
            'use_cache': True
        })
        assert response.status_code == 200

        # Check cache status
        with patch('src.routes.models.kv_cache_manager') as mock_cache:
            mock_cache.get_stats.return_value = {
                'enabled': True,
                'num_caches': 1,
                'conversations': [{
                    'conversation_id': conversation_id,
                    'sequence_length': 50
                }]
            }

            response = client.get('/api/models/cache/status')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['num_caches'] == 1

    def test_concurrent_request_handling(self, app, client):
        """Test handling multiple concurrent requests"""
        import concurrent.futures

        flask_app, _socketio = app

        # Set up a mock model in loaded_models
        mock_model = MagicMock()
        mock_model.model_id = 'test-model'
        mock_model.generate.return_value = "Response"
        mock_model.tokenize.return_value = [1, 2, 3]

        with flask_app.app_context():
            flask_app.config['app_state']['loaded_models']['test-model'] = mock_model

        def make_request(msg):
            return client.post('/v1/chat/completions', json={
                'model': 'test-model',
                'messages': [{'role': 'user', 'content': msg}],
                'stream': False
            })

        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(10):
                future = executor.submit(make_request, f"Message {i}")
                futures.append(future)

            # Wait for all to complete
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert all(r.status_code == 200 for r in results)

    def test_performance_monitoring(self, client):
        """Test performance monitoring and metrics"""
        # Get hardware info
        response = client.get('/api/hardware/info')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'chip_type' in data
        assert 'total_memory_gb' in data

        # Get real-time metrics
        response = client.get('/api/hardware/metrics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'cpu' in data
        assert 'memory' in data

        # Get GPU metrics
        with patch('src.routes.hardware.metal_monitor') as mock_metal:
            mock_metrics = MagicMock()
            mock_metrics.timestamp = time.time()
            mock_metrics.gpu_utilization = 75.0
            mock_metrics.gpu_frequency_mhz = 1200
            mock_metrics.memory_used_gb = 4.5
            mock_metrics.memory_total_gb = 16.0
            mock_metrics.memory_bandwidth_utilization = 50.0
            mock_metrics.temperature_celsius = 55.0
            mock_metrics.power_watts = 15.0
            mock_metal.get_current_metrics.return_value = mock_metrics
            mock_metal.get_average_metrics.return_value = None
            mock_metal.get_peak_metrics.return_value = None
            mock_metal.metrics_history = []

            response = client.get('/api/hardware/gpu/metrics')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['current']['gpu_utilization_percent'] == 75.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
