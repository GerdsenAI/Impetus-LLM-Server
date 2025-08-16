# Impetus-LLM-Server Test Suite

This folder contains automated tests for the macOS menu bar app, server APIs, dashboard, and advanced behaviors.

Requirements:
- macOS with Accessibility permissions enabled for Terminal and VS Code (for AppleScript GUI tests)
- Python 3.11+ (repo uses 3.13 locally) and pip
- Node.js (for dashboard tests if enabled)

Markers:
- gui: macOS GUI tests via AppleScript (require user session)
- e2e: end-to-end tests hitting the running server
- perf: performance measurements
- slow: long-running/model-loading

Running:
- Quick API smoke tests: `pytest -m "not gui and not slow"`
- Include GUI: `pytest -m gui`
- Full suite: `pytest -m "e2e or gui"`

Notes:
- GUI tests use AppleScript under `gui/` called from Python. They will prompt for Accessibility on first run.
- Server tests start the Flask app in a subprocess and wait for `/api/health`.
