"""
Unit tests for Apple Silicon hardware detection (utils/hardware_detector.py).
"""

from unittest.mock import MagicMock, patch

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


class TestDetectAppleSiliconM3:
    """Tests for M3 family chip detection."""

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m3_base_detection(self, mock_platform, mock_run_command):
        """Base M3 chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M3" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M3"
        assert result["gpu_cores"] == 10
        assert result["max_memory_bandwidth_gbps"] == 100

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m3_pro_detection(self, mock_platform, mock_run_command):
        """M3 Pro chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M3 Pro" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M3 Pro"
        assert result["gpu_cores"] == 18
        assert result["max_memory_bandwidth_gbps"] == 150

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m3_max_detection(self, mock_platform, mock_run_command):
        """M3 Max chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M3 Max" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M3 Max"
        assert result["gpu_cores"] == 40
        assert result["max_memory_bandwidth_gbps"] == 400

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m3_ultra_detection(self, mock_platform, mock_run_command):
        """M3 Ultra chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M3 Ultra" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M3 Ultra"
        assert result["gpu_cores"] == 76
        assert result["max_memory_bandwidth_gbps"] == 800


class TestDetectAppleSiliconM5:
    """Tests for M5 family chip detection."""

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m5_base_detection(self, mock_platform, mock_run_command):
        """Base M5 chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M5" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M5"
        assert result["gpu_cores"] == 12
        assert result["max_memory_bandwidth_gbps"] == 150

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m5_pro_detection(self, mock_platform, mock_run_command):
        """M5 Pro chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M5 Pro" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M5 Pro"
        assert result["gpu_cores"] == 24
        assert result["max_memory_bandwidth_gbps"] == 300

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m5_max_detection(self, mock_platform, mock_run_command):
        """M5 Max chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M5 Max" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M5 Max"
        assert result["gpu_cores"] == 48
        assert result["max_memory_bandwidth_gbps"] == 600

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m5_ultra_detection(self, mock_platform, mock_run_command):
        """M5 Ultra chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M5 Ultra" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M5 Ultra"
        assert result["gpu_cores"] == 80
        assert result["max_memory_bandwidth_gbps"] == 1200


class TestDetectAppleSiliconExtras:
    """Tests for remaining Apple Silicon detection branches."""

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m1_ultra_detection(self, mock_platform, mock_run_command):
        """M1 Ultra chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M1 Ultra" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M1 Ultra"
        assert result["gpu_cores"] == 64

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m1_max_detection(self, mock_platform, mock_run_command):
        """M1 Max chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M1 Max" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M1 Max"
        assert result["gpu_cores"] == 32

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m1_pro_detection(self, mock_platform, mock_run_command):
        """M1 Pro chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M1 Pro" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M1 Pro"
        assert result["gpu_cores"] == 16

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m2_ultra_detection(self, mock_platform, mock_run_command):
        """M2 Ultra chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M2 Ultra" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M2 Ultra"
        assert result["gpu_cores"] == 76

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m2_max_detection(self, mock_platform, mock_run_command):
        """M2 Max chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M2 Max" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M2 Max"
        assert result["gpu_cores"] == 38

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m2_base_detection(self, mock_platform, mock_run_command):
        """Base M2 chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M2" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M2"
        assert result["gpu_cores"] == 10
        assert result["max_memory_bandwidth_gbps"] == 100

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m4_pro_detection(self, mock_platform, mock_run_command):
        """M4 Pro chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M4 Pro" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M4 Pro"
        assert result["gpu_cores"] == 20
        assert result["max_memory_bandwidth_gbps"] == 273

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_m4_base_detection(self, mock_platform, mock_run_command):
        """Base M4 chip is correctly identified."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.side_effect = lambda cmd: (
            "Apple M4" if any("brand_string" in c for c in cmd) else None
        )
        result = detect_apple_silicon()
        assert result["chip_type"] == "M4"
        assert result["gpu_cores"] == 10
        assert result["max_memory_bandwidth_gbps"] == 120

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_no_brand_string_returns_unknown(self, mock_platform, mock_run_command):
        """When sysctl returns None for brand_string, chip_type stays Unknown."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_run_command.return_value = None
        result = detect_apple_silicon()
        assert result["chip_type"] == "Unknown"
        assert result["neural_engine_cores"] == 0


class TestDetectAneAvailability:
    """Tests for detect_ane_availability function."""

    @patch("src.utils.hardware_detector.platform")
    def test_non_darwin_returns_unavailable(self, mock_platform):
        """Non-macOS returns ANE unavailable."""
        from src.utils.hardware_detector import detect_ane_availability

        mock_platform.system.return_value = "Linux"
        mock_platform.machine.return_value = "x86_64"
        result = detect_ane_availability()
        assert result["available"] is False
        assert result["compute_units"] == "cpu_only"

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_ane_version_detected(self, mock_platform, mock_run_command):
        """ANE version detected via sysctl."""
        from src.utils.hardware_detector import detect_ane_availability

        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"

        def side_effect(cmd):
            cmd_str = " ".join(cmd)
            if "ane.version" in cmd_str:
                return "2"
            if "brand_string" in cmd_str:
                return "Apple M2 Pro"
            return None

        mock_run_command.side_effect = side_effect
        result = detect_ane_availability()
        assert result["available"] is True
        assert result["version"] == 2
        assert result["compute_units"] == "cpu_and_ne"

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_ane_fallback_from_brand_string(self, mock_platform, mock_run_command):
        """ANE availability detected from brand string when sysctl key missing."""
        from src.utils.hardware_detector import detect_ane_availability

        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"

        def side_effect(cmd):
            cmd_str = " ".join(cmd)
            if "ane.version" in cmd_str:
                return None
            if "brand_string" in cmd_str:
                return "Apple M3"
            return None

        mock_run_command.side_effect = side_effect
        result = detect_ane_availability()
        assert result["available"] is True
        assert result["compute_units"] == "cpu_and_ne"

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_ane_version_parse_error(self, mock_platform, mock_run_command):
        """Invalid ANE version string doesn't crash."""
        from src.utils.hardware_detector import detect_ane_availability

        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"

        def side_effect(cmd):
            cmd_str = " ".join(cmd)
            if "ane.version" in cmd_str:
                return "not_a_number"
            if "brand_string" in cmd_str:
                return "Apple M1"
            return None

        mock_run_command.side_effect = side_effect
        result = detect_ane_availability()
        assert result["available"] is True
        assert result["version"] == 0


class TestThermalStateExtras:
    """Additional tests for thermal state branches."""

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_fair_thermal_level(self, mock_platform, mock_run_command):
        """Thermal level 25 maps to fair."""
        mock_platform.system.return_value = "Darwin"
        mock_run_command.return_value = "25"
        result = get_thermal_state()
        assert result["thermal_state"] == "fair"
        assert result["thermal_pressure"] == 25

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_critical_thermal_level(self, mock_platform, mock_run_command):
        """Thermal level 90 maps to critical."""
        mock_platform.system.return_value = "Darwin"
        mock_run_command.return_value = "90"
        result = get_thermal_state()
        assert result["thermal_state"] == "critical"
        assert result["thermal_pressure"] == 90

    @patch("src.utils.hardware_detector.run_command")
    @patch("src.utils.hardware_detector.platform")
    def test_thermal_command_fails(self, mock_platform, mock_run_command):
        """When sysctl fails, thermal stays nominal."""
        mock_platform.system.return_value = "Darwin"
        mock_run_command.return_value = None
        result = get_thermal_state()
        assert result["thermal_state"] == "nominal"
        assert result["thermal_pressure"] == 0


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
