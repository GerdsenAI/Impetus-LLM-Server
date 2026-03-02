"""
Unit tests for WebSocket event handlers (routes/websocket.py).
"""

import sys
import time
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask_socketio import SocketIO

from src.routes.websocket import gather_hardware_status, gather_metrics, register_handlers


class TestWebSocketHandlers:
    """Tests for Socket.IO event handlers registered by register_handlers()."""

    @pytest.fixture
    def app_state(self):
        """Build a minimal app_state dict used across all handler tests."""
        return {
            "loaded_models": {},
            "hardware_info": {"chip_type": "M2 Pro", "total_memory_gb": 32},
            "metrics": {"requests_total": 10},
            "active_sessions": {},
            "socketio": None,
        }

    @pytest.fixture
    def app(self, app_state):
        """Create a Flask app with SocketIO and register websocket handlers."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["app_state"] = app_state
        socketio = SocketIO(app, async_mode="threading")
        with patch("src.routes.websocket.threading"):
            register_handlers(socketio, app_state)
        return app, socketio, app_state

    @pytest.fixture
    def client(self, app):
        """Return a Flask-SocketIO test client connected to the app."""
        flask_app, socketio, _ = app
        return socketio.test_client(flask_app)

    def test_connect_emits_hardware_info(self, client, app):
        """On connect the server emits a 'hardware_info' event with cached hardware data."""
        _, _, app_state = app
        received = client.get_received()
        hardware_events = [e for e in received if e["name"] == "hardware_info"]
        assert len(hardware_events) == 1
        assert hardware_events[0]["args"][0] == {"chip_type": "M2 Pro", "total_memory_gb": 32}

    def test_connect_emits_models_update(self, client, app):
        """On connect the server emits a 'models_update' event listing loaded model names."""
        received = client.get_received()
        model_events = [e for e in received if e["name"] == "models_update"]
        assert len(model_events) == 1
        assert model_events[0]["args"][0] == {"loaded_models": []}

    def test_connect_emits_models_update_with_loaded_models(self, app):
        """On connect the models_update payload includes names of currently loaded models."""
        flask_app, socketio, app_state = app
        app_state["loaded_models"] = {"org/model-a": MagicMock(), "org/model-b": MagicMock()}
        test_client = socketio.test_client(flask_app)

        received = test_client.get_received()
        model_events = [e for e in received if e["name"] == "models_update"]
        assert len(model_events) == 1
        loaded = model_events[0]["args"][0]["loaded_models"]
        assert sorted(loaded) == ["org/model-a", "org/model-b"]
        test_client.disconnect()

    def test_subscribe_valid_room(self, client):
        """Subscribing to a valid room ('metrics') returns a 'subscribed' acknowledgement."""
        client.get_received()  # drain connect events
        client.emit("subscribe", {"room": "metrics"})
        received = client.get_received()
        subscribed_events = [e for e in received if e["name"] == "subscribed"]
        assert len(subscribed_events) == 1
        assert subscribed_events[0]["args"][0] == {"room": "metrics"}

    @pytest.mark.parametrize("room", ["metrics", "hardware", "models", "logs"])
    def test_subscribe_all_valid_rooms(self, client, room):
        """Subscribing to any of the four valid rooms succeeds."""
        client.get_received()
        client.emit("subscribe", {"room": room})
        received = client.get_received()
        subscribed_events = [e for e in received if e["name"] == "subscribed"]
        assert len(subscribed_events) == 1
        assert subscribed_events[0]["args"][0]["room"] == room

    def test_subscribe_invalid_room(self, client):
        """Subscribing to an invalid room name returns an 'error' event."""
        client.get_received()
        client.emit("subscribe", {"room": "invalid"})
        received = client.get_received()
        error_events = [e for e in received if e["name"] == "error"]
        assert len(error_events) == 1
        assert "Invalid room" in error_events[0]["args"][0]["message"]

    def test_unsubscribe(self, client):
        """Unsubscribing from a room returns an 'unsubscribed' acknowledgement."""
        client.get_received()
        client.emit("subscribe", {"room": "hardware"})
        client.get_received()  # drain subscribed event
        client.emit("unsubscribe", {"room": "hardware"})
        received = client.get_received()
        unsub_events = [e for e in received if e["name"] == "unsubscribed"]
        assert len(unsub_events) == 1
        assert unsub_events[0]["args"][0] == {"room": "hardware"}

    @patch("src.routes.websocket.metal_monitor")
    @patch("src.routes.websocket.psutil")
    def test_get_metrics(self, mock_psutil, mock_metal, client):
        """Emitting 'get_metrics' returns a 'metrics_update' event with system data."""
        mock_psutil.cpu_percent.return_value = 25.0
        mock_memory = MagicMock()
        mock_memory.percent = 60.0
        mock_memory.available = 16 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=2 * 1024**3)
        mock_process.num_threads.return_value = 8
        mock_psutil.Process.return_value = mock_process
        mock_metal._is_macos.return_value = False

        client.get_received()  # drain connect events
        client.emit("get_metrics")
        received = client.get_received()
        metrics_events = [e for e in received if e["name"] == "metrics_update"]
        assert len(metrics_events) == 1
        data = metrics_events[0]["args"][0]
        assert "system" in data
        assert "process" in data
        assert "application" in data
        assert "models" in data

    @patch("src.routes.websocket.gather_hardware_status")
    def test_get_hardware_status(self, mock_gather, client):
        """Emitting 'get_hardware_status' returns a 'hardware_status' event."""
        mock_gather.return_value = {
            "timestamp": time.time(),
            "thermal": {"thermal_state": "nominal"},
            "cpu": {"frequency_mhz": 3200, "usage_per_core": [10.0], "average_usage": 10.0},
            "performance_mode": "balanced",
        }
        client.get_received()
        client.emit("get_hardware_status")
        received = client.get_received()
        hw_events = [e for e in received if e["name"] == "hardware_status"]
        assert len(hw_events) == 1
        assert hw_events[0]["args"][0]["thermal"]["thermal_state"] == "nominal"

    def test_subscribe_download_no_task_id(self, client):
        """Subscribing to download progress without a task_id returns an error."""
        client.get_received()
        client.emit("subscribe_download", {})
        received = client.get_received()
        error_events = [e for e in received if e["name"] == "error"]
        assert len(error_events) == 1
        assert "task_id required" in error_events[0]["args"][0]["message"]

    def test_subscribe_download_with_status(self, client):
        """Subscribing to download progress with a valid task_id emits 'download_progress'."""
        mock_task = MagicMock()
        mock_task.task_id = "dl-123"
        mock_task.model_id = "org/test-model"
        mock_task.status.value = "downloading"
        mock_task.progress = 0.45
        mock_task.downloaded_bytes = 2 * 1024**3
        mock_task.total_bytes = 4 * 1024**3
        mock_task.speed_mbps = 120.5
        mock_task.eta_seconds = 60

        mock_dm_module = MagicMock()
        mock_dm_module.download_manager.get_task_status.return_value = mock_task

        # Lazy import resolves to gerdsen_ai_server.src.services.download_manager;
        # patch both the long-form and the conftest-aliased short-form module paths.
        modules_patch = {
            "gerdsen_ai_server.src.services.download_manager": mock_dm_module,
            "src.services.download_manager": mock_dm_module,
        }
        with patch.dict(sys.modules, modules_patch):
            client.get_received()
            client.emit("subscribe_download", {"task_id": "dl-123"})
            received = client.get_received()

        progress_events = [e for e in received if e["name"] == "download_progress"]
        assert len(progress_events) == 1
        payload = progress_events[0]["args"][0]
        assert payload["task_id"] == "dl-123"
        assert payload["model_id"] == "org/test-model"
        assert payload["status"] == "downloading"
        assert payload["progress"] == 0.45
        assert payload["speed_mbps"] == 120.5

    def test_subscribe_download_task_not_found(self, client):
        """Subscribing to download progress with unknown task_id emits no download_progress."""
        mock_dm_module = MagicMock()
        mock_dm_module.download_manager.get_task_status.return_value = None

        modules_patch = {
            "gerdsen_ai_server.src.services.download_manager": mock_dm_module,
            "src.services.download_manager": mock_dm_module,
        }
        with patch.dict(sys.modules, modules_patch):
            client.get_received()
            client.emit("subscribe_download", {"task_id": "nonexistent"})
            received = client.get_received()

        progress_events = [e for e in received if e["name"] == "download_progress"]
        assert len(progress_events) == 0

    def test_disconnect_removes_session(self, app):
        """Disconnecting removes the client from active_sessions."""
        flask_app, socketio, app_state = app
        test_client = socketio.test_client(flask_app)

        # After connect the session should exist
        assert len(app_state["active_sessions"]) == 1

        test_client.disconnect()

        # After disconnect the session should be removed
        assert len(app_state["active_sessions"]) == 0

    def test_connect_adds_session(self, client, app):
        """Connecting adds the client to active_sessions with metadata."""
        _, _, app_state = app
        assert len(app_state["active_sessions"]) == 1
        session = list(app_state["active_sessions"].values())[0]
        assert "connected_at" in session
        assert isinstance(session["rooms"], set)

    def test_subscribe_tracks_room_in_session(self, client, app):
        """Subscribing to a room adds it to the session's room set."""
        _, _, app_state = app
        client.get_received()
        client.emit("subscribe", {"room": "metrics"})
        client.get_received()

        session = list(app_state["active_sessions"].values())[0]
        assert "metrics" in session["rooms"]

    def test_unsubscribe_removes_room_from_session(self, client, app):
        """Unsubscribing from a room removes it from the session's room set."""
        _, _, app_state = app
        client.get_received()
        client.emit("subscribe", {"room": "logs"})
        client.get_received()
        client.emit("unsubscribe", {"room": "logs"})
        client.get_received()

        session = list(app_state["active_sessions"].values())[0]
        assert "logs" not in session["rooms"]


class TestGatherMetrics:
    """Tests for the gather_metrics() helper function."""

    @pytest.fixture
    def app_state(self):
        """Build a minimal app_state for gather_metrics testing."""
        return {
            "loaded_models": {"org/model-x": MagicMock()},
            "metrics": {"requests_total": 42, "tokens_generated": 500},
        }

    @patch("src.routes.websocket.metal_monitor")
    @patch("src.routes.websocket.psutil")
    def test_gather_metrics_structure(self, mock_psutil, mock_metal, app_state):
        """gather_metrics returns a dict with system, gpu, process, application, and models keys."""
        mock_psutil.cpu_percent.return_value = 30.0
        mock_memory = MagicMock()
        mock_memory.percent = 55.0
        mock_memory.available = 12 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1 * 1024**3)
        mock_process.num_threads.return_value = 6
        mock_psutil.Process.return_value = mock_process
        mock_metal._is_macos.return_value = False

        result = gather_metrics(app_state)

        assert "timestamp" in result
        assert isinstance(result["timestamp"], float)
        assert "system" in result
        assert "gpu" in result
        assert "process" in result
        assert "application" in result
        assert "models" in result

    @patch("src.routes.websocket.metal_monitor")
    @patch("src.routes.websocket.psutil")
    def test_gather_metrics_system_values(self, mock_psutil, mock_metal, app_state):
        """gather_metrics returns correct CPU and memory values under the system key."""
        mock_psutil.cpu_percent.return_value = 45.0
        mock_memory = MagicMock()
        mock_memory.percent = 70.0
        mock_memory.available = 8 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=2 * 1024**3)
        mock_process.num_threads.return_value = 4
        mock_psutil.Process.return_value = mock_process
        mock_metal._is_macos.return_value = False

        result = gather_metrics(app_state)

        assert result["system"]["cpu_percent"] == 45.0
        assert result["system"]["memory_percent"] == 70.0
        assert result["system"]["memory_available_gb"] == 8.0

    @patch("src.routes.websocket.metal_monitor")
    @patch("src.routes.websocket.psutil")
    def test_gather_metrics_process_values(self, mock_psutil, mock_metal, app_state):
        """gather_metrics returns RSS memory and thread count under the process key."""
        mock_psutil.cpu_percent.return_value = 10.0
        mock_memory = MagicMock()
        mock_memory.percent = 40.0
        mock_memory.available = 16 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=3 * 1024**3)
        mock_process.num_threads.return_value = 12
        mock_psutil.Process.return_value = mock_process
        mock_metal._is_macos.return_value = False

        result = gather_metrics(app_state)

        assert result["process"]["memory_gb"] == 3.0
        assert result["process"]["threads"] == 12

    @patch("src.routes.websocket.metal_monitor")
    @patch("src.routes.websocket.psutil")
    def test_gather_metrics_gpu_on_macos(self, mock_psutil, mock_metal, app_state):
        """gather_metrics includes GPU data when running on macOS with Metal available."""
        mock_psutil.cpu_percent.return_value = 20.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0, available=16 * 1024**3)
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1 * 1024**3)
        mock_process.num_threads.return_value = 4
        mock_psutil.Process.return_value = mock_process

        mock_metal._is_macos.return_value = True
        mock_gpu = MagicMock()
        mock_gpu.gpu_utilization = 60.0
        mock_gpu.memory_used_gb = 10.0
        mock_gpu.memory_bandwidth_utilization = 35.0
        mock_metal.get_current_metrics.return_value = mock_gpu

        result = gather_metrics(app_state)

        assert result["gpu"] is not None
        assert result["gpu"]["utilization_percent"] == 60.0
        assert result["gpu"]["memory_used_gb"] == 10.0
        assert result["gpu"]["memory_bandwidth_percent"] == 35.0

    @patch("src.routes.websocket.metal_monitor")
    @patch("src.routes.websocket.psutil")
    def test_gather_metrics_gpu_none_when_not_macos(self, mock_psutil, mock_metal, app_state):
        """gather_metrics returns gpu=None when not on macOS."""
        mock_psutil.cpu_percent.return_value = 20.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0, available=16 * 1024**3)
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1 * 1024**3)
        mock_process.num_threads.return_value = 4
        mock_psutil.Process.return_value = mock_process
        mock_metal._is_macos.return_value = False

        result = gather_metrics(app_state)

        assert result["gpu"] is None

    @patch("src.routes.websocket.metal_monitor")
    @patch("src.routes.websocket.psutil")
    def test_gather_metrics_models_info(self, mock_psutil, mock_metal, app_state):
        """gather_metrics includes loaded model count and names under the models key."""
        mock_psutil.cpu_percent.return_value = 10.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=40.0, available=20 * 1024**3)
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1 * 1024**3)
        mock_process.num_threads.return_value = 4
        mock_psutil.Process.return_value = mock_process
        mock_metal._is_macos.return_value = False

        result = gather_metrics(app_state)

        assert result["models"]["loaded_count"] == 1
        assert result["models"]["loaded_models"] == ["org/model-x"]

    @patch("src.routes.websocket.metal_monitor")
    @patch("src.routes.websocket.psutil")
    def test_gather_metrics_application_passthrough(self, mock_psutil, mock_metal, app_state):
        """gather_metrics passes through the application metrics from app_state."""
        mock_psutil.cpu_percent.return_value = 10.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=40.0, available=20 * 1024**3)
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1 * 1024**3)
        mock_process.num_threads.return_value = 4
        mock_psutil.Process.return_value = mock_process
        mock_metal._is_macos.return_value = False

        result = gather_metrics(app_state)

        assert result["application"] == {"requests_total": 42, "tokens_generated": 500}

    @patch("src.routes.websocket.metal_monitor")
    @patch("src.routes.websocket.psutil")
    def test_gather_metrics_gpu_exception_handled(self, mock_psutil, mock_metal, app_state):
        """gather_metrics returns gpu=None when Metal metrics raise an exception."""
        mock_psutil.cpu_percent.return_value = 10.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=40.0, available=20 * 1024**3)
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1 * 1024**3)
        mock_process.num_threads.return_value = 4
        mock_psutil.Process.return_value = mock_process
        mock_metal._is_macos.return_value = True
        mock_metal.get_current_metrics.side_effect = RuntimeError("Metal unavailable")

        result = gather_metrics(app_state)

        assert result["gpu"] is None


class TestGatherHardwareStatus:
    """Tests for the gather_hardware_status() helper function."""

    @pytest.fixture
    def app_state(self):
        """Build a minimal app_state for gather_hardware_status testing."""
        return {
            "hardware_info": {"performance_mode": "balanced"},
        }

    @patch("src.routes.websocket.psutil")
    @patch("src.routes.websocket.get_thermal_state")
    def test_gather_hardware_status_structure(self, mock_thermal, mock_psutil, app_state):
        """gather_hardware_status returns a dict with timestamp, thermal, cpu, and performance_mode keys."""
        mock_thermal.return_value = {"thermal_state": "nominal"}
        mock_psutil.cpu_freq.return_value = MagicMock(current=3200.0)
        mock_psutil.cpu_percent.return_value = [15.0, 20.0, 18.0, 12.0]

        result = gather_hardware_status(app_state)

        assert "timestamp" in result
        assert isinstance(result["timestamp"], float)
        assert "thermal" in result
        assert "cpu" in result
        assert "performance_mode" in result

    @patch("src.routes.websocket.psutil")
    @patch("src.routes.websocket.get_thermal_state")
    def test_gather_hardware_status_thermal(self, mock_thermal, mock_psutil, app_state):
        """gather_hardware_status passes through the thermal state from get_thermal_state."""
        mock_thermal.return_value = {"thermal_state": "serious", "pressure_level": "critical"}
        mock_psutil.cpu_freq.return_value = MagicMock(current=2800.0)
        mock_psutil.cpu_percent.return_value = [50.0, 60.0]

        result = gather_hardware_status(app_state)

        assert result["thermal"]["thermal_state"] == "serious"
        assert result["thermal"]["pressure_level"] == "critical"

    @patch("src.routes.websocket.psutil")
    @patch("src.routes.websocket.get_thermal_state")
    def test_gather_hardware_status_cpu_values(self, mock_thermal, mock_psutil, app_state):
        """gather_hardware_status returns frequency, per-core usage, and average usage."""
        mock_thermal.return_value = {"thermal_state": "nominal"}
        mock_psutil.cpu_freq.return_value = MagicMock(current=3000.0)
        mock_psutil.cpu_percent.return_value = [10.0, 20.0, 30.0, 40.0]

        result = gather_hardware_status(app_state)

        assert result["cpu"]["frequency_mhz"] == 3000.0
        assert result["cpu"]["usage_per_core"] == [10.0, 20.0, 30.0, 40.0]
        assert result["cpu"]["average_usage"] == 25.0

    @patch("src.routes.websocket.psutil")
    @patch("src.routes.websocket.get_thermal_state")
    def test_gather_hardware_status_no_cpu_freq(self, mock_thermal, mock_psutil, app_state):
        """gather_hardware_status returns frequency_mhz=0 when cpu_freq is None."""
        mock_thermal.return_value = {"thermal_state": "nominal"}
        mock_psutil.cpu_freq.return_value = None
        mock_psutil.cpu_percent.return_value = [25.0]

        result = gather_hardware_status(app_state)

        assert result["cpu"]["frequency_mhz"] == 0

    @patch("src.routes.websocket.psutil")
    @patch("src.routes.websocket.get_thermal_state")
    def test_gather_hardware_status_performance_mode(self, mock_thermal, mock_psutil, app_state):
        """gather_hardware_status reads performance_mode from app_state hardware_info."""
        app_state["hardware_info"]["performance_mode"] = "performance"
        mock_thermal.return_value = {"thermal_state": "nominal"}
        mock_psutil.cpu_freq.return_value = MagicMock(current=3500.0)
        mock_psutil.cpu_percent.return_value = [80.0, 85.0]

        result = gather_hardware_status(app_state)

        assert result["performance_mode"] == "performance"

    @patch("src.routes.websocket.psutil")
    @patch("src.routes.websocket.get_thermal_state")
    def test_gather_hardware_status_default_performance_mode(self, mock_thermal, mock_psutil):
        """gather_hardware_status defaults performance_mode to 'balanced' when not set."""
        app_state = {"hardware_info": {}}
        mock_thermal.return_value = {"thermal_state": "nominal"}
        mock_psutil.cpu_freq.return_value = MagicMock(current=3200.0)
        mock_psutil.cpu_percent.return_value = [20.0]

        result = gather_hardware_status(app_state)

        assert result["performance_mode"] == "balanced"
