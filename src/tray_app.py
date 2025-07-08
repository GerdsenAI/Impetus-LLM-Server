#!/usr/bin/env python3
"""
Impetus Tray App - Lightweight system tray application for Impetus LLM Server

This module implements a headless tray/menubar application that provides:
1. Server start/stop controls
2. Status indicator in the system tray
3. Quick access to open the web UI in a browser
4. Basic server monitoring
5. Auto-start on login capability

The tray app replaces the previous Electron GUI with a more lightweight solution,
moving all configuration and management to the web-based UI.

Version: 2.0.0
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
import logging
import json
import socket
import platform
import shutil
import requests
from datetime import datetime
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

# Configure logging
log_dir = os.path.join(os.path.expanduser("~"), ".impetus", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"impetus_tray_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('impetus_tray')

# Server configuration
DEFAULT_PORT = 8080
DEFAULT_HOST = "localhost"
DEFAULT_WEB_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"

# Status constants
STATUS_STOPPED = "stopped"
STATUS_RUNNING = "running"
STATUS_ERROR = "error"


class ImpetusServerMonitor:
    """Monitors the Impetus LLM server process and status."""
    
    def __init__(self, server_script_path=None, port=DEFAULT_PORT, host=DEFAULT_HOST, max_restart_attempts=3):
        """Initialize the server monitor.
        
        Args:
            server_script_path: Path to the server script. If None, will use default.
            port: Port number the server will run on.
            host: Host address the server will bind to.
            max_restart_attempts: Maximum number of automatic restart attempts after failure.
        """
        self.server_process = None
        self.status = STATUS_STOPPED
        self.error_message = None
        self.port = port
        self.host = host
        self.max_restart_attempts = max_restart_attempts
        self.restart_attempts = 0
        self.health_check_url = f"http://{host}:{port}/health"
        self.auto_recovery = True
        self.last_restart_time = None
        
        # Determine server script path
        if server_script_path is None:
            # Get the project root directory
            current_dir = Path(__file__).parent.resolve()
            project_root = current_dir.parent
            self.server_script_path = project_root / "gerdsen_ai_server" / "src" / "production_main.py"
            
            # In deployed app, the path might be different
            if not self.server_script_path.exists() and getattr(sys, 'frozen', False):
                # Look in relative paths for bundled apps
                bundle_dir = Path(sys._MEIPASS) if getattr(sys, '_MEIPASS', False) else Path(os.path.dirname(sys.executable))
                possible_paths = [
                    bundle_dir / "gerdsen_ai_server" / "src" / "production_main.py",
                    bundle_dir / "src" / "production_main.py",
                    bundle_dir / "production_main.py",
                    bundle_dir.parent / "Resources" / "gerdsen_ai_server" / "src" / "production_main.py"
                ]
                
                for path in possible_paths:
                    if path.exists():
                        self.server_script_path = path
                        break
        else:
            self.server_script_path = Path(server_script_path)
        
        logger.info(f"Server script path: {self.server_script_path}")
            
        # Ensure the server script exists
        if not self.server_script_path.exists():
            self.status = STATUS_ERROR
            self.error_message = f"Server script not found: {self.server_script_path}"
            logger.error(f"Server script not found: {self.server_script_path}")
    
    def is_port_in_use(self):
        """Check if the server port is already in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self.host, self.port))
                return False
            except socket.error:
                return True
    
    def check_health(self):
        """Check if the server is healthy by making a request to the health endpoint."""
        try:
            response = requests.get(self.health_check_url, timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False
            
    def kill_process_on_port(self):
        """Attempt to kill any process using the server port."""
        try:
            if platform.system() == "Darwin":  # macOS
                cmd = ["lsof", "-i", f":{self.port}", "-t"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.stdout:
                    pid = int(result.stdout.strip())
                    logger.info(f"Killing process {pid} using port {self.port}")
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(1)  # Give it a moment to terminate
                    return True
            elif platform.system() == "Windows":  # Windows
                cmd = ["netstat", "-ano", "|findstr", f":{self.port}"]
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'LISTENING' in line:
                            pid = int(line.strip().split()[-1])
                            logger.info(f"Killing process {pid} using port {self.port}")
                            os.kill(pid, signal.SIGTERM)
                            time.sleep(1)  # Give it a moment to terminate
                            return True
            return False
        except Exception as e:
            logger.error(f"Error killing process on port {self.port}: {e}")
            return False
    
    def start_server(self):
        """Start the Impetus LLM server."""
        if self.status == STATUS_RUNNING and self.check_health():
            logger.info("Server is already running and healthy")
            return True
        
        # If the server is marked as running but health check fails,
        # update the status to reflect reality
        if self.status == STATUS_RUNNING and not self.check_health():
            logger.warning("Server marked as running but health check failed")
            self.status = STATUS_ERROR
            
        # Check if port is already in use
        if self.is_port_in_use():
            logger.warning(f"Port {self.port} is already in use")
            # Try to kill the process using the port
            if self.kill_process_on_port():
                logger.info("Successfully killed process using the port")
            else:
                self.status = STATUS_ERROR
                self.error_message = f"Port {self.port} is already in use and could not be freed"
                logger.error(self.error_message)
                return False
            
        try:
            # Clear previous error state
            self.error_message = None
            logger.info(f"Starting server from: {self.server_script_path}")
            
            # Set up environment variables for the server
            env = os.environ.copy()
            env["IMPETUS_PORT"] = str(self.port)
            env["IMPETUS_HOST"] = self.host
            env["IMPETUS_LOG_LEVEL"] = "INFO"
            
            # Start the server as a subprocess
            self.server_process = subprocess.Popen(
                [sys.executable, str(self.server_script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            logger.info(f"Server process started with PID: {self.server_process.pid}")
            
            # Wait and check if server starts successfully
            max_wait_time = 15  # seconds
            wait_interval = 1  # seconds
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                # Check if process is still running
                if self.server_process.poll() is not None:
                    # Process exited
                    stdout, stderr = self.server_process.communicate()
                    self.error_message = stderr or stdout
                    self.status = STATUS_ERROR
                    logger.error(f"Server process exited unexpectedly: {self.error_message}")
                    return False
                
                # Check if server is responding
                if self.check_health():
                    self.status = STATUS_RUNNING
                    self.restart_attempts = 0  # Reset restart counter on successful start
                    logger.info("Server started successfully and is healthy")
                    
                    # Start monitoring threads
                    threading.Thread(
                        target=self._monitor_server_output,
                        daemon=True
                    ).start()
                    
                    threading.Thread(
                        target=self._health_check_loop,
                        daemon=True
                    ).start()
                    
                    return True
                
                time.sleep(wait_interval)
                elapsed_time += wait_interval
                
            # Timed out waiting for server to start
            self.status = STATUS_ERROR
            self.error_message = f"Server failed to start within {max_wait_time} seconds"
            logger.error(self.error_message)
            
            # Kill the process since it's not responding
            self._kill_server_process()
            return False
                
        except Exception as e:
            self.status = STATUS_ERROR
            self.error_message = str(e)
            logger.exception("Error starting server")
            return False
    
    def stop_server(self):
        """Stop the Impetus LLM server."""
        if self.status != STATUS_RUNNING or self.server_process is None:
            logger.info("Server is not running, nothing to stop")
            self.status = STATUS_STOPPED
            return True
            
        try:
            logger.info(f"Stopping server process (PID: {self.server_process.pid})")
            
            # Try graceful shutdown first by sending SIGTERM
            self._kill_server_process()
            
            # Update status
            self.status = STATUS_STOPPED
            logger.info("Server stopped successfully")
            return True
            
        except Exception as e:
            self.status = STATUS_ERROR
            self.error_message = str(e)
            logger.exception("Error stopping server")
            return False

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
    """Monitor the server's stdout and stderr output."""
    if not self.server_process:
        return

    while self.server_process and self.server_process.poll() is None:
        # Read output line by line
        for line in iter(self.server_process.stdout.readline, ""):
            if not line:
                break
            # Log server output
            logger.info(f"Server: {line.strip()}")

        for line in iter(self.server_process.stderr.readline, ""):
            if not line:
                break
            # Log error output
            logger.error(f"Server error: {line.strip()}")

        time.sleep(0.1)

    # Process has terminated
    if self.server_process:
        return_code = self.server_process.poll()
        if return_code is not None:
            if return_code != 0:
                self.status = STATUS_ERROR
                self.error_message = f"Server process exited with code {return_code}"
                logger.error(f"Server process exited with code {return_code}")

                # Attempt auto-recovery if enabled
                if self.auto_recovery and self.restart_attempts < self.max_restart_attempts:
                    self._auto_restart()
            else:
                logger.info("Server process exited normally")
                self.status = STATUS_STOPPED

def _health_check_loop(self):
    """Periodically check server health and attempt recovery if needed."""
    check_interval = 15  # seconds

    while True:
        if self.status == STATUS_RUNNING:
            # Only perform health checks if the server is supposed to be running
            if not self.check_health():
                logger.warning("Health check failed for running server")

                # Check if the process is still alive
                if self.server_process and self.server_process.poll() is None:
                    # Process is still running but not responding
                    logger.warning("Server process is running but not responding to health checks")

                    # Attempt recovery if enabled
                    if self.auto_recovery and self.restart_attempts < self.max_restart_attempts:
                        logger.info("Attempting auto-recovery of non-responsive server")
                        self._auto_restart()
                else:
                    # Process has died but status wasn't updated
                    logger.warning("Server process has died unexpectedly")
                    self.status = STATUS_ERROR
                    self.error_message = "Server process terminated unexpectedly"

                    # Attempt recovery if enabled
                    if self.auto_recovery and self.restart_attempts < self.max_restart_attempts:
                        self._auto_restart()

        time.sleep(check_interval)

def _auto_restart(self):
    """Attempt to automatically restart the server after failure."""
    # Increment restart counter
    self.restart_attempts += 1
    logger.info(f"Auto-restart attempt {self.restart_attempts}/{self.max_restart_attempts}")

    # If server process is still running, kill it
    if self.server_process and self.server_process.poll() is None:
        logger.info("Killing non-responsive server process before restart")
        self._kill_server_process(force=True)

    # Record time of restart
    self.last_restart_time = datetime.now()

    # Attempt to restart
    if self.start_server():
        logger.info("Auto-restart successful")
    else:
        logger.error(f"Auto-restart failed: {self.error_message}")

def get_status_info(self):
    """Get detailed status information about the server.

    Returns:
        dict: Status information including uptime, memory usage, etc.
    """
    info = {
        "status": self.status,
        "error": self.error_message,
        "port": self.port,
        "host": self.host,
        "restart_attempts": self.restart_attempts,
        "auto_recovery": self.auto_recovery
    }

    # Add process information if available
    if self.server_process and self.server_process.poll() is None:
        info["pid"] = self.server_process.pid

        # Get uptime if last_restart_time is available
        if self.last_restart_time:
            uptime = datetime.now() - self.last_restart_time
            info["uptime_seconds"] = uptime.total_seconds()

        # Try to get memory usage on supported platforms
        try:
            if platform.system() == "Darwin":  # macOS
                cmd = ["ps", "-o", "rss=", "-p", str(self.server_process.pid)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.stdout.strip():
                    memory_kb = int(result.stdout.strip())
                    info["memory_usage_kb"] = memory_kb
        except Exception:
            pass

    return info

def _kill_server_process(self, force=False):
    """Kill the server process.

    Args:
        force: If True, use SIGKILL instead of SIGTERM.
    """
    if self.server_process is None:
        return

    try:
        # Get process group ID on Unix/Linux/macOS
        if hasattr(os, 'killpg') and hasattr(os, 'getpgid'):
            sig = signal.SIGKILL if force else signal.SIGTERM
            try:
                os.killpg(os.getpgid(self.server_process.pid), sig)
            except ProcessLookupError:
                # Process already gone
                pass
        else:
            # Windows doesn't have process groups
            sig = signal.SIGTERM
            if force and hasattr(signal, 'SIGKILL'):
                sig = signal.SIGKILL
            self.server_process.send_signal(sig)

        # Wait for the process to terminate
        try:
            self.server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't terminate gracefully
            if not force:
                logger.warning("Server not responding to SIGTERM, sending SIGKILL")
                self._kill_server_process(force=True)

    except Exception as e:
        logger.exception(f"Error killing server process: {e}")


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
