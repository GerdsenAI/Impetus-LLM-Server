#!/usr/bin/env python3
"""
macOS Service Wrapper for GerdsenAI MLX Manager
Provides menu bar integration, minimize-to-tray functionality, and service management
"""

import os
import sys
import json
import time
import threading
import subprocess
import logging
import signal
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Try to import macOS-specific libraries
try:
    import rumps  # For menu bar applications
    RUMPS_AVAILABLE = True
except ImportError:
    RUMPS_AVAILABLE = False
    print("rumps not available - menu bar functionality will be limited")

try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("pystray not available - system tray functionality will be limited")

@dataclass
class ServiceConfig:
    """Configuration for the macOS service"""
    app_name: str = "GerdsenAI MLX Manager"
    server_port: int = 5000
    auto_start_server: bool = True
    minimize_to_tray: bool = True
    show_notifications: bool = True
    log_level: str = "INFO"
    update_interval: int = 2  # seconds

class MacOSService:
    """Main macOS service class for GerdsenAI MLX Manager"""
    
    def __init__(self, config: ServiceConfig = None):
        self.config = config or ServiceConfig()
        self.server_process = None
        self.is_running = False
        self.menu_app = None
        self.tray_icon = None
        
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize service components
        self._setup_signal_handlers()
        self._create_menu_bar_app()
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def _create_menu_bar_app(self):
        """Create menu bar application"""
        if RUMPS_AVAILABLE:
            self._create_rumps_app()
        elif PYSTRAY_AVAILABLE:
            self._create_pystray_app()
        else:
            self.logger.warning("No menu bar library available")
    
    def _create_rumps_app(self):
        """Create rumps-based menu bar application"""
        try:
            self.menu_app = rumps.App(self.config.app_name, "🧠")
            
            # Add menu items
            self.menu_app.menu = [
                rumps.MenuItem("Open Dashboard", callback=self._open_dashboard),
                rumps.MenuItem("Performance Monitor", callback=self._open_performance),
                rumps.MenuItem("Model Manager", callback=self._open_models),
                rumps.separator,
                rumps.MenuItem("Start Server", callback=self._start_server),
                rumps.MenuItem("Stop Server", callback=self._stop_server),
                rumps.separator,
                rumps.MenuItem("Settings", callback=self._open_settings),
                rumps.MenuItem("About", callback=self._show_about),
                rumps.separator,
                rumps.MenuItem("Quit", callback=self._quit_app)
            ]
            
            self.logger.info("rumps menu bar app created")
            
        except Exception as e:
            self.logger.error(f"Failed to create rumps app: {e}")
            self.menu_app = None
    
    def _create_pystray_app(self):
        """Create pystray-based system tray application"""
        try:
            # Create a simple icon (you would normally load from file)
            image = Image.new('RGB', (64, 64), color='blue')
            
            menu = pystray.Menu(
                item('Open Dashboard', self._open_dashboard),
                item('Performance Monitor', self._open_performance),
                item('Model Manager', self._open_models),
                pystray.Menu.SEPARATOR,
                item('Start Server', self._start_server),
                item('Stop Server', self._stop_server),
                pystray.Menu.SEPARATOR,
                item('Settings', self._open_settings),
                item('About', self._show_about),
                pystray.Menu.SEPARATOR,
                item('Quit', self._quit_app)
            )
            
            self.tray_icon = pystray.Icon(
                self.config.app_name,
                image,
                menu=menu
            )
            
            self.logger.info("pystray system tray app created")
            
        except Exception as e:
            self.logger.error(f"Failed to create pystray app: {e}")
            self.tray_icon = None
    
    def _open_dashboard(self, sender=None):
        """Open the main dashboard"""
        url = f"http://localhost:{self.config.server_port}"
        webbrowser.open(url)
        self.logger.info("Opened dashboard")
    
    def _open_performance(self, sender=None):
        """Open performance monitor"""
        url = f"http://localhost:{self.config.server_port}#performance"
        webbrowser.open(url)
        self.logger.info("Opened performance monitor")
    
    def _open_models(self, sender=None):
        """Open model manager"""
        url = f"http://localhost:{self.config.server_port}#models"
        webbrowser.open(url)
        self.logger.info("Opened model manager")
    
    def _start_server(self, sender=None):
        """Start the Flask server"""
        if self.server_process is None:
            self.start_server()
        else:
            self.logger.info("Server is already running")
    
    def _stop_server(self, sender=None):
        """Stop the Flask server"""
        if self.server_process is not None:
            self.stop_server()
        else:
            self.logger.info("Server is not running")
    
    def _open_settings(self, sender=None):
        """Open settings"""
        url = f"http://localhost:{self.config.server_port}#settings"
        webbrowser.open(url)
        self.logger.info("Opened settings")
    
    def _show_about(self, sender=None):
        """Show about dialog"""
        if RUMPS_AVAILABLE and self.menu_app:
            rumps.alert(
                title="About GerdsenAI MLX Manager",
                message="Advanced MLX model management for Apple Silicon\nVersion 2.0.0 Enhanced",
                ok="OK"
            )
        else:
            self.logger.info("About: GerdsenAI MLX Manager v2.0.0 Enhanced")
    
    def _quit_app(self, sender=None):
        """Quit the application"""
        self.stop()
        if RUMPS_AVAILABLE and self.menu_app:
            rumps.quit_application()
        elif PYSTRAY_AVAILABLE and self.tray_icon:
            self.tray_icon.stop()
        sys.exit(0)
    
    def start_server(self):
        """Start the Flask server process"""
        try:
            server_path = Path(__file__).parent.parent / "gerdsen_ai_server" / "src" / "main.py"
            
            if not server_path.exists():
                self.logger.error(f"Server file not found: {server_path}")
                return False
            
            # Start server in background
            self.server_process = subprocess.Popen([
                sys.executable, str(server_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.logger.info(f"Started server with PID: {self.server_process.pid}")
            
            # Wait a moment for server to start
            time.sleep(2)
            
            # Check if server is running
            if self.server_process.poll() is None:
                self.logger.info("Server started successfully")
                return True
            else:
                self.logger.error("Server failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the Flask server process"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.logger.info("Server stopped successfully")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.logger.warning("Server killed after timeout")
            except Exception as e:
                self.logger.error(f"Error stopping server: {e}")
            finally:
                self.server_process = None
    
    def start(self):
        """Start the macOS service"""
        self.is_running = True
        self.logger.info("Starting GerdsenAI MLX Manager service")
        
        # Auto-start server if configured
        if self.config.auto_start_server:
            self.start_server()
        
        # Start menu bar app
        if RUMPS_AVAILABLE and self.menu_app:
            self.logger.info("Starting rumps menu bar app")
            self.menu_app.run()
        elif PYSTRAY_AVAILABLE and self.tray_icon:
            self.logger.info("Starting pystray system tray")
            self.tray_icon.run()
        else:
            # Fallback: run in console mode
            self.logger.info("Running in console mode")
            self._console_mode()
    
    def _console_mode(self):
        """Run in console mode when no GUI libraries are available"""
        print(f"\n{self.config.app_name} - Console Mode")
        print("=" * 50)
        print("Commands:")
        print("  start  - Start the server")
        print("  stop   - Stop the server")
        print("  open   - Open dashboard in browser")
        print("  status - Show server status")
        print("  quit   - Quit the application")
        print("=" * 50)
        
        while self.is_running:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command == "start":
                    self.start_server()
                elif command == "stop":
                    self.stop_server()
                elif command == "open":
                    self._open_dashboard()
                elif command == "status":
                    status = "Running" if self.server_process else "Stopped"
                    print(f"Server status: {status}")
                elif command == "quit":
                    break
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        self.stop()
    
    def stop(self):
        """Stop the macOS service"""
        self.is_running = False
        self.logger.info("Stopping GerdsenAI MLX Manager service")
        
        # Stop server
        self.stop_server()
        
        # Stop menu bar app
        if PYSTRAY_AVAILABLE and self.tray_icon:
            self.tray_icon.stop()

class LaunchAgentManager:
    """Manages macOS Launch Agent for automatic startup"""
    
    def __init__(self, service_config: ServiceConfig):
        self.config = service_config
        self.plist_path = Path.home() / "Library" / "LaunchAgents" / "com.gerdsen.ai.mlx.manager.plist"
        self.logger = logging.getLogger(__name__)
    
    def create_launch_agent(self, python_path: str, script_path: str):
        """Create Launch Agent plist file"""
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gerdsen.ai.mlx.manager</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
        <string>--service</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/gerdsen-ai-mlx-manager.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/gerdsen-ai-mlx-manager.error.log</string>
    <key>WorkingDirectory</key>
    <string>{Path(script_path).parent}</string>
</dict>
</plist>"""
        
        try:
            # Create LaunchAgents directory if it doesn't exist
            self.plist_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write plist file
            with open(self.plist_path, 'w') as f:
                f.write(plist_content)
            
            self.logger.info(f"Created Launch Agent: {self.plist_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create Launch Agent: {e}")
            return False
    
    def install_launch_agent(self):
        """Install and load the Launch Agent"""
        try:
            # Load the launch agent
            subprocess.run([
                "launchctl", "load", str(self.plist_path)
            ], check=True)
            
            self.logger.info("Launch Agent installed and loaded")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install Launch Agent: {e}")
            return False
    
    def uninstall_launch_agent(self):
        """Uninstall the Launch Agent"""
        try:
            # Unload the launch agent
            subprocess.run([
                "launchctl", "unload", str(self.plist_path)
            ], check=True)
            
            # Remove plist file
            if self.plist_path.exists():
                self.plist_path.unlink()
            
            self.logger.info("Launch Agent uninstalled")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to uninstall Launch Agent: {e}")
            return False

def main():
    """Main entry point for the macOS service"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GerdsenAI MLX Manager macOS Service")
    parser.add_argument("--service", action="store_true", help="Run as background service")
    parser.add_argument("--install", action="store_true", help="Install Launch Agent")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall Launch Agent")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Create service configuration
    config = ServiceConfig(
        server_port=args.port,
        log_level=args.log_level
    )
    
    if args.install:
        # Install Launch Agent
        manager = LaunchAgentManager(config)
        python_path = sys.executable
        script_path = os.path.abspath(__file__)
        
        if manager.create_launch_agent(python_path, script_path):
            if manager.install_launch_agent():
                print("Launch Agent installed successfully")
            else:
                print("Failed to install Launch Agent")
        else:
            print("Failed to create Launch Agent")
        return
    
    if args.uninstall:
        # Uninstall Launch Agent
        manager = LaunchAgentManager(config)
        if manager.uninstall_launch_agent():
            print("Launch Agent uninstalled successfully")
        else:
            print("Failed to uninstall Launch Agent")
        return
    
    # Start the service
    service = MacOSService(config)
    
    try:
        service.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        service.stop()

if __name__ == "__main__":
    main()

