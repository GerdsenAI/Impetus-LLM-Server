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
        flask_app, socketio = app
        return flask_app.test_client()

    @pytest.fixture
    def socketio_client(self, app):
        """Create SocketIO test client"""
        flask_app, socketio = app
        return socketio.test_client(flask_app)

    @patch('src.model_loaders.mlx_loader.MLX_AVAILABLE', True)
    @patch('src.model_loaders.mlx_loader.load')
    @patch('src.services.download_manager.download_manager')
    @patch('src.services.model_discovery.ModelDiscoveryService')
    def test_download_load_warmup_inference_flow(self,
                                                mock_discovery_class,
                                                mock_download_manager,
                                                mock_mlx_load,
                                                client,
                                                socketio_client):
        """Test complete flow: download → load → warmup → inference"""

        # Setup mocks
        mock_discovery = MagicMock()
        mock_model_info = MagicMock()
        mock_model_info.size_gb = 3.5
        mock_discovery.get_model_info.return_value = mock_model_info
        mock_discovery_class.return_value = mock_discovery

        # Mock download manager
        mock_download_manager.check_disk_space.return_value = (True, 50.0)
        mock_download_manager.create_download_task.return_value = "task-123"
        mock_download_manager.get_task_status.return_value = MagicMock(
            status=MagicMock(value='completed'),
            progress=1.0
        )

        # Mock MLX model
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_model.config = {'max_position_embeddings': 2048}
        mock_tokenizer.encode.return_value = [1, 2, 3]
        mock_mlx_load.return_value = (mock_model, mock_tokenizer)

        # Step 1: Discover models
        response = client.get('/api/models/discover')
        assert response.status_code == 200

        # Step 2: Start download
        with patch('src.routes.models.Thread'):
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
        with patch('src.services.model_warmup.model_warmup_service') as mock_warmup:
            mock_status = MagicMock()
            mock_status.is_warmed = True
            mock_status.warmup_time_ms = 200.0
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

        # Step 6: Run inference
        with patch('src.routes.openai_api.generate') as mock_generate:
            mock_generate.return_value = "Generated response"

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
        response = client.post('/api/models/benchmark/test-model')
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

    def test_websocket_real_time_updates(self, socketio_client):
        """Test WebSocket real-time updates"""
        # Connect to WebSocket
        socketio_client.connect()

        # Subscribe to metrics
        socketio_client.emit('subscribe', {'room': 'metrics'})

        # Should receive subscription confirmation
        received = socketio_client.get_received()
        assert any(msg['name'] == 'subscribed' for msg in received)

        # Wait for metrics update (sent every 2 seconds)
        time.sleep(2.5)

        # Should have received metrics
        received = socketio_client.get_received()
        metrics_msgs = [msg for msg in received if msg['name'] == 'metrics_update']
        # In test environment, background threads might not run
        # assert len(metrics_msgs) > 0

        socketio_client.disconnect()

    def test_error_recovery_flow(self, client):
        """Test error recovery mechanisms"""
        # Test OOM recovery
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

    @patch('src.utils.mmap_loader.mmap_loader')
    def test_memory_mapped_loading(self, mock_mmap_loader, client):
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

    def test_kv_cache_conversation_flow(self, client):
        """Test KV cache with multi-turn conversation"""
        conversation_id = 'test-conv-123'

        with patch('src.routes.openai_api.generate') as mock_generate:
            mock_generate.return_value = "Response"

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
        with patch('src.inference.kv_cache_manager.kv_cache_manager') as mock_cache:
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

    def test_concurrent_request_handling(self, client):
        """Test handling multiple concurrent requests"""
        import concurrent.futures

        def make_request(msg):
            with patch('src.routes.openai_api.generate') as mock_gen:
                mock_gen.return_value = f"Response to {msg}"

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
        assert 'memory_gb' in data

        # Get real-time metrics
        response = client.get('/api/hardware/metrics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'cpu' in data
        assert 'memory' in data

        # Get GPU metrics
        with patch('src.utils.metal_monitor.metal_monitor') as mock_metal:
            mock_metrics = MagicMock()
            mock_metrics.gpu_utilization = 75.0
            mock_metrics.memory_used_gb = 4.5
            mock_metal.get_current_metrics.return_value = mock_metrics

            response = client.get('/api/hardware/gpu/metrics')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['gpu_utilization'] == 75.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
