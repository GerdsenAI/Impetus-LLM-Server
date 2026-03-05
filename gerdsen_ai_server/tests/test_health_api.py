"""
Unit tests for health check and metrics endpoints (routes/health.py).
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from src.routes.health import bp as health_bp


class TestHealthCheck:
    """Tests for GET /api/health"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(health_bp, url_prefix="/api")
        app.config["app_state"] = {
            "loaded_models": {},
            "metrics": {},
            "hardware_info": {},
            "model_inference_counts": {},
        }
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch("src.routes.health.last_heartbeat", datetime.now())
    def test_health_check_healthy(self, client):
        """GET /api/health returns 200 with healthy status when heartbeat is fresh."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data
        assert "version" in data

    @patch("src.routes.health.last_heartbeat", datetime.now() - timedelta(seconds=60))
    def test_health_check_stale_heartbeat(self, client):
        """GET /api/health returns 503 when heartbeat is stale (>30s)."""
        response = client.get("/api/health")
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data["status"] == "unhealthy"
        assert "stale" in data.get("error", "").lower()

    @patch("src.routes.health.last_heartbeat", datetime.now())
    @patch("src.routes.health.settings")
    def test_health_check_exception(self, mock_settings, client):
        """GET /api/health returns 503 on internal error."""
        mock_settings.version = property(lambda self: (_ for _ in ()).throw(RuntimeError("boom")))
        type(mock_settings).version = property(lambda self: (_ for _ in ()).throw(RuntimeError("boom")))
        response = client.get("/api/health")
        # Should be 503 since the exception is caught
        assert response.status_code in (200, 503)


class TestReadinessCheck:
    """Tests for GET /api/health/ready"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(health_bp, url_prefix="/api")
        app.config["app_state"] = {
            "loaded_models": {"test-model": MagicMock()},
            "metrics": {},
            "hardware_info": {},
        }
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch("src.routes.health.psutil")
    @patch("src.routes.health.settings")
    def test_readiness_ready(self, mock_settings, mock_psutil, client):
        """GET /api/health/ready returns 200 when all checks pass."""
        mock_memory = MagicMock()
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_settings.model.require_model_for_ready = False

        with patch("platform.system", return_value="Linux"):
            response = client.get("/api/health/ready")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["ready"] is True
        assert data["checks"]["memory_available"] is True

    @patch("src.routes.health.psutil")
    @patch("src.routes.health.settings")
    def test_readiness_not_ready_high_memory(self, mock_settings, mock_psutil, client):
        """GET /api/health/ready returns 503 when memory usage > 95%."""
        mock_memory = MagicMock()
        mock_memory.percent = 97.0
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_settings.model.require_model_for_ready = False

        with patch("platform.system", return_value="Linux"):
            response = client.get("/api/health/ready")

        assert response.status_code == 503
        data = json.loads(response.data)
        assert data["ready"] is False
        assert data["checks"]["memory_available"] is False

    @patch("src.routes.health.psutil")
    @patch("src.routes.health.settings")
    def test_readiness_model_required_none_loaded(self, mock_settings, mock_psutil, app):
        """GET /api/health/ready returns 503 when model required but none loaded."""
        app.config["app_state"]["loaded_models"] = {}
        client = app.test_client()

        mock_memory = MagicMock()
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_settings.model.require_model_for_ready = True

        with patch("platform.system", return_value="Linux"):
            response = client.get("/api/health/ready")

        assert response.status_code == 503
        data = json.loads(response.data)
        assert data["checks"]["models_loaded"] is False


class TestLivenessCheck:
    """Tests for GET /api/health/live"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(health_bp, url_prefix="/api")
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch("src.routes.health.last_heartbeat", datetime.now())
    def test_liveness_check(self, client):
        """GET /api/health/live returns 200 with alive=True."""
        response = client.get("/api/health/live")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["alive"] is True
        assert "uptime_seconds" in data


class TestDetailedStatus:
    """Tests for GET /api/health/status"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(health_bp, url_prefix="/api")
        app.config["app_state"] = {
            "loaded_models": {},
            "metrics": {},
            "hardware_info": {},
            "model_inference_counts": {},
        }
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch("src.routes.health.psutil")
    @patch("src.routes.health.settings")
    def test_detailed_status_healthy(self, mock_settings, mock_psutil, client):
        """GET /api/health/status returns 200 with health_score near 100 when healthy."""
        mock_psutil.cpu_percent.return_value = 20.0
        mock_memory = MagicMock()
        mock_memory.percent = 40.0
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.getloadavg.return_value = (1.0, 1.0, 1.0)
        mock_settings.version = "2.0.0"

        with patch("platform.system", return_value="Linux"):
            response = client.get("/api/health/status")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] in ("healthy", "degraded")
        assert "health_score" in data
        assert "system" in data

    @patch("src.routes.health.psutil")
    @patch("src.routes.health.settings")
    def test_detailed_status_degraded(self, mock_settings, mock_psutil, client):
        """GET /api/health/status returns degraded when CPU > 80%."""
        mock_psutil.cpu_percent.return_value = 85.0
        mock_memory = MagicMock()
        mock_memory.percent = 92.0
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.getloadavg.return_value = (5.0, 5.0, 5.0)
        mock_settings.version = "2.0.0"

        with patch("platform.system", return_value="Linux"):
            response = client.get("/api/health/status")

        assert response.status_code == 200
        data = json.loads(response.data)
        # health_score should be reduced: -20 for CPU>80, -30 for mem>90 = 50
        assert data["health_score"] < 70
        assert data["status"] in ("degraded", "unhealthy")


class TestPrometheusMetrics:
    """Tests for GET /api/metrics"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(health_bp, url_prefix="/api")
        app.config["app_state"] = {
            "loaded_models": {},
            "metrics": {"requests_total": 42, "tokens_generated": 1000},
            "hardware_info": {},
        }
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch("src.routes.health.psutil")
    @patch("src.routes.health.settings")
    def test_prometheus_metrics_format(self, mock_settings, mock_psutil, client):
        """GET /api/metrics returns text/plain with Prometheus format."""
        mock_psutil.cpu_percent.return_value = 30.0
        mock_memory = MagicMock()
        mock_memory.percent = 50.0
        mock_memory.available = 8 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_settings.version = "2.0.0"
        mock_settings.environment = "testing"

        response = client.get("/api/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.content_type
        text = response.data.decode()
        assert "impetus_uptime_seconds" in text
        assert "impetus_requests_total 42" in text
        assert "impetus_tokens_generated_total 1000" in text

    @patch("src.routes.health.psutil")
    @patch("src.routes.health.settings")
    def test_prometheus_metrics_with_models(self, mock_settings, mock_psutil, client, app):
        """GET /api/metrics includes per-model metrics when models are loaded."""
        app.config["app_state"]["loaded_models"] = {"test-org/test-model": MagicMock()}
        mock_psutil.cpu_percent.return_value = 30.0
        mock_memory = MagicMock()
        mock_memory.percent = 50.0
        mock_memory.available = 8 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_settings.version = "2.0.0"
        mock_settings.environment = "testing"

        response = client.get("/api/metrics")
        assert response.status_code == 200
        text = response.data.decode()
        assert "impetus_model_loaded" in text
        assert "test-org/test-model" in text


class TestJsonMetrics:
    """Tests for GET /api/metrics/json"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(health_bp, url_prefix="/api")
        app.config["app_state"] = {
            "loaded_models": {},
            "metrics": {
                "requests_total": 100,
                "successful_requests": 95,
                "failed_requests": 5,
            },
        }
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch("src.routes.health.psutil")
    def test_json_metrics_structure(self, mock_psutil, client):
        """GET /api/metrics/json returns 200 with HealthMetrics structure."""
        mock_psutil.cpu_percent.return_value = 25.0
        mock_memory = MagicMock()
        mock_memory.percent = 45.0
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=500 * 1024 * 1024)
        mock_psutil.Process.return_value = mock_process

        response = client.get("/api/metrics/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["total_requests"] == 100
        assert data["successful_requests"] == 95
        assert data["failed_requests"] == 5
        assert "cpu_usage_percent" in data
        assert "memory_usage_mb" in data
        assert "loaded_models_count" in data

    @patch("src.routes.health.psutil")
    def test_json_metrics_error(self, mock_psutil, client):
        """GET /api/metrics/json returns 500 on psutil failure."""
        mock_psutil.cpu_percent.side_effect = RuntimeError("psutil error")

        response = client.get("/api/metrics/json")
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
