"""
Unit tests for application settings (config/settings.py).
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.config.settings import (
    ComputeSettings,
    HardwareSettings,
    InferenceSettings,
    ModelSettings,
    ServerSettings,
    Settings,
)


class TestServerSettings:
    """Tests for ServerSettings."""

    def test_default_host(self):
        """Default host is 127.0.0.1 (local-only binding)."""
        s = ServerSettings()
        assert s.host == "127.0.0.1"

    def test_default_port(self):
        """Default port is 8080."""
        s = ServerSettings()
        assert s.port == 8080

    def test_default_api_key_none(self):
        """Default API key is None."""
        s = ServerSettings()
        assert s.api_key is None

    def test_cors_origins(self):
        """Default CORS origins include localhost:3000 and :5173."""
        s = ServerSettings()
        assert "http://localhost:3000" in s.cors_origins
        assert "http://localhost:5173" in s.cors_origins


class TestModelSettings:
    """Tests for ModelSettings."""

    def test_default_max_loaded_models(self):
        """Default max loaded models is 3."""
        s = ModelSettings()
        assert s.max_loaded_models == 3

    def test_default_model(self):
        """Default model is Mistral-7B-Instruct 4bit."""
        s = ModelSettings()
        assert "Mistral-7B" in s.default_model

    def test_models_dir_is_path(self):
        """models_dir is a Path object."""
        s = ModelSettings()
        assert isinstance(s.models_dir, Path)

    def test_require_model_for_ready_default(self):
        """require_model_for_ready defaults to False."""
        s = ModelSettings()
        assert s.require_model_for_ready is False


class TestInferenceSettings:
    """Tests for InferenceSettings."""

    def test_default_temperature(self):
        """Default temperature is 0.7."""
        s = InferenceSettings()
        assert s.temperature == 0.7

    def test_default_max_tokens(self):
        """Default max tokens is 2048."""
        s = InferenceSettings()
        assert s.max_tokens == 2048

    def test_default_top_p(self):
        """Default top_p is 0.95."""
        s = InferenceSettings()
        assert s.top_p == 0.95


class TestHardwareSettings:
    """Tests for HardwareSettings."""

    def test_default_performance_mode(self):
        """Default performance mode is balanced."""
        s = HardwareSettings()
        assert s.performance_mode == "balanced"

    def test_default_max_cpu_percent(self):
        """Default max CPU percent is 80.0."""
        s = HardwareSettings()
        assert s.max_cpu_percent == 80.0

    def test_default_max_memory_percent(self):
        """Default max memory percent is 75.0."""
        s = HardwareSettings()
        assert s.max_memory_percent == 75.0


class TestComputeSettings:
    """Tests for ComputeSettings."""

    def test_default_preferred_device(self):
        """Default preferred embedding device is auto."""
        s = ComputeSettings()
        assert s.preferred_embedding_device == "auto"

    def test_default_embedding_model(self):
        """Default embedding model is all-MiniLM-L6-v2."""
        s = ComputeSettings()
        assert s.default_embedding_model == "all-MiniLM-L6-v2"


class TestSettings:
    """Tests for the top-level Settings class."""

    def test_settings_has_all_subsections(self):
        """Settings contains all subsetting groups."""
        s = Settings()
        assert isinstance(s.server, ServerSettings)
        assert isinstance(s.model, ModelSettings)
        assert isinstance(s.inference, InferenceSettings)
        assert isinstance(s.hardware, HardwareSettings)
        assert isinstance(s.compute, ComputeSettings)

    def test_default_environment(self):
        """Default environment is development."""
        s = Settings()
        assert s.environment == "development"

    def test_default_version(self):
        """Version is set."""
        s = Settings()
        assert s.version == "0.1.0"

    def test_app_name(self):
        """App name is Impetus LLM Server."""
        s = Settings()
        assert s.app_name == "Impetus LLM Server"
