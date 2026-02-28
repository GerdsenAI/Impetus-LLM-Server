"""
E2E tests: Server lifecycle — health, readiness, metrics, docs.

These tests verify the server starts and responds correctly to
health probes, Prometheus metrics, and API docs without needing
any model loaded.
"""

import pytest
import requests

pytestmark = [pytest.mark.e2e]


class TestServerLifecycle:
    """Server health and observability endpoints."""

    def test_server_index(self, e2e_server, base_url):
        """GET / returns server info."""
        r = requests.get(f"{base_url}/", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "name" in data or "version" in data or "uptime" in data

    def test_liveness_probe(self, e2e_server, base_url):
        """GET /api/health/live returns alive: true."""
        r = requests.get(f"{base_url}/api/health/live", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data.get("alive") is True

    def test_readiness_probe(self, e2e_server, base_url):
        """GET /api/health/ready returns a ready field."""
        r = requests.get(f"{base_url}/api/health/ready", timeout=5)
        # May be 200 or 503 depending on whether a model is loaded
        assert r.status_code in (200, 503)
        data = r.json()
        assert "ready" in data

    def test_health_check(self, e2e_server, base_url):
        """GET /api/health returns status: healthy."""
        r = requests.get(f"{base_url}/api/health", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "healthy"

    def test_detailed_status(self, e2e_server, base_url):
        """GET /api/health/status returns system and MLX info."""
        r = requests.get(f"{base_url}/api/health/status", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert "system" in data

    def test_prometheus_metrics(self, e2e_server, base_url):
        """GET /api/metrics returns Prometheus-format text."""
        r = requests.get(f"{base_url}/api/metrics", timeout=5)
        assert r.status_code == 200
        assert "text/plain" in r.headers.get("Content-Type", "")
        assert "impetus_" in r.text

    def test_json_metrics(self, e2e_server, base_url):
        """GET /api/metrics/json returns structured JSON metrics."""
        r = requests.get(f"{base_url}/api/metrics/json", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "cpu_usage_percent" in data or "total_requests" in data

    def test_api_docs(self, e2e_server, base_url):
        """GET /docs returns HTML documentation."""
        r = requests.get(f"{base_url}/docs", timeout=5)
        assert r.status_code == 200
        assert "html" in r.headers.get("Content-Type", "").lower() or "<" in r.text
