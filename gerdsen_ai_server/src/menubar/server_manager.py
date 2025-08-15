"""
Server lifecycle management for the Impetus Menu Bar Application
"""

import subprocess
import time
import threading
import requests
import os
import sys
from pathlib import Path
from typing import Optional, Callable
from loguru import logger

from .config import (
    SERVER_MAIN, SERVER_DIR, API_BASE_URL, HEALTH_ENDPOINT,
    SERVER_STARTUP_TIMEOUT, SERVER_SHUTDOWN_TIMEOUT,
    CONFIG_DIR, LOGS_DIR, MODELS_DIR, CACHE_DIR
)


class ServerManager:
    """Manages the Flask server process lifecycle"""
    
    def __init__(self, status_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the server manager
        
        Args:
            status_callback: Function to call with status updates ('starting', 'running', 'stopped', 'error')
        """
        self.process: Optional[subprocess.Popen] = None
        self.status_callback = status_callback
        self.is_running = False
        self.health_check_thread: Optional[threading.Thread] = None
        self.stop_health_check = threading.Event()
        self.current_model: Optional[str] = None
        
        # Ensure directories exist
        for directory in [CONFIG_DIR, LOGS_DIR, MODELS_DIR, CACHE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def start_server(self) -> bool:
        """
        Start the Flask server process
        
        Returns:
            True if server started successfully, False otherwise
        """
        if self.is_running:
            logger.info("Server is already running")
            return True
        
        try:
            self._update_status("starting")
            
            # Set up environment variables
            env = os.environ.copy()
            env.update({
                "IMPETUS_HOST": "127.0.0.1",
                "IMPETUS_PORT": "8080",
                "IMPETUS_MODELS_DIR": str(MODELS_DIR),
                "IMPETUS_CACHE_DIR": str(CACHE_DIR),
                "IMPETUS_LOG_DIR": str(LOGS_DIR),
                "IMPETUS_LOG_LEVEL": "INFO",
                "PYTHONPATH": str(SERVER_DIR)
            })
            
            # Get Python from current virtual environment or system
            python_executable = sys.executable
            
            # Start the server process
            log_file = LOGS_DIR / "impetus_server.log"
            with open(log_file, "a") as log:
                self.process = subprocess.Popen(
                    [python_executable, str(SERVER_MAIN)],
                    cwd=str(SERVER_DIR),
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True  # Detach from parent process group
                )
            
            # Wait for server to be ready
            if self._wait_for_server():
                self.is_running = True
                self._update_status("running")
                
                # Start health monitoring
                self._start_health_monitoring()
                
                logger.info("Server started successfully")
                return True
            else:
                self.stop_server()
                self._update_status("error")
                logger.error("Server failed to start within timeout")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            self._update_status("error")
            return False
    
    def stop_server(self) -> bool:
        """
        Stop the Flask server process
        
        Returns:
            True if server stopped successfully, False otherwise
        """
        if not self.process:
            logger.info("No server process to stop")
            return True
        
        try:
            self._update_status("stopping")
            
            # Stop health monitoring
            self._stop_health_monitoring()
            
            # Terminate the process
            self.process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=SERVER_SHUTDOWN_TIMEOUT)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop gracefully
                self.process.kill()
                self.process.wait()
            
            self.process = None
            self.is_running = False
            self._update_status("stopped")
            
            logger.info("Server stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop server: {e}")
            self._update_status("error")
            return False
    
    def restart_server(self) -> bool:
        """
        Restart the Flask server
        
        Returns:
            True if server restarted successfully, False otherwise
        """
        logger.info("Restarting server...")
        self.stop_server()
        time.sleep(2)  # Brief pause before restart
        return self.start_server()
    
    def check_health(self) -> bool:
        """
        Check if the server is healthy
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_loaded_models(self) -> list:
        """
        Get list of loaded models from the server
        
        Returns:
            List of loaded model IDs
        """
        try:
            response = requests.get(f"{API_BASE_URL}/v1/models", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
        except:
            pass
        return []
    
    def load_model(self, model_id: str) -> bool:
        """
        Load a model on the server
        
        Args:
            model_id: The model ID to load
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            # For now, models auto-load when requested
            # We'll make a test request to trigger loading
            response = requests.post(
                f"{API_BASE_URL}/v1/chat/completions",
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=60  # Model loading can take time
            )
            
            if response.status_code in [200, 201]:
                self.current_model = model_id
                logger.info(f"Model {model_id} loaded successfully")
                return True
            else:
                logger.error(f"Failed to load model {model_id}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            return False
    
    def get_server_stats(self) -> dict:
        """
        Get server statistics (CPU, memory usage, etc.)
        
        Returns:
            Dictionary with server stats
        """
        try:
            import psutil
            
            stats = {
                "cpu_percent": 0,
                "memory_mb": 0,
                "uptime": 0
            }
            
            if self.process and self.is_running:
                try:
                    proc = psutil.Process(self.process.pid)
                    stats["cpu_percent"] = proc.cpu_percent(interval=0.1)
                    stats["memory_mb"] = proc.memory_info().rss / 1024 / 1024
                    stats["uptime"] = time.time() - proc.create_time()
                except:
                    pass
            
            return stats
            
        except ImportError:
            return {"error": "psutil not installed"}
    
    def _wait_for_server(self) -> bool:
        """
        Wait for the server to be ready
        
        Returns:
            True if server is ready, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
            if self.check_health():
                return True
            time.sleep(1)
        
        return False
    
    def _update_status(self, status: str):
        """Update status and notify callback if set"""
        if self.status_callback:
            self.status_callback(status)
    
    def _start_health_monitoring(self):
        """Start background health monitoring thread"""
        self.stop_health_check.clear()
        self.health_check_thread = threading.Thread(target=self._health_monitor_loop)
        self.health_check_thread.daemon = True
        self.health_check_thread.start()
    
    def _stop_health_monitoring(self):
        """Stop health monitoring thread"""
        self.stop_health_check.set()
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
    
    def _health_monitor_loop(self):
        """Background loop to monitor server health"""
        consecutive_failures = 0
        
        while not self.stop_health_check.is_set():
            if self.check_health():
                consecutive_failures = 0
                self._update_status("running")
            else:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    self._update_status("error")
                    logger.warning(f"Server health check failed {consecutive_failures} times")
            
            self.stop_health_check.wait(5)  # Check every 5 seconds