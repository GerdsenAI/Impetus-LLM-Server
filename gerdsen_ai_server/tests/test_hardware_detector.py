"""
Unit tests for Apple Silicon hardware detection (utils/hardware_detector.py).
"""

from unittest.mock import MagicMock, patch

import pytest

from src.utils.hardware_detector import (
    detect_apple_silicon,
    detect_hardware,
    get_memory_info,
    get_thermal_state,
    run_command,
)


class TestRunCommand:
    """Tests for run_command utility."""

    @patch("src.utils.hardware_detector.subprocess.run")
    def test_successful_command(self, mock_run):
        """Successful command returns stripped stdout."""
        mock_run.return_value = MagicMock(stdout="  output  ")
        result = run_command(["echo", "test"])
        assert result == "output"

    @patch("src.utils.hardware_detector.subprocess.run")
    def test_failed_command_returns_none(self, mock_run):
        """Failed command returns None."""
        mock_run.side_effect = Exception("command failed")
        result = run_command(["nonexistent"])
        assert result is None


class TestDetectAppleSilicon:
    """Tests for detect_apple_silicon function."""

    @patch("src.utils.hardware_detector.platform")
    def test_non_darwin_returns_unknown(self, mock_platform):
        """Non-macOS returns Unknown chip type."""
        mock_platform.system.return_value = "Linux"
        mock_platform.machine.return_value = "x86_64"
        result = detect_apple_silicon()
        assert result["chip_type"] == "Unknown"

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m2_pro_detection(self, mock_platform, mock_run_command):
        """M2 Pro chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"

        def side_effect(cmd):
            if cmd == ["sysctl", "-n", "machdep.cpu.brand_string"]:
                return "Apple M2 Pro"
            if cmd == ["sysctl", "-n", "hw.perflevel0.physicalcpu"]:
                return "6"
            if cmd == ["sysctl", "-n", "hw.perflevel1.physicalcpu"]:
                return "4"
            return None

        mock_run_command.side_effect = side_effect
        result = detect_apple_silicon()
        assert result["chip_type"] == "M2 Pro"
        assert result["performance_cores"] == 6
        assert result["efficiency_cores"] == 4
        assert result["neural_engine_cores"] == 16

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m4_max_detection(self, mock_platform, mock_run_command):
        """M4 Max chip is correctly identified with bandwidth."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"

        def side_effect(cmd):
            if cmd == ["sysctl", "-n", "machdep.cpu.brand_string"]:
                return "Apple M4 Max"
            return None

        mock_run_command.side_effect = side_effect
        result = detect_apple_silicon()
        assert result["chip_type"] == "M4 Max"
        assert result["max_memory_bandwidth_gbps"] == 546

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m1_base_detection(self, mock_platform, mock_run_command):
        """Base M1 chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"

        def side_effect(cmd):
            if cmd == ["sysctl", "-n", "machdep.cpu.brand_string"]:
                return "Apple M1"
            return None

        mock_run_command.side_effect = side_effect
        result = detect_apple_silicon()
        assert result["chip_type"] == "M1"
        assert result["gpu_cores"] == 8


class TestGetMemoryInfo:
    """Tests for get_memory_info function."""

    @patch("src.utils.hardware_detector.psutil")
    def test_memory_info_structure(self, mock_psutil):
        """Returns dict with expected memory keys."""
        mock_memory = MagicMock()
        mock_memory.total = 32 * 1024**3
        mock_memory.available = 16 * 1024**3
        mock_memory.used = 16 * 1024**3
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory

        result = get_memory_info()
        assert "total_memory_gb" in result
        assert "available_memory_gb" in result
        assert abs(result["total_memory_gb"] - 32.0) < 0.1


class TestGetThermalState:
    """Tests for get_thermal_state function."""

    @patch("src.utils.hardware_detector.platform")
    def test_non_darwin_returns_nominal(self, mock_platform):
        """Non-macOS returns nominal thermal state."""
        mock_platform.system.return_value = "Linux"
        result = get_thermal_state()
        assert result["thermal_state"] == "nominal"

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_nominal_thermal_level(self, mock_platform, mock_run_command):
        """Thermal level 0 maps to nominal."""
        mock_platform.system.return_value = "Darwin"
        mock_run_command.return_value = "0"
        result = get_thermal_state()
        assert result["thermal_state"] == "nominal"

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_serious_thermal_level(self, mock_platform, mock_run_command):
        """Thermal level 60 maps to serious."""
        mock_platform.system.return_value = "Darwin"
        mock_run_command.return_value = "60"
        result = get_thermal_state()
        assert result["thermal_state"] == "serious"
        assert result["thermal_pressure"] == 60


class TestDetectHardware:
    """Tests for detect_hardware function."""

    @patch("src.utils.hardware_detector.get_thermal_state")
    @patch("src.utils.hardware_detector.get_memory_info")
    @patch("src.utils.hardware_detector.psutil")
    @patch("src.utils.hardware_detector.platform")
    def test_basic_hardware_info(self, mock_platform, mock_psutil, mock_memory, mock_thermal):
        """detect_hardware returns platform, cpu_count, and memory."""
        mock_platform.system.return_value = "Linux"
        mock_platform.version.return_value = "5.0"
        mock_platform.machine.return_value = "x86_64"
        mock_platform.processor.return_value = "x86_64"
        mock_psutil.cpu_count.side_effect = [8, 4]
        mock_memory.return_value = {"total_memory_gb": 16.0, "available_memory_gb": 8.0}
        mock_thermal.return_value = {"thermal_state": "nominal"}

        result = detect_hardware()
        assert result["platform"] == "Linux"
        assert result["cpu_count"] == 8
        assert result["total_memory_gb"] == 16.0

    @patch("src.utils.hardware_detector.get_thermal_state")
    @patch("src.utils.hardware_detector.get_memory_info")
    @patch("src.utils.hardware_detector.detect_ane_availability")
    @patch("src.utils.hardware_detector.detect_apple_silicon")
    @patch("src.utils.hardware_detector.psutil")
    @patch("src.utils.hardware_detector.platform")
    def test_apple_silicon_recommendations(
        self, mock_platform, mock_psutil, mock_silicon, mock_ane, mock_memory, mock_thermal
    ):
        """Apple Silicon with high bandwidth gets increased batch size."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.version.return_value = "23.0"
        mock_platform.machine.return_value = "arm64"
        mock_platform.processor.return_value = "arm"
        mock_psutil.cpu_count.side_effect = [12, 6]
        mock_silicon.return_value = {
            "chip_type": "M2 Max",
            "max_memory_bandwidth_gbps": 400,
            "performance_cores": 8,
            "efficiency_cores": 4,
        }
        mock_ane.return_value = {"available": True, "version": 2, "compute_units": "cpu_and_ne"}
        mock_memory.return_value = {"total_memory_gb": 64.0, "available_memory_gb": 32.0}
        mock_thermal.return_value = {"thermal_state": "nominal"}

        result = detect_hardware()
        assert result["chip_type"] == "M2 Max"
        assert result["recommended_batch_size"] == 4
        assert result["recommended_context_length"] == 8192
