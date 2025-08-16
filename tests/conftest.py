import os
import platform
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def artifacts_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("artifacts")
    return d


def requires_macos():
    return platform.system() == "Darwin"


def pytest_configure(config):
    config.addinivalue_line("markers", "gui: macOS GUI tests via AppleScript")
    config.addinivalue_line("markers", "e2e: end-to-end tests requiring server")
    config.addinivalue_line("markers", "slow: long-running tests")
