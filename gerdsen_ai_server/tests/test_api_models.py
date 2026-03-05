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


class TestGetAvailableModels:
    """Tests for get_available_models function."""

    @pytest.fixture
    def app(self):
        """Create test Flask app with models blueprint."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(models_bp, url_prefix="/api/models")
        app.config["app_state"] = {
            "loaded_models": {},
            "hardware_info": {"chip_type": "M1"},
            "model_benchmarks": {},
            "socketio": None,
        }
        return app

    @patch("src.routes.models.settings")
    def test_models_dir_not_exists(self, mock_settings, app):
        """Returns empty list when models directory doesn't exist."""
        from src.routes.models import get_available_models

        mock_settings.model.models_dir = MagicMock()
        mock_settings.model.models_dir.exists.return_value = False
        with app.app_context():
            result = get_available_models()
        assert result == []

    @patch("src.routes.models.settings")
    def test_mlx_model_detected(self, mock_settings, app, tmp_path):
        """MLX model detected via config.json."""
        from src.routes.models import get_available_models

        model_dir = tmp_path / "test-model"
        model_dir.mkdir()
        (model_dir / "config.json").write_text("{}")
        (model_dir / "weights.safetensors").write_bytes(b"\x00" * 1024)

        mock_settings.model.models_dir = tmp_path
        with app.app_context():
            result = get_available_models()
        assert len(result) == 1
        assert result[0]["format"] == "mlx"
        assert result[0]["id"] == "test-model"
        assert result[0]["size_gb"] > 0

    @patch("src.routes.models.settings")
    def test_gguf_model_detected(self, mock_settings, app, tmp_path):
        """GGUF model detected via .gguf file."""
        from src.routes.models import get_available_models

        model_dir = tmp_path / "gguf-model"
        model_dir.mkdir()
        (model_dir / "model.gguf").write_bytes(b"\x00" * 2048)

        mock_settings.model.models_dir = tmp_path
        with app.app_context():
            result = get_available_models()
        assert len(result) == 1
        assert result[0]["format"] == "gguf"

    @patch("src.routes.models.settings")
    def test_loaded_model_marked(self, mock_settings, app, tmp_path):
        """Loaded model is marked as loaded=True."""
        from src.routes.models import get_available_models

        model_dir = tmp_path / "loaded-model"
        model_dir.mkdir()
        (model_dir / "config.json").write_text("{}")

        mock_settings.model.models_dir = tmp_path
        app.config["app_state"]["loaded_models"]["loaded-model"] = MagicMock()
        with app.app_context():
            result = get_available_models()
        assert result[0]["loaded"] is True

    @patch("src.routes.models.settings")
    def test_hub_model_added(self, mock_settings, app, tmp_path):
        """Hub-downloaded model (not on disk) added to list."""
        from src.routes.models import get_available_models

        mock_settings.model.models_dir = tmp_path
        app.config["app_state"]["loaded_models"]["hub-model"] = MagicMock()
        with app.app_context():
            result = get_available_models()
        assert len(result) == 1
        assert result[0]["id"] == "hub-model"
        assert result[0]["path"] == "hub"
        assert result[0]["loaded"] is True


class TestDownloadRoutes:
    """Tests for download-related route handlers."""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(models_bp, url_prefix="/api/models")
        app.config["app_state"] = {
            "loaded_models": {},
            "hardware_info": {"chip_type": "M1"},
            "model_benchmarks": {},
            "socketio": None,
        }
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch("src.routes.models.download_manager")
    def test_get_download_status_found(self, mock_dm, client):
        """Get download status for existing task returns 200."""
        from datetime import datetime

        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.model_id = "test-model"
        mock_task.status.value = "downloading"
        mock_task.progress = 0.5
        mock_task.downloaded_bytes = 2 * 1024**3
        mock_task.total_bytes = 4 * 1024**3
        mock_task.speed_mbps = 50.0
        mock_task.eta_seconds = 40
        mock_task.error = None
        mock_task.started_at = datetime(2024, 1, 1)
        mock_task.completed_at = None
        mock_dm.get_task_status.return_value = mock_task

        response = client.get("/api/models/download/task-123")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["task_id"] == "task-123"
        assert data["status"] == "downloading"
        assert data["progress"] == 0.5

    @patch("src.routes.models.download_manager")
    def test_get_download_status_not_found(self, mock_dm, client):
        """Get download status for unknown task returns 404."""
        mock_dm.get_task_status.return_value = None
        response = client.get("/api/models/download/nonexistent")
        assert response.status_code == 404

    @patch("src.routes.models.download_manager")
    def test_list_downloads_empty(self, mock_dm, client):
        """List downloads returns empty list when no tasks exist."""
        mock_dm.get_all_tasks.return_value = {}
        response = client.get("/api/models/downloads")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["downloads"] == []
        assert data["total"] == 0

    @patch("src.routes.models.download_manager")
    def test_list_downloads_with_tasks(self, mock_dm, client):
        """List downloads returns all tasks."""
        mock_task = MagicMock()
        mock_task.task_id = "task-1"
        mock_task.model_id = "model-a"
        mock_task.status.value = "completed"
        mock_task.progress = 1.0
        mock_task.started_at = None
        mock_dm.get_all_tasks.return_value = {"task-1": mock_task}

        response = client.get("/api/models/downloads")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["total"] == 1
        assert data["downloads"][0]["task_id"] == "task-1"

    @patch("src.routes.models.download_manager")
    def test_cancel_download_success(self, mock_dm, client):
        """Cancel download returns success when task is cancellable."""
        mock_dm.cancel_download.return_value = True
        response = client.delete("/api/models/download/task-1")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "cancelled"

    @patch("src.routes.models.download_manager")
    def test_cancel_download_failure(self, mock_dm, client):
        """Cancel download returns 400 when task can't be cancelled."""
        mock_dm.cancel_download.return_value = False
        response = client.delete("/api/models/download/task-1")
        assert response.status_code == 400

    def test_unload_model_missing_id(self, client):
        """Unload without model_id returns 400."""
        response = client.post("/api/models/unload", json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"] == "model_id is required"


class TestLoadModelInternal:
    """Tests for _load_model_internal function."""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(models_bp, url_prefix="/api/models")
        app.config["app_state"] = {
            "loaded_models": {},
            "hardware_info": {"chip_type": "M1"},
            "model_benchmarks": {},
            "socketio": None,
        }
        return app

    @patch("src.routes.models.settings")
    @patch("src.routes.models.psutil")
    def test_already_loaded(self, mock_psutil, mock_settings, app):
        """Returns already_loaded status for duplicate load request."""
        from src.routes.models import _load_model_internal

        app_state = {"loaded_models": {"test-model": MagicMock()}}
        with app.app_context():
            result = _load_model_internal("test-model", app_state)
        assert result["status"] == "already_loaded"

    @patch("src.routes.models.settings")
    @patch("psutil.virtual_memory")
    def test_insufficient_memory(self, mock_memory, mock_settings, app):
        """Returns error when insufficient memory available."""
        from src.routes.models import _load_model_internal

        mock_mem = MagicMock()
        mock_mem.available = 3 * 1024**3  # Only 3GB free
        mock_memory.return_value = mock_mem

        mock_settings.model.models_dir = MagicMock()
        model_dir = MagicMock()
        model_dir.exists.return_value = False
        mock_settings.model.models_dir.__truediv__ = MagicMock(return_value=model_dir)

        app_state = {"loaded_models": {}}
        with app.app_context():
            result = _load_model_internal("big-model", app_state)
        assert "error" in result

    @patch("src.routes.models.settings")
    @patch("psutil.virtual_memory")
    def test_model_limit_reached(self, mock_memory, mock_settings, app):
        """Returns error when max_loaded_models reached."""
        from src.routes.models import _load_model_internal

        mock_mem = MagicMock()
        mock_mem.available = 32 * 1024**3
        mock_memory.return_value = mock_mem

        mock_settings.model.models_dir = MagicMock()
        model_dir = MagicMock()
        model_dir.exists.return_value = False
        mock_settings.model.models_dir.__truediv__ = MagicMock(return_value=model_dir)
        mock_settings.model.max_loaded_models = 1

        app_state = {"loaded_models": {"existing-model": MagicMock()}}
        with app.app_context():
            result = _load_model_internal("new-model", app_state)
        assert result["error"] == "Model limit reached"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
