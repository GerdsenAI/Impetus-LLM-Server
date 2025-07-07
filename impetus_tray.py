#!/usr/bin/env python3
"""
Impetus Tray App Launcher

This script serves as the main entry point for launching the Impetus tray application.
It provides a lightweight system tray icon with controls for managing the Impetus LLM server.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
current_dir = Path(__file__).parent.resolve()
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Import the tray app module
from tray_app import main

if __name__ == "__main__":
    # Launch the tray application
    main()
