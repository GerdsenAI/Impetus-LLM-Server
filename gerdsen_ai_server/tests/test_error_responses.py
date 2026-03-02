"""
Unit tests for user-friendly error responses (utils/error_responses.py).
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.utils.error_responses import ErrorResponse, handle_error


class TestErrorResponse:
    """Tests for ErrorResponse static methods."""

    @pytest.fixture
    def app(self):
        """Create test Flask app for JSON serialization context."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        return app

    def test_model_not_found(self, app):
        """model_not_found returns 404 with suggestions."""
        with app.app_context():
            response, status = ErrorResponse.model_not_found("test-model")
            assert status == 404
            data = json.loads(response.data)
            assert data["error"] == "Model not found"
            assert data["model_id"] == "test-model"
            assert len(data["suggestions"]) > 0

    def test_insufficient_memory(self, app):
        """insufficient_memory returns 507 with memory info."""
        with app.app_context():
            response, status = ErrorResponse.insufficient_memory(8.0, 4.5)
            assert status == 507
            data = json.loads(response.data)
            assert "8.0GB" in data["message"]
            assert "4.5GB" in data["message"]
            assert data["required_gb"] == 8.0

    def test_port_in_use(self, app):
        """port_in_use returns 500 with port info and suggestions."""
        with app.app_context():
            response, status = ErrorResponse.port_in_use(8080)
            assert status == 500
            data = json.loads(response.data)
            assert data["port"] == 8080
            assert any("8080" in s for s in data["suggestions"])

    def test_mlx_not_available(self, app):
        """mlx_not_available returns 500 with install suggestions."""
        with app.app_context():
            response, status = ErrorResponse.mlx_not_available()
            assert status == 500
            data = json.loads(response.data)
            assert "MLX" in data["error"]
            assert any("pip install" in s for s in data["suggestions"])

    def test_model_load_failed_memory_error(self, app):
        """model_load_failed adds memory-specific suggestion for memory errors."""
        with app.app_context():
            response, status = ErrorResponse.model_load_failed("test", "Out of memory")
            assert status == 500
            data = json.loads(response.data)
            assert any("smaller" in s.lower() for s in data["suggestions"])

    def test_model_load_failed_generic(self, app):
        """model_load_failed returns generic suggestions for unknown errors."""
        with app.app_context():
            response, status = ErrorResponse.model_load_failed("test", "unknown error")
            assert status == 500
            data = json.loads(response.data)
            assert data["model_id"] == "test"

    def test_invalid_request(self, app):
        """invalid_request returns 400 with field and expected format."""
        with app.app_context():
            response, status = ErrorResponse.invalid_request("model_id", "string")
            assert status == 400
            data = json.loads(response.data)
            assert data["field"] == "model_id"
            assert data["expected"] == "string"

    def test_thermal_throttling(self, app):
        """thermal_throttling returns 503 with cooling suggestions."""
        with app.app_context():
            response, status = ErrorResponse.thermal_throttling()
            assert status == 503
            data = json.loads(response.data)
            assert "thermal" in data["error"].lower()


class TestHandleError:
    """Tests for the handle_error routing function."""

    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        return app

    @patch("src.utils.error_responses.psutil")
    def test_routes_memory_error(self, mock_psutil, app):
        """Memory-related errors route to insufficient_memory."""
        mock_psutil.virtual_memory.return_value = MagicMock(available=4 * 1024**3)
        with app.app_context():
            _, status = handle_error(RuntimeError("Out of memory"), "loading model")
            assert status == 507

    def test_routes_mlx_error(self, app):
        """MLX import errors route to mlx_not_available."""
        with app.app_context():
            _, status = handle_error(ImportError("mlx not found"), "init")
            assert status == 500

    def test_routes_thermal_error(self, app):
        """Thermal errors route to thermal_throttling."""
        with app.app_context():
            _, status = handle_error(RuntimeError("thermal throttling detected"), "inference")
            assert status == 503

    def test_routes_generic_error(self, app):
        """Unknown errors route to generic_error."""
        with app.app_context():
            _, status = handle_error(RuntimeError("something weird"), "test")
            assert status == 500
