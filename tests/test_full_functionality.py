"""
Automated end-to-end script inspired by the user's regimen. Safe-by-default (no model load).
Enable model tests by export IMPETUS_ENABLE_MODEL_TESTS=1 before running.
"""

import os
import time
import subprocess
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_server_health_quick():
    # Try to hit an already-running server first
    try:
        r = requests.get("http://localhost:8080/api/health", timeout=2)
        if r.status_code == 200:
            return
    except Exception:
        pass

    # Start a local server if not running
    proc = subprocess.Popen(["python3", str(REPO_ROOT / "gerdsen_ai_server" / "src" / "main.py")], cwd=str(REPO_ROOT))
    try:
        # Wait for server
        for _ in range(50):
            try:
                r = requests.get("http://localhost:8080/api/health", timeout=1)
                if r.status_code == 200:
                    break
            except Exception:
                time.sleep(0.2)
        else:
            raise AssertionError("Server did not become healthy")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    test_server_health_quick()
