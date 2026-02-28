"""
E2E tests: Hardware monitoring — info, metrics, GPU, performance modes.

Tests the hardware observation and tuning endpoints.
"""

import pytest
import requests

pytestmark = [pytest.mark.e2e]


class TestHardwareMonitoring:
    """Hardware info and metrics endpoints."""

    def test_hardware_info(self, e2e_server, base_url):
        """GET /api/hardware/info returns chip and memory info."""
        r = requests.get(f"{base_url}/api/hardware/info", timeout=10)
        assert r.status_code == 200
        data = r.json()
        # Should contain chip_type or chip or similar hardware identification
        has_chip = any(
            k in data for k in ("chip_type", "chip", "processor", "cpu_brand")
        )
        assert has_chip, f"No chip identifier found in: {list(data.keys())}"

    def test_hardware_metrics(self, e2e_server, base_url):
        """GET /api/hardware/metrics returns CPU and memory stats."""
        r = requests.get(f"{base_url}/api/hardware/metrics", timeout=10)
        # May return 500 on sandboxed environments (CI)
        if r.status_code == 200:
            data = r.json()
            assert "cpu" in data
            assert "memory" in data
        else:
            # Tolerate 500 on CI runners with restricted psutil
            assert r.status_code == 500

    def test_gpu_metrics(self, e2e_server, base_url):
        """GET /api/hardware/gpu/metrics returns GPU data on macOS."""
        r = requests.get(f"{base_url}/api/hardware/gpu/metrics", timeout=10)
        # 200 on real macOS, 404 on non-macOS, 500 on error
        assert r.status_code in (200, 404, 500)
        if r.status_code == 200:
            data = r.json()
            assert "current" in data

    def test_optimization_recommendations(self, e2e_server, base_url):
        """GET /api/hardware/optimization returns recommendations."""
        r = requests.get(f"{base_url}/api/hardware/optimization", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "recommendations" in data
        assert "current_performance_mode" in data

    def test_performance_mode_set(self, e2e_server, base_url):
        """POST /api/hardware/performance-mode changes the mode."""
        r = requests.post(
            f"{base_url}/api/hardware/performance-mode",
            json={"mode": "performance"},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("mode") == "performance"

        # Reset to balanced
        requests.post(
            f"{base_url}/api/hardware/performance-mode",
            json={"mode": "balanced"},
            timeout=10,
        )
