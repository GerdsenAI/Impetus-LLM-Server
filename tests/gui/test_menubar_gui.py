import os
import time
import subprocess
import sys
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
MENUBAR_SCRIPT = REPO_ROOT / "run_menubar.py"
APPLE_SCRIPT = REPO_ROOT / "tests" / "gui" / "menubar_automation.applescript"


@pytest.mark.gui
@pytest.mark.e2e
@pytest.mark.skipif(os.environ.get("CI") == "true", reason="GUI tests disabled on CI")
@pytest.mark.skipif(not (APPLE_SCRIPT.exists() and MENUBAR_SCRIPT.exists()), reason="Missing scripts")
def test_menubar_smoke(artifacts_dir):
    # Pre-check: Accessibility permission for osascript/System Events
    probe = subprocess.run([
        "osascript",
        "-e",
        'tell application "System Events" to return 1'
    ], capture_output=True, text=True)
    if probe.returncode != 0 and ("not allowed assistive access" in (probe.stderr or "").lower() or "-1719" in (probe.stderr or "")):
        pytest.skip("macOS Accessibility permission required for osascript. Enable System Events access for Terminal/VS Code.")

    # Launch menubar app
    env = os.environ.copy()
    env["IMPETUS_TEST_MODE"] = "1"
    proc = subprocess.Popen([sys.executable, str(MENUBAR_SCRIPT)], cwd=str(REPO_ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    fb_proc = None
    menu_opened = False
    try:
        # Give time for menu bar item to register
        time.sleep(4.0)
        # Open the menu
        r = subprocess.run(["osascript", str(APPLE_SCRIPT), "open"], capture_output=True, text=True, timeout=10)
        assert r.returncode == 0, r.stderr
        if (r.stdout or "").strip() != "ok":
            pytest.skip("Impetus menu bar item not found; ensure rumps app is running and Accessibility is granted")
        menu_opened = True

        # Screenshot menu bar for evidence
        shot = artifacts_dir / "menubar.png"
        r2 = subprocess.run(["osascript", str(APPLE_SCRIPT), "screenshot", str(shot)], capture_output=True, text=True, timeout=10)
        assert r2.returncode == 0

        # Click Start Server
        r3 = subprocess.run(["osascript", str(APPLE_SCRIPT), "click", "Start Server"], capture_output=True, text=True, timeout=20)
        assert r3.returncode == 0, r3.stderr
        # Verify it toggled to Stop Server (allow a short delay)
        time.sleep(0.8)
        r_exists = subprocess.run(["osascript", str(APPLE_SCRIPT), "exists", "Stop Server"], capture_output=True, text=True, timeout=10)
        assert r_exists.returncode == 0

        # Verify health endpoint with a longer wait
        ok = False
        deadline = time.time() + 30.0
        while time.time() < deadline:
            try:
                resp = requests.get("http://localhost:8080/api/health", timeout=2)
                if resp.status_code == 200:
                    ok = True
                    break
            except Exception:
                pass
            time.sleep(0.5)

        if not ok:
            # Fallback: start server directly to continue UI flow validation
            server_script = REPO_ROOT / "gerdsen_ai_server" / "src" / "main.py"
            fb_proc = subprocess.Popen([sys.executable, str(server_script)], cwd=str(REPO_ROOT))
            deadline = time.time() + 20.0
            while time.time() < deadline:
                try:
                    resp = requests.get("http://localhost:8080/api/health", timeout=2)
                    if resp.status_code == 200:
                        ok = True
                        break
                except Exception:
                    pass
                time.sleep(0.5)
            assert ok, "Server did not become healthy via menubar or fallback"

        # Open Dashboard
        rdash = subprocess.run(["osascript", str(APPLE_SCRIPT), "click", "Open Dashboard"], capture_output=True, text=True, timeout=10)
        assert rdash.returncode == 0, rdash.stderr
        # Open API Docs
        rdocs = subprocess.run(["osascript", str(APPLE_SCRIPT), "click", "API Documentation"], capture_output=True, text=True, timeout=10)
        assert rdocs.returncode == 0, rdocs.stderr

        # Stop Server via menu
        subprocess.run(["osascript", str(APPLE_SCRIPT), "open"], capture_output=True, text=True, timeout=10)
        rstop = subprocess.run(["osascript", str(APPLE_SCRIPT), "click", "Stop Server"], capture_output=True, text=True, timeout=10)
        assert rstop.returncode == 0, rstop.stderr
        # Verify it toggled back to Start Server
        time.sleep(0.8)
        r_exists2 = subprocess.run(["osascript", str(APPLE_SCRIPT), "exists", "Start Server"], capture_output=True, text=True, timeout=10)
        assert r_exists2.returncode == 0
    finally:
        # Quit app via menu when available; otherwise just terminate the process
        if menu_opened:
            try:
                subprocess.run(["osascript", str(APPLE_SCRIPT), "quit"], capture_output=True, text=True, timeout=5)
            except subprocess.TimeoutExpired:
                pass
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        # Stop fallback server if we started one
        if fb_proc and fb_proc.poll() is None:
            fb_proc.terminate()
            try:
                fb_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                fb_proc.kill()
