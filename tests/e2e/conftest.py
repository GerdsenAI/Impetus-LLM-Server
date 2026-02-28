"""
E2E test fixtures — real server subprocess, auth, model loading.

All E2E tests start a real Impetus server process and exercise the
full HTTP stack with real MLX inference on Apple Silicon.
"""

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_SCRIPT = REPO_ROOT / "gerdsen_ai_server" / "src" / "main.py"

# ---------------------------------------------------------------------------
# Test configuration (overridable via env vars)
# ---------------------------------------------------------------------------

E2E_API_KEY = os.environ.get("IMPETUS_E2E_API_KEY", "test-e2e-key-12345")
E2E_MODEL = os.environ.get(
    "IMPETUS_E2E_MODEL", "mlx-community/SmolLM2-135M-Instruct-4bit"
)
E2E_EMBEDDING_MODEL = os.environ.get(
    "IMPETUS_E2E_EMBEDDING_MODEL", "all-MiniLM-L6-v2"
)
E2E_PORT = int(os.environ.get("IMPETUS_E2E_PORT", "8080"))
E2E_TIMEOUT = int(os.environ.get("IMPETUS_E2E_TIMEOUT", "120"))
BASE_URL = f"http://127.0.0.1:{E2E_PORT}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def wait_for_server(host: str, port: int, timeout: float = 30.0) -> bool:
    """Block until the server is accepting connections and /api/health returns 200."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        sock = socket.socket()
        sock.settimeout(1)
        try:
            sock.connect((host, port))
            sock.close()
            # Verify health endpoint
            try:
                r = requests.get(f"http://{host}:{port}/api/health", timeout=2)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            # Port is open even if health not ready yet — keep waiting
        except Exception:
            pass
        time.sleep(0.5)
    return False


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def e2e_server(tmp_path_factory):
    """Start the Impetus server as a subprocess, or reuse a running one."""
    # Check for an already-running server (handy for local dev)
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if r.status_code == 200:
            yield None  # reuse existing server
            return
    except Exception:
        pass

    # Build isolated environment for the server
    vectorstore_dir = tmp_path_factory.mktemp("vectorstore")
    env = os.environ.copy()
    env.update(
        {
            "IMPETUS_API_KEY": E2E_API_KEY,
            "IMPETUS_ENV": "testing",
            "IMPETUS_DEFAULT_MODEL": E2E_MODEL,
            "IMPETUS_VECTORSTORE_DIR": str(vectorstore_dir),
            "IMPETUS_PORT": str(E2E_PORT),
            "IMPETUS_LOG_LEVEL": "WARNING",
            "IMPETUS_REQUIRE_MODEL_FOR_READY": "false",
        }
    )

    proc = subprocess.Popen(
        [sys.executable, str(SERVER_SCRIPT)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )

    assert wait_for_server("127.0.0.1", E2E_PORT, E2E_TIMEOUT), (
        f"Server did not become healthy on :{E2E_PORT} within {E2E_TIMEOUT}s"
    )

    yield proc

    # Teardown
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def api_key():
    return E2E_API_KEY


@pytest.fixture(scope="session")
def auth_headers(api_key):
    return {"Authorization": f"Bearer {api_key}"}


@pytest.fixture(scope="session")
def loaded_model(e2e_server, base_url, auth_headers):
    """Load the small test model once and verify it's available."""
    model_id = E2E_MODEL

    # Try loading
    r = requests.post(
        f"{base_url}/api/models/load",
        json={"model_id": model_id},
        timeout=E2E_TIMEOUT,
    )
    # Accept both success and already_loaded
    assert r.status_code == 200, f"Failed to load model: {r.text}"
    data = r.json()
    assert data.get("status") in ("success", "already_loaded"), (
        f"Unexpected load status: {data}"
    )

    # Verify via models list
    r = requests.get(f"{base_url}/api/models/list", timeout=10)
    assert r.status_code == 200
    models = r.json().get("models", [])
    assert any(m["id"] == model_id and m["loaded"] for m in models), (
        f"Model {model_id} not found in loaded models list"
    )

    yield model_id

    # Teardown: unload
    requests.post(
        f"{base_url}/api/models/unload",
        json={"model_id": model_id},
        timeout=30,
    )


# ---------------------------------------------------------------------------
# Function-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def http_client():
    """Fresh requests.Session per test for isolation."""
    with requests.Session() as s:
        yield s


# ---------------------------------------------------------------------------
# Module-scoped fixtures for RAG tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_collection_name():
    """Unique collection name for RAG tests."""
    return "e2e_test_collection"


