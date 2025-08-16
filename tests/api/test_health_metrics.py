import os
import time
import socket
import subprocess
from pathlib import Path
import sys

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_SCRIPT = REPO_ROOT / "gerdsen_ai_server" / "src" / "main.py"


def _wait_for_port(host: str, port: int, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = socket.socket()
        s.settimeout(1)
        try:
            s.connect((host, port))
            s.close()
            return True
        except Exception:
            time.sleep(0.2)
    return False


@pytest.fixture(scope="module")
def server_proc():
    # Reuse running server if available
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
    assert _wait_for_port("127.0.0.1", 8080, 30), "Server did not start"
    yield proc
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.mark.e2e
def test_status_and_metrics(server_proc):
    r = requests.get("http://localhost:8080/api/status", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") in {"healthy", "degraded"}

    r2 = requests.get("http://localhost:8080/api/metrics", timeout=5)
    assert r2.ok
    assert "impetus_uptime_seconds" in r2.text

    r3 = requests.get("http://localhost:8080/api/metrics/json", timeout=5)
    assert r3.ok
    j = r3.json()
    assert "cpu_usage_percent" in j
