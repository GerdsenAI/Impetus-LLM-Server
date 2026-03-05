"""
Unit tests for error recovery and resilience system (utils/error_recovery.py).
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from src.utils.error_recovery import (
    ErrorEvent,
    ErrorRecoveryService,
    ErrorType,
    with_memory_limit,
)


class TestErrorRecoveryService:
    """Tests for the ErrorRecoveryService."""

    @pytest.fixture
    def service(self):
        """Create fresh ErrorRecoveryService."""
        return ErrorRecoveryService(max_history=10)

    def test_handle_error_records_event(self, service):
        """handle_error adds event to error_history."""
        service.handle_error(ErrorType.UNKNOWN, RuntimeError("test"))
        assert len(service.error_history) == 1
        assert service.error_history[0].error_type == ErrorType.UNKNOWN

    def test_handle_error_returns_false_for_unknown(self, service):
        """handle_error returns False for UNKNOWN error type with no strategy."""
        result = service.handle_error(ErrorType.UNKNOWN, RuntimeError("test"))
        assert result is False

    def test_failure_loop_detection(self, service):
        """Failure loop is detected after 3 errors within 5 minutes."""
        for _ in range(3):
            service.handle_error(ErrorType.NETWORK_ERROR, RuntimeError("fail"))

        # 4th error should detect failure loop
        result = service.handle_error(ErrorType.NETWORK_ERROR, RuntimeError("fail again"))
        assert result is False

    def test_no_failure_loop_different_types(self, service):
        """Different error types don't trigger failure loop."""
        service.handle_error(ErrorType.NETWORK_ERROR, RuntimeError("net"))
        service.handle_error(ErrorType.OUT_OF_MEMORY, RuntimeError("oom"))
        service.handle_error(ErrorType.DOWNLOAD_FAILURE, RuntimeError("dl"))

        assert not service._is_failure_loop(ErrorType.NETWORK_ERROR)

    def test_oom_recovery_without_app_state(self, service):
        """OOM recovery returns False without app_state."""
        result = service.handle_error(ErrorType.OUT_OF_MEMORY, RuntimeError("oom"))
        assert result is False

    def test_oom_recovery_unloads_model(self, service):
        """OOM recovery unloads least recently used model."""
        mock_model = MagicMock()
        service.app_state = {
            "loaded_models": {"model-a": mock_model},
            "socketio": None,
        }

        result = service.handle_error(ErrorType.OUT_OF_MEMORY, RuntimeError("oom"))
        assert result is True
        assert "model-a" not in service.app_state["loaded_models"]
        mock_model.unload.assert_called_once()

    @patch("src.utils.error_recovery.time.sleep")
    def test_thermal_recovery_switches_mode(self, mock_sleep, service):
        """Thermal recovery switches to efficiency mode."""
        import gerdsen_ai_server.src.config.settings as settings_mod

        service.app_state = {"loaded_models": {}}
        with patch.object(settings_mod, "settings") as mock_settings:
            mock_settings.hardware = MagicMock()
            mock_settings.inference = MagicMock()
            mock_settings.inference.max_tokens = 2048

            result = service.handle_error(ErrorType.THERMAL_THROTTLE, RuntimeError("hot"))
            assert result is True
            assert mock_settings.hardware.performance_mode == "efficiency"

    def test_network_error_recovery(self, service):
        """Network error recovery returns True (will retry)."""
        result = service.handle_error(ErrorType.NETWORK_ERROR, RuntimeError("timeout"))
        assert result is True

    def test_inference_failure_oom_reduces_tokens(self, service):
        """Inference failure with OOM reduces max_tokens."""
        import gerdsen_ai_server.src.config.settings as settings_mod

        with patch.object(settings_mod, "settings") as mock_settings:
            mock_settings.inference = MagicMock()
            mock_settings.inference.max_tokens = 2048

            result = service.handle_error(
                ErrorType.INFERENCE_FAILURE, RuntimeError("out of memory during inference")
            )
            assert result is True

    def test_max_history_enforced(self, service):
        """Error history respects maxlen."""
        for i in range(20):
            service.handle_error(ErrorType.UNKNOWN, RuntimeError(f"error {i}"))
        assert len(service.error_history) == 10

    def test_set_app_state(self, service):
        """set_app_state stores reference to app state."""
        state = {"loaded_models": {}}
        service.set_app_state(state)
        assert service.app_state is state


class TestErrorEvent:
    """Tests for ErrorEvent dataclass."""

    def test_error_event_defaults(self):
        """ErrorEvent has recovered=False by default."""
        event = ErrorEvent(
            error_type=ErrorType.UNKNOWN,
            timestamp=datetime.now(),
            message="test",
            context={},
        )
        assert event.recovered is False

    def test_error_event_fields(self):
        """ErrorEvent stores all fields correctly."""
        now = datetime.now()
        event = ErrorEvent(
            error_type=ErrorType.OUT_OF_MEMORY,
            timestamp=now,
            message="oom",
            context={"model": "test"},
            recovered=True,
        )
        assert event.error_type == ErrorType.OUT_OF_MEMORY
        assert event.timestamp == now
        assert event.context["model"] == "test"
        assert event.recovered is True


class TestWithMemoryLimit:
    """Tests for the with_memory_limit decorator."""

    @patch("src.utils.error_recovery.psutil")
    def test_memory_within_limit(self, mock_psutil):
        """Function executes normally when within memory limit."""
        mock_memory = MagicMock()
        mock_memory.used = 4 * 1024**3  # 4GB used
        mock_psutil.virtual_memory.return_value = mock_memory

        @with_memory_limit(max_memory_gb=16.0)
        def my_func():
            return "ok"

        assert my_func() == "ok"

    @patch("src.utils.error_recovery.psutil")
    def test_memory_exceeds_limit(self, mock_psutil):
        """MemoryError raised when memory exceeds limit."""
        mock_memory = MagicMock()
        mock_memory.used = 20 * 1024**3  # 20GB used
        mock_psutil.virtual_memory.return_value = mock_memory

        @with_memory_limit(max_memory_gb=16.0)
        def my_func():
            return "ok"

        with pytest.raises(MemoryError, match="exceeds limit"):
            my_func()
