"""
Unit tests for hardware monitoring endpoints (routes/hardware.py).
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from src.routes.hardware import bp as hardware_bp


class TestHardwareInfo:
    """Tests for GET /api/hardware/info"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(hardware_bp, url_prefix="/api/hardware")
        app.config["app_state"] = {
            "hardware_info": {},
        }
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    def test_hardware_info_cached(self, client, app):
        """GET /api/hardware/info returns cached info when available."""
        app.config["app_state"]["hardware_info"] = {
            "chip_type": "Apple M2 Pro",
            "total_memory_gb": 32,
        }
        response = client.get("/api/hardware/info")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["chip_type"] == "Apple M2 Pro"
        assert data["total_memory_gb"] == 32

    @patch("src.routes.hardware.detect_hardware")
    def test_hardware_info_detect(self, mock_detect, client, app):
        """GET /api/hardware/info re-detects when not cached."""
        app.config["app_state"]["hardware_info"] = {}
        mock_detect.return_value = {
            "chip_type": "Apple M4",
            "total_memory_gb": 64,
        }
        response = client.get("/api/hardware/info")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["chip_type"] == "Apple M4"
        mock_detect.assert_called_once()


class TestHardwareMetrics:
    """Tests for GET /api/hardware/metrics"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(hardware_bp, url_prefix="/api/hardware")
        app.config["app_state"] = {}
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch("src.routes.hardware.metal_monitor")
    @patch("src.routes.hardware.get_thermal_state")
    @patch("src.routes.hardware.psutil")
    def test_hardware_metrics_success(self, mock_psutil, mock_thermal, mock_metal, client):
        """GET /api/hardware/metrics returns 200 with CPU, memory, disk, network."""
        # CPU
        mock_psutil.cpu_percent.return_value = [20.0, 30.0, 25.0, 15.0]
        mock_cpu_freq = MagicMock()
        mock_cpu_freq.current = 3200.0
        mock_cpu_freq.min = 600.0
        mock_cpu_freq.max = 3500.0
        mock_psutil.cpu_freq.return_value = mock_cpu_freq

        # Memory
        mock_memory = MagicMock()
        mock_memory.total = 32 * 1024**3
        mock_memory.available = 16 * 1024**3
        mock_memory.used = 16 * 1024**3
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory

        # Swap
        mock_swap = MagicMock()
        mock_swap.used = 1024**3
        mock_swap.percent = 10.0
        mock_psutil.swap_memory.return_value = mock_swap

        # Disk
        mock_disk = MagicMock()
        mock_disk.total = 1000 * 1024**3
        mock_disk.used = 500 * 1024**3
        mock_disk.free = 500 * 1024**3
        mock_disk.percent = 50.0
        mock_psutil.disk_usage.return_value = mock_disk

        # Network
        mock_net = MagicMock()
        mock_net.bytes_sent = 100 * 1024 * 1024
        mock_net.bytes_recv = 200 * 1024 * 1024
        mock_net.packets_sent = 1000
        mock_net.packets_recv = 2000
        mock_psutil.net_io_counters.return_value = mock_net

        # Process
        mock_process = MagicMock()
        mock_process.cpu_percent.return_value = 5.0
        mock_process.memory_info.return_value = MagicMock(rss=500 * 1024 * 1024)
        mock_process.num_threads.return_value = 10
        mock_process.open_files.return_value = []
        mock_psutil.Process.return_value = mock_process
        mock_psutil.boot_time.return_value = 1700000000.0

        # Thermal
        mock_thermal.return_value = {"thermal_state": "nominal"}

        # GPU not macOS
        mock_metal._is_macos.return_value = False

        response = client.get("/api/hardware/metrics")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data
        assert data["gpu"] is None

    @patch("src.routes.hardware.metal_monitor")
    @patch("src.routes.hardware.get_thermal_state")
    @patch("src.routes.hardware.psutil")
    def test_hardware_metrics_with_gpu(self, mock_psutil, mock_thermal, mock_metal, client):
        """GET /api/hardware/metrics includes GPU data on macOS."""
        # Minimal mocks
        mock_psutil.cpu_percent.return_value = [10.0]
        mock_psutil.cpu_freq.return_value = MagicMock(current=3000, min=600, max=3500)
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=32 * 1024**3, available=16 * 1024**3,
            used=16 * 1024**3, percent=50.0
        )
        mock_psutil.swap_memory.return_value = MagicMock(used=0, percent=0)
        mock_psutil.disk_usage.return_value = MagicMock(
            total=1000 * 1024**3, used=500 * 1024**3,
            free=500 * 1024**3, percent=50
        )
        mock_psutil.net_io_counters.return_value = MagicMock(
            bytes_sent=0, bytes_recv=0, packets_sent=0, packets_recv=0
        )
        mock_process = MagicMock()
        mock_process.cpu_percent.return_value = 1.0
        mock_process.memory_info.return_value = MagicMock(rss=200 * 1024 * 1024)
        mock_process.num_threads.return_value = 5
        mock_process.open_files.return_value = []
        mock_psutil.Process.return_value = mock_process
        mock_psutil.boot_time.return_value = 1700000000.0
        mock_thermal.return_value = {"thermal_state": "nominal"}

        # GPU available
        mock_metal._is_macos.return_value = True
        mock_gpu = MagicMock()
        mock_gpu.gpu_utilization = 45.0
        mock_gpu.gpu_frequency_mhz = 1400
        mock_gpu.memory_used_gb = 8.0
        mock_gpu.memory_total_gb = 32.0
        mock_gpu.memory_bandwidth_utilization = 30.0
        mock_gpu.temperature_celsius = 55.0
        mock_metal.get_current_metrics.return_value = mock_gpu

        response = client.get("/api/hardware/metrics")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["gpu"] is not None
        assert data["gpu"]["utilization_percent"] == 45.0

    @patch("src.routes.hardware.psutil")
    def test_hardware_metrics_error(self, mock_psutil, client):
        """GET /api/hardware/metrics returns 500 on psutil failure."""
        mock_psutil.cpu_percent.side_effect = RuntimeError("psutil error")
        response = client.get("/api/hardware/metrics")
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data


class TestOptimizationRecommendations:
    """Tests for GET /api/hardware/optimization"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(hardware_bp, url_prefix="/api/hardware")
        app.config["app_state"] = {
            "hardware_info": {"chip_type": "Apple M2 Pro"},
        }
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch("src.routes.hardware.get_thermal_state")
    @patch("src.routes.hardware.psutil")
    @patch("src.routes.hardware.settings")
    def test_optimization_healthy(self, mock_settings, mock_psutil, mock_thermal, client):
        """GET /api/hardware/optimization returns empty recommendations when healthy."""
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.cpu_percent.return_value = 30.0
        mock_thermal.return_value = {"thermal_state": "nominal"}
        mock_settings.hardware.performance_mode = "balanced"

        response = client.get("/api/hardware/optimization")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["current_performance_mode"] == "balanced"
        assert len(data["recommendations"]) == 0

    @patch("src.routes.hardware.get_thermal_state")
    @patch("src.routes.hardware.psutil")
    @patch("src.routes.hardware.settings")
    def test_optimization_high_memory(self, mock_settings, mock_psutil, mock_thermal, client):
        """GET /api/hardware/optimization recommends unloading models when memory > 80%."""
        mock_psutil.virtual_memory.return_value = MagicMock(percent=85.0)
        mock_psutil.cpu_percent.return_value = 30.0
        mock_thermal.return_value = {"thermal_state": "nominal"}
        mock_settings.hardware.performance_mode = "balanced"

        response = client.get("/api/hardware/optimization")
        assert response.status_code == 200
        data = json.loads(response.data)
        memory_recs = [r for r in data["recommendations"] if r["type"] == "memory"]
        assert len(memory_recs) == 1
        assert memory_recs[0]["severity"] == "high"


class TestPerformanceMode:
    """Tests for POST /api/hardware/performance-mode"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(hardware_bp, url_prefix="/api/hardware")
        app.config["app_state"] = {}
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch("src.routes.hardware.settings")
    def test_set_performance_mode_valid(self, mock_settings, client):
        """POST /api/hardware/performance-mode with valid mode returns 200."""
        mock_settings.hardware = MagicMock()

        for mode in ("efficiency", "balanced", "performance"):
            response = client.post(
                "/api/hardware/performance-mode",
                json={"mode": mode},
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["mode"] == mode

    def test_set_performance_mode_invalid(self, client):
        """POST /api/hardware/performance-mode with invalid mode returns 400."""
        response = client.post(
            "/api/hardware/performance-mode",
            json={"mode": "turbo"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestComputeCapabilities:
    """Tests for GET /api/hardware/compute/capabilities"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(hardware_bp, url_prefix="/api/hardware")
        app.config["app_state"] = {}
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch("src.routes.hardware.psutil")
    @patch("src.model_loaders.compute_dispatcher.compute_dispatcher")
    def test_compute_capabilities(self, mock_dispatcher, mock_psutil, client):
        """GET /api/hardware/compute/capabilities returns 200 with capabilities."""
        mock_dispatcher.get_capabilities.return_value = {
            "active_device": "gpu",
            "ane_available": False,
        }
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=32 * 1024**3, available=16 * 1024**3, percent=50.0
        )

        response = client.get("/api/hardware/compute/capabilities")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "active_device" in data
        assert "memory" in data


class TestGpuMetrics:
    """Tests for GET /api/hardware/gpu/metrics"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(hardware_bp, url_prefix="/api/hardware")
        app.config["app_state"] = {}
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch("src.routes.hardware.metal_monitor")
    def test_gpu_metrics_not_macos(self, mock_metal, client):
        """GET /api/hardware/gpu/metrics returns 404 on non-macOS."""
        mock_metal._is_macos.return_value = False
        response = client.get("/api/hardware/gpu/metrics")
        assert response.status_code == 404

    @patch("src.routes.hardware.metal_monitor")
    def test_gpu_metrics_success(self, mock_metal, client):
        """GET /api/hardware/gpu/metrics returns 200 with GPU data on macOS."""
        mock_metal._is_macos.return_value = True
        mock_current = MagicMock()
        mock_current.timestamp = 1700000000.0
        mock_current.gpu_utilization = 50.0
        mock_current.gpu_frequency_mhz = 1400
        mock_current.memory_used_gb = 10.0
        mock_current.memory_total_gb = 32.0
        mock_current.memory_bandwidth_utilization = 25.0
        mock_current.temperature_celsius = 50.0
        mock_current.power_watts = 20.0
        mock_metal.get_current_metrics.return_value = mock_current
        mock_metal.get_average_metrics.return_value = None
        mock_metal.get_peak_metrics.return_value = None
        mock_metal.metrics_history = []

        response = client.get("/api/hardware/gpu/metrics")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "current" in data
        assert data["current"]["gpu_utilization_percent"] == 50.0
