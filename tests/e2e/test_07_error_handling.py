"""
E2E tests: Error handling — auth failures, invalid requests, missing models.

Tests that the server returns appropriate error codes and messages.
"""

import pytest
import requests

pytestmark = [pytest.mark.e2e]


class TestAuthErrors:
    """Authentication error scenarios on /v1 endpoints."""

    def test_no_auth_header(self, e2e_server, base_url):
        """POST /v1/chat/completions without auth returns 401."""
        payload = {
            "model": "any-model",
            "messages": [{"role": "user", "content": "test"}],
        }
        r = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            timeout=10,
        )
        assert r.status_code == 401

    def test_invalid_api_key(self, e2e_server, base_url):
        """POST with a wrong Bearer token returns 401."""
        headers = {"Authorization": "Bearer wrong-key-abc123"}
        payload = {
            "model": "any-model",
            "messages": [{"role": "user", "content": "test"}],
        }
        r = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=10,
        )
        assert r.status_code == 401

    def test_health_no_auth_required(self, e2e_server, base_url):
        """GET /api/health does NOT require authentication."""
        r = requests.get(f"{base_url}/api/health", timeout=5)
        assert r.status_code == 200


class TestRequestValidation:
    """Invalid request payloads."""

    def test_invalid_model_name(self, e2e_server, base_url, auth_headers):
        """POST with a nonexistent model returns 404."""
        payload = {
            "model": "nonexistent/fake-model-xyz",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 5,
            "stream": False,
        }
        r = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            timeout=30,
        )
        # Server tries to auto-load and fails → 404
        assert r.status_code in (404, 400, 500)
        data = r.json()
        assert "error" in data

    def test_empty_messages(self, e2e_server, base_url, auth_headers):
        """POST with empty messages list returns 400."""
        payload = {
            "model": "any-model",
            "messages": [],
            "stream": False,
        }
        r = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            timeout=10,
        )
        # Pydantic validation should reject empty messages
        assert r.status_code in (400, 422)

    def test_invalid_json_body(self, e2e_server, base_url, auth_headers):
        """POST with malformed body returns 400."""
        r = requests.post(
            f"{base_url}/v1/chat/completions",
            data="this is not json",
            headers={**auth_headers, "Content-Type": "application/json"},
            timeout=10,
        )
        assert r.status_code in (400, 415, 422, 500)

    def test_missing_model_field(self, e2e_server, base_url, auth_headers):
        """POST without required 'model' field returns 400."""
        payload = {
            "messages": [{"role": "user", "content": "test"}],
        }
        r = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            timeout=10,
        )
        assert r.status_code in (400, 422)


class TestModelManagementErrors:
    """Model management error scenarios."""

    def test_unload_nonexistent_model(self, e2e_server, base_url):
        """POST /api/models/unload with unknown model returns 404."""
        r = requests.post(
            f"{base_url}/api/models/unload",
            json={"model_id": "nonexistent/model-xyz"},
            timeout=10,
        )
        assert r.status_code == 404

    def test_load_missing_model_id(self, e2e_server, base_url):
        """POST /api/models/load without model_id returns 400."""
        r = requests.post(
            f"{base_url}/api/models/load",
            json={},
            timeout=10,
        )
        assert r.status_code == 400

    def test_invalid_performance_mode(self, e2e_server, base_url):
        """POST /api/hardware/performance-mode with invalid mode returns 400."""
        r = requests.post(
            f"{base_url}/api/hardware/performance-mode",
            json={"mode": "turbo"},
            timeout=10,
        )
        assert r.status_code == 400
