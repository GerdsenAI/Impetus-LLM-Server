#!/usr/bin/env python3
"""
Impetus Tray App - Lightweight system tray application for Impetus LLM Server

This module implements a headless tray/menubar application that provides:
1. Server start/stop controls
2. Status indicator in the system tray
3. Quick access to open the web UI in a browser
4. Basic server monitoring

The tray app replaces the previous Electron GUI with a more lightweight solution,
moving all configuration and management to the web-based UI.
"""

import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
import tempfile
import fcntl
import atexit
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

# Server configuration
DEFAULT_PORT = 8080
DEFAULT_HOST = "localhost"
WEB_UI_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"

# Status constants
STATUS_STOPPED = "stopped"
STATUS_RUNNING = "running"
STATUS_ERROR = "error"


class ImpetusServerMonitor:
    """Monitors the Impetus LLM server process and status."""
    
    def __init__(self, server_script_path=None):
        """Initialize the server monitor.
        
        Args:
            server_script_path: Path to the server script. If None, will use default.
        """
        self.server_process = None
        self.status = STATUS_STOPPED
        self.error_message = None
        
        # Determine server script path
        if server_script_path is None:
            # Get the project root directory
            current_dir = Path(__file__).parent.resolve()
            project_root = current_dir.parent
            self.server_script_path = project_root / "gerdsen_ai_server" / "src" / "production_main.py"
        else:
            self.server_script_path = Path(server_script_path)
            
        # Ensure the server script exists
        if not self.server_script_path.exists():
            self.status = STATUS_ERROR
            self.error_message = f"Server script not found: {self.server_script_path}"
    
    def start_server(self):
        """Start the Impetus LLM server."""
        if self.status == STATUS_RUNNING:
            return True
            
        try:
            # Start the server as a subprocess
            self.server_process = subprocess.Popen(
                [sys.executable, str(self.server_script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment for the server to start
            time.sleep(2)
            
            # Check if the process is still running
            if self.server_process.poll() is None:
                self.status = STATUS_RUNNING
                
                # Start a thread to monitor the server output
                threading.Thread(
                    target=self._monitor_server_output,
                    daemon=True
                ).start()
                
                return True
            else:
                # Process exited immediately, likely an error
                stdout, stderr = self.server_process.communicate()
                self.error_message = stderr or stdout
                self.status = STATUS_ERROR
                return False
                
        except Exception as e:
            self.status = STATUS_ERROR
            self.error_message = str(e)
            return False
    
    def stop_server(self):
        """Stop the Impetus LLM server."""
        if self.server_process and self.status == STATUS_RUNNING:
            try:
                # Try to terminate gracefully first
                self.server_process.terminate()
                
                # Wait for process to terminate
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    self.server_process.kill()
                
                self.status = STATUS_STOPPED
                self.server_process = None
                return True
            except Exception as e:
                self.status = STATUS_ERROR
                self.error_message = f"Error stopping server: {str(e)}"
                return False
        return True
    
    def check_server_status(self):
        """Check if the server is running."""
        if self.server_process:
            # Check if process is still running
            if self.server_process.poll() is None:
                self.status = STATUS_RUNNING
            else:
                self.status = STATUS_STOPPED
                self.server_process = None
        return self.status
    
    def _monitor_server_output(self):
        """Monitor the server output for errors."""
        while self.server_process and self.server_process.poll() is None:
            # Read output line by line
            for line in iter(self.server_process.stderr.readline, ''):
                if "error" in line.lower() or "exception" in line.lower():
                    print(f"Server error: {line.strip()}")
                    # Don't set error status for non-fatal errors
            
            # Check if process has exited
            if self.server_process.poll() is not None:
                stdout, stderr = self.server_process.communicate()
                if stderr:
                    self.error_message = stderr
                    self.status = STATUS_ERROR
                break
                
            time.sleep(1)


class ImpetusTrayApp:
    """Impetus system tray application."""
    
    def __init__(self):
        """Initialize the tray application."""
        self.server_monitor = ImpetusServerMonitor()
        self.icon = None
        self.status_thread = None
        self.running = False
    
    def create_image(self):
        """Create the tray icon image based on server status."""
        # Create a simple colored circle icon
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw different colored circles based on status
        status = self.server_monitor.check_server_status()
        if status == STATUS_RUNNING:
            # Green circle for running
            color = (0, 255, 0)
        elif status == STATUS_ERROR:
            # Red circle for error
            color = (255, 0, 0)
        else:
            # Gray circle for stopped
            color = (128, 128, 128)
            
        # Draw the circle
        dc.ellipse((4, 4, width-4, height-4), fill=color)
        
        return image
    
    def update_icon(self):
        """Update the tray icon to reflect current status."""
        if self.icon:
            self.icon.icon = self.create_image()
    
    def start_server_action(self):
        """Start the server from the tray menu."""
        success = self.server_monitor.start_server()
        self.update_icon()
        
        if not success and self.server_monitor.error_message:
            # In a real app, we would show a notification here
            print(f"Error starting server: {self.server_monitor.error_message}")
    
    def stop_server_action(self):
        """Stop the server from the tray menu."""
        self.server_monitor.stop_server()
        self.update_icon()
    
    def open_web_ui_action(self):
        """Open the web UI in the default browser."""
        # Check if server is running first
        if self.server_monitor.check_server_status() != STATUS_RUNNING:
            # Try to start the server first
            success = self.server_monitor.start_server()
            if not success:
                print("Cannot open web UI: Server failed to start")
                return
                
        # Open the web UI in the default browser
        webbrowser.open(WEB_UI_URL)
    
    def exit_action(self):
        """Exit the tray application."""
        # Stop the server if it's running
        self.server_monitor.stop_server()
        
        # Stop the status update thread
        self.running = False
        if self.status_thread:
            self.status_thread.join(timeout=1)
            
        # Stop the tray icon
        self.icon.stop()
    
    def status_update_loop(self):
        """Background thread to update the tray icon status."""
        while self.running:
            self.update_icon()
            time.sleep(2)
    
    def run(self):
        """Run the tray application."""
        # Create the menu
        menu = pystray.Menu(
            pystray.MenuItem("Start Server", self.start_server_action),
            pystray.MenuItem("Stop Server", self.stop_server_action),
            pystray.MenuItem("Open Web UI", self.open_web_ui_action),
            pystray.MenuItem("Exit", self.exit_action)
        )
        
        # Create the icon
        self.icon = pystray.Icon(
            "impetus",
            self.create_image(),
            "Impetus LLM Server",
            menu
        )
        
        # Start the status update thread
        self.running = True
        self.status_thread = threading.Thread(
            target=self.status_update_loop,
            daemon=True
        )
        self.status_thread.start()
        
        # Run the tray icon
        self.icon.run()


def is_already_running():
    """Check if another instance of the application is already running.
    
    Returns:
        bool: True if another instance is running, False otherwise.
    """
    lock_file = os.path.join(tempfile.gettempdir(), 'impetus_tray_app.lock')
    
    try:
        # Try to create and lock the file
        global lock_fd
        lock_fd = open(lock_file, 'w')
        fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        # If we got here, no other instance is running
        # Write PID to the lock file
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
        
        # Register cleanup function
        atexit.register(cleanup_lock)
        
        return False
    except IOError:
        # Another instance has the lock
        return True


def cleanup_lock():
    """Clean up the lock file when the application exits."""
    try:
        if 'lock_fd' in globals():
            fcntl.lockf(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
    except Exception:
        pass


def main():
    """Main entry point for the tray application."""
    # Check if another instance is already running
    if is_already_running():
        print("Another instance of Impetus Tray App is already running.")
        # If running from GUI, show a notification
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("Impetus", "Impetus is already running in the menu bar.")
            root.destroy()
        except Exception:
            pass
        sys.exit(0)
    
    # No other instance is running, start the app
    app = ImpetusTrayApp()
    app.run()


if __name__ == "__main__":
    main()
