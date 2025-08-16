import os
import time
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
APPLE_SCRIPT = REPO_ROOT / "tests" / "gui" / "menubar_automation.applescript"
MENUBAR_SCRIPT = REPO_ROOT / "run_menubar.py"


@pytest.mark.gui
@pytest.mark.skipif(os.environ.get("CI") == "true", reason="GUI tests disabled on CI")
@pytest.mark.skipif(not (APPLE_SCRIPT.exists() and MENUBAR_SCRIPT.exists()), reason="Missing scripts")
def test_switch_performance_modes():
    # Pre-check: Accessibility permission for osascript/System Events
    probe = subprocess.run([
        "osascript",
        "-e",
        'tell application "System Events" to return 1'
    ], capture_output=True, text=True)
    if probe.returncode != 0 and ("not allowed assistive access" in (probe.stderr or "").lower() or "-1719" in (probe.stderr or "")):
        pytest.skip("macOS Accessibility permission required for osascript. Enable System Events access for Terminal/VS Code.")

    env = os.environ.copy()
    env["IMPETUS_TEST_MODE"] = "1"
    proc = subprocess.Popen([sys.executable, str(MENUBAR_SCRIPT)], cwd=str(REPO_ROOT), env=env)
    try:
        time.sleep(2.0)
        # Open menu and navigate: Performance Mode -> Efficiency Mode
        subprocess.run(["osascript", str(APPLE_SCRIPT), "nestedclick", "Performance Mode", "Efficiency Mode"], timeout=10)
        time.sleep(0.5)
        # Switch to Balanced Mode
        subprocess.run(["osascript", str(APPLE_SCRIPT), "nestedclick", "Performance Mode", "Balanced Mode"], timeout=10)
        time.sleep(0.5)
        # Switch to Performance Mode
        subprocess.run(["osascript", str(APPLE_SCRIPT), "nestedclick", "Performance Mode", "Performance Mode"], timeout=10)
    finally:
        subprocess.run(["osascript", str(APPLE_SCRIPT), "quit"], timeout=10)
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
