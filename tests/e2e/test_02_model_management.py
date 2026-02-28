"""
E2E tests: Model management — load, list, warmup, cache, unload.

These tests exercise the full model lifecycle through the real API.
"""

import pytest
import requests

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


class TestModelManagement:
    """Model lifecycle via /api/models endpoints."""

    def test_load_model(self, e2e_server, base_url, loaded_model):
        """Model loads successfully via POST /api/models/load."""
        # loaded_model fixture already asserts successful load
        assert loaded_model is not None

    def test_v1_models_openai_format(self, e2e_server, base_url, auth_headers, loaded_model):
        """GET /v1/models returns OpenAI-compatible format."""
        r = requests.get(f"{base_url}/v1/models", headers=auth_headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("object") == "list"
        assert isinstance(data.get("data"), list)
        assert len(data["data"]) >= 1
        model_entry = data["data"][0]
        assert "id" in model_entry
        assert model_entry.get("object") == "model"

    def test_model_list_shows_loaded(self, e2e_server, base_url, loaded_model):
        """GET /api/models/list shows the loaded model."""
        r = requests.get(f"{base_url}/api/models/list", timeout=10)
        assert r.status_code == 200
        models = r.json().get("models", [])
        loaded_ids = [m["id"] for m in models if m.get("loaded")]
        assert loaded_model in loaded_ids

    def test_warmup_model(self, e2e_server, base_url, loaded_model):
        """POST /api/models/warmup/{id} warms the model."""
        r = requests.post(
            f"{base_url}/api/models/warmup/{loaded_model}",
            json={"async": False, "num_prompts": 1},
            timeout=60,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") in ("warmed", "warming")

    def test_warmup_status(self, e2e_server, base_url, loaded_model):
        """GET /api/models/warmup/status lists warmup info."""
        r = requests.get(f"{base_url}/api/models/warmup/status", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "warmup_status" in data
        assert "total_models" in data

    def test_cache_status(self, e2e_server, base_url, loaded_model):
        """GET /api/models/cache/status returns cache stats."""
        r = requests.get(f"{base_url}/api/models/cache/status", timeout=10)
        assert r.status_code == 200
        data = r.json()
        # Should have some stats keys
        assert isinstance(data, dict)

    def test_cache_settings_get(self, e2e_server, base_url, loaded_model):
        """GET /api/models/cache/settings returns current settings."""
        r = requests.get(f"{base_url}/api/models/cache/settings", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "enabled" in data
        assert "max_conversations" in data

    def test_cache_clear(self, e2e_server, base_url, loaded_model):
        """POST /api/models/cache/clear succeeds."""
        r = requests.post(
            f"{base_url}/api/models/cache/clear",
            json={},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "success"

    def test_load_duplicate_model(self, e2e_server, base_url, loaded_model):
        """POST /api/models/load with already-loaded model returns already_loaded."""
        r = requests.post(
            f"{base_url}/api/models/load",
            json={"model_id": loaded_model},
            timeout=30,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") in ("already_loaded", "success")
