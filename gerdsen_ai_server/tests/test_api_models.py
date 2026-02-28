"""
Unit tests for models API endpoints
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from src.routes.models import bp as models_bp


class TestModelsAPI:
    """Test models API endpoints"""

    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(models_bp, url_prefix='/api/models')

        # Mock app state
        app.config['app_state'] = {
            'loaded_models': {},
            'hardware_info': {'chip_type': 'M1'},
            'model_benchmarks': {},
            'socketio': None
        }

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    def test_list_models_empty(self, client):
        """Test listing models when none available"""
        with patch('src.routes.models.get_available_models') as mock_get:
            mock_get.return_value = []

            response = client.get('/api/models/list')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['models'] == []
            assert 'models_directory' in data

    def test_list_models_with_models(self, client):
        """Test listing models with available models"""
        with patch('src.routes.models.get_available_models') as mock_get:
            mock_get.return_value = [
                {
                    'id': 'test-model',
                    'name': 'Test Model',
                    'loaded': True,
                    'size_gb': 3.5
                }
            ]

            with patch('src.routes.models.model_warmup_service') as mock_warmup:
                mock_status = MagicMock()
                mock_status.is_warmed = True
                mock_status.warmup_time_ms = 200.0
                mock_status.kernel_compilation_time_ms = 150.0
                mock_warmup.get_warmup_status.return_value = mock_status

                response = client.get('/api/models/list')

                assert response.status_code == 200
                data = json.loads(response.data)
                assert len(data['models']) == 1
                assert data['models'][0]['id'] == 'test-model'
                assert data['models'][0]['warmup']['is_warmed'] is True

    def test_load_model_missing_id(self, client):
        """Test loading model without model_id"""
        response = client.post('/api/models/load', json={})

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'model_id is required'

    @patch('src.routes.models._load_model_internal')
    def test_load_model_success(self, mock_load, client):
        """Test successful model loading"""
        mock_load.return_value = {
            'status': 'success',
            'model_id': 'test-model',
            'message': 'Model loaded successfully'
        }

        response = client.post('/api/models/load', json={'model_id': 'test-model'})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'

    @patch('src.model_loaders.mlx_loader.MLXModelLoader')
    @patch('src.routes.models.model_warmup_service')
    def test_load_model_with_warmup(self, mock_warmup_service, mock_loader_class, client, app):
        """Test loading model with auto warmup"""
        # Mock loader
        mock_loader = MagicMock()
        mock_model = MagicMock()
        mock_loader.load_model.return_value = mock_model
        mock_loader_class.return_value = mock_loader

        # Mock warmup status
        mock_status = MagicMock()
        mock_status.is_warmed = False
        mock_warmup_service.get_warmup_status.return_value = mock_status

        response = client.post('/api/models/load', json={
            'model_id': 'test-model',
            'auto_warmup': True
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Model loaded and warming up'
        assert data['warmup']['status'] == 'warming'

        # Verify loader was called with warmup
        mock_loader.load_model.assert_called_once_with(
            'test-model',
            auto_warmup=True,
            warmup_async=True,
            use_mmap=True
        )

    def test_unload_model_not_loaded(self, client):
        """Test unloading model that isn't loaded"""
        response = client.post('/api/models/unload', json={'model_id': 'test-model'})

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not currently loaded' in data['message']

    def test_unload_model_success(self, client, app):
        """Test successful model unloading"""
        # Add model to loaded models
        mock_model = MagicMock()
        app.config['app_state']['loaded_models']['test-model'] = mock_model

        response = client.post('/api/models/unload', json={'model_id': 'test-model'})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'test-model' not in app.config['app_state']['loaded_models']
        mock_model.unload.assert_called_once()

    @patch('src.routes.models.ModelDiscoveryService')
    def test_discover_models(self, mock_discovery_class, client):
        """Test model discovery endpoint"""
        # Mock discovery service
        mock_discovery = MagicMock()
        mock_model_info = MagicMock()
        mock_model_info.id = "test-model"
        mock_model_info.name = "Test Model"
        mock_model_info.category.value = "general"
        mock_model_info.size_gb = 3.5
        mock_model_info.quantization = "4-bit"
        mock_model_info.context_length = 4096
        mock_model_info.description = "Test description"
        mock_model_info.features = ["chat"]
        mock_model_info.recommended_for = ["general"]
        mock_model_info.min_memory_gb = 8
        mock_model_info.popularity_score = 5

        mock_discovery.get_all_models.return_value = [mock_model_info]
        mock_discovery.estimate_performance.return_value = 50
        mock_discovery_class.return_value = mock_discovery

        response = client.get('/api/models/discover')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['models']) == 1
        assert data['models'][0]['id'] == 'test-model'
        assert data['models'][0]['estimated_tokens_per_sec'] == 50

    def test_warmup_model_not_loaded(self, client):
        """Test warming up model that isn't loaded"""
        response = client.post('/api/models/warmup/test-model')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'must be loaded before warming up' in data['message']

    @patch('src.routes.models.model_warmup_service')
    def test_warmup_model_success(self, mock_warmup_service, client, app):
        """Test successful model warmup"""
        # Add model to loaded models
        mock_model = MagicMock()
        app.config['app_state']['loaded_models']['test-model'] = mock_model

        # Mock warmup status
        mock_status = MagicMock()
        mock_status.is_warmed = True
        mock_status.warmup_time_ms = 250.0
        mock_status.kernel_compilation_time_ms = 180.0
        mock_status.error = None
        mock_warmup_service.warmup_model.return_value = mock_status

        response = client.post('/api/models/warmup/test-model', json={
            'num_prompts': 2,
            'async': False
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'warmed'
        assert data['is_warmed'] is True
        assert data['warmup_time_ms'] == 250.0

        # Verify warmup was called
        mock_warmup_service.warmup_model.assert_called_once_with(
            mock_model,
            'test-model',
            num_prompts=2,
            async_warmup=False
        )

    @patch('src.routes.models.model_warmup_service')
    def test_warmup_status(self, mock_warmup_service, client, app):
        """Test getting warmup status"""
        # Mock warmup status
        mock_warmup_service.get_all_warmup_status.return_value = {
            'model1': {
                'is_warmed': True,
                'warmup_time_ms': 200,
                'last_warmup': None,
                'warmup_prompts_used': 3,
                'kernel_compilation_time_ms': 150,
                'error': None,
                'age_seconds': None
            }
        }

        # Add loaded model without warmup
        app.config['app_state']['loaded_models']['model2'] = MagicMock()

        response = client.get('/api/models/warmup/status')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['warmup_status']) == 2
        assert data['warmup_status']['model1']['is_warmed'] is True
        assert data['warmup_status']['model2']['is_warmed'] is False
        assert data['warmed_models'] == 1

    @patch('src.routes.models.kv_cache_manager')
    def test_cache_status(self, mock_cache_manager, client):
        """Test getting KV cache status"""
        mock_cache_manager.get_stats.return_value = {
            'enabled': True,
            'num_caches': 2,
            'total_memory_mb': 512,
            'max_memory_mb': 2048,
            'memory_usage_percent': 25,
            'conversations': []
        }

        response = client.get('/api/models/cache/status')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['enabled'] is True
        assert data['num_caches'] == 2
        assert data['memory_usage_percent'] == 25

    @patch('src.routes.models.kv_cache_manager')
    def test_clear_cache_specific(self, mock_cache_manager, client):
        """Test clearing specific conversation cache"""
        mock_cache_manager.clear_cache.return_value = True

        response = client.post('/api/models/cache/clear', json={
            'model_id': 'test-model',
            'conversation_id': 'test-conv'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['message'] == 'Cache cleared'

        mock_cache_manager.clear_cache.assert_called_once_with(
            'test-model',
            'test-conv'
        )

    @patch('src.routes.models.benchmark_service')
    def test_benchmark_model(self, mock_benchmark_service, client, app):
        """Test model benchmarking"""
        # Add model
        mock_model = MagicMock()
        app.config['app_state']['loaded_models']['test-model'] = mock_model

        # Mock benchmark result
        mock_suite = MagicMock()
        mock_suite.timestamp = "2024-01-01T00:00:00"
        mock_suite.average_tokens_per_second = 75.5
        mock_suite.average_first_token_latency_ms = 150.0
        mock_suite.peak_tokens_per_second = 85.0
        mock_suite.average_memory_gb = 4.5

        mock_result = MagicMock()
        mock_result.prompt_length = 50
        mock_result.output_tokens = 100
        mock_result.tokens_per_second = 75.0
        mock_result.time_to_first_token_ms = 145.0
        mock_result.total_time_ms = 1333.0
        mock_result.gpu_utilization_avg = 85.0

        mock_suite.results = [mock_result]
        mock_benchmark_service.benchmark_model.return_value = mock_suite

        response = client.post('/api/models/benchmark/test-model', json={})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['summary']['average_tokens_per_second'] == 75.5
        assert len(data['results']) == 1
        assert data['results'][0]['tokens_per_second'] == 75.0

    @patch('src.services.download_manager.download_manager')
    @patch('src.services.model_discovery.ModelDiscoveryService')
    def test_download_model(self, mock_discovery_class, mock_download_manager, client):
        """Test model download endpoint"""
        # Mock discovery
        mock_discovery = MagicMock()
        mock_model_info = MagicMock()
        mock_model_info.size_gb = 3.5
        mock_discovery.get_model_info.return_value = mock_model_info
        mock_discovery_class.return_value = mock_discovery

        # Mock download manager
        mock_download_manager.check_disk_space.return_value = (True, 50.0)
        mock_download_manager.create_download_task.return_value = "task-123"

        with patch('threading.Thread'):
            response = client.post('/api/models/download', json={
                'model_id': 'test-model',
                'auto_load': False
            })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'started'
        assert data['task_id'] == 'task-123'
        assert data['estimated_size_gb'] == 3.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
