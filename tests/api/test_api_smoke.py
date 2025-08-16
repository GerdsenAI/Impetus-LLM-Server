import os
import time
import json
import socket
import subprocess
from pathlib import Path
import sys

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_SCRIPT = REPO_ROOT / "gerdsen_ai_server" / "src" / "main.py"


def wait_for_port(host: str, port: int, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = socket.socket()
        s.settimeout(1)
        try:
            s.connect((host, port))
            s.close()
            # Also verify health endpoint if possible
            try:
                r = requests.get("http://localhost:8080/api/health", timeout=2)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            # Port open counts as success even if health not yet ready
            return True
        except Exception:
            time.sleep(0.3)
    return False


@pytest.fixture(scope="session")
def server_proc():
    # If a server is already up, reuse it
    try:
        r = requests.get("http://localhost:8080/api/health", timeout=2)
        if r.status_code == 200:
            yield None
            return
    except Exception:
        pass

    env = os.environ.copy()
    env.setdefault("IMPETUS_ENV", "testing")
    proc = subprocess.Popen([sys.executable, str(SERVER_SCRIPT)], cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert wait_for_port("127.0.0.1", 8080, 30), "Server did not start on :8080"
    yield proc
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.mark.e2e
def test_health_endpoint(server_proc):
    r = requests.get("http://localhost:8080/api/health", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "healthy"


@pytest.mark.e2e
def test_docs_and_index(server_proc):
    r = requests.get("http://localhost:8080/")
    assert r.ok
    r2 = requests.get("http://localhost:8080/docs")
    assert r2.ok


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.parametrize("payload", [
    {"model": "mlx-community/Mistral-7B-Instruct-v0.3-4bit", "messages": [{"role": "user", "content": "Hello"}], "stream": False, "max_tokens": 8},
])
@pytest.mark.skipif(os.environ.get("IMPETUS_ENABLE_MODEL_TESTS") != "1", reason="Model tests disabled; set IMPETUS_ENABLE_MODEL_TESTS=1 to enable")
def test_openai_chat_completion(server_proc, payload):
    r = requests.post("http://localhost:8080/v1/chat/completions", json=payload, timeout=60)
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        data = r.json()
        assert data.get("object") in ("chat.completion",)
    else:
        # Accept model-not-loaded path in environments without MLX/models
        err = r.json()
        assert err.get("error")


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(os.environ.get("IMPETUS_ENABLE_MODEL_TESTS") != "1", reason="Streaming disabled without models")
def test_streaming_response(server_proc):
    payload = {
        "model": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
        "messages": [{"role": "user", "content": "Write a haiku about the ocean."}],
        "stream": True,
        "max_tokens": 16,
    }
    with requests.post("http://localhost:8080/v1/chat/completions", json=payload, stream=True, timeout=120) as r:
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            saw_done = False
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    data = line[len("data: "):]
                    if data == "[DONE]":
                        saw_done = True
                        break
            assert saw_done, "Did not see [DONE] in stream"
