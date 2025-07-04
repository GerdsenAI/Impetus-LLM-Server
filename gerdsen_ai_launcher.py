#!/usr/bin/env python3
"""
GerdsenAI MLX Manager - Integrated Launcher
Combines the Flask server with macOS service functionality
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
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import our components
try:
    from src.macos_service import MacOSService, ServiceConfig, LaunchAgentManager
    MACOS_SERVICE_AVAILABLE = True
except ImportError:
    MACOS_SERVICE_AVAILABLE = False
    print("macOS service not available")

try:
    from src.apple_silicon_detector import AppleSiliconDetector
    APPLE_SILICON_AVAILABLE = True
except ImportError:
    APPLE_SILICON_AVAILABLE = False
    print("Apple Silicon detector not available")

try:
    from src.enhanced_mlx_manager import EnhancedMLXManager
    MLX_MANAGER_AVAILABLE = True
except ImportError:
    MLX_MANAGER_AVAILABLE = False
    print("Enhanced MLX manager not available")

class GerdsenAILauncher:
    """Main launcher class that integrates all components"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.server_port = self.config.get('server_port', 5000)
        self.log_level = self.config.get('log_level', 'INFO')
        self.auto_start_server = self.config.get('auto_start_server', True)
        self.minimize_to_tray = self.config.get('minimize_to_tray', True)
        
        # Initialize logging
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.apple_detector = None
        self.mlx_manager = None
        self.macos_service = None
        self.server_process = None
        self.is_running = False
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all available components"""
        self.logger.info("Initializing GerdsenAI MLX Manager components...")
        
        # Initialize Apple Silicon detector
        if APPLE_SILICON_AVAILABLE:
            try:
                self.apple_detector = AppleSiliconDetector()
                self.logger.info("Apple Silicon detector initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Apple Silicon detector: {e}")
        
        # Initialize MLX manager
        if MLX_MANAGER_AVAILABLE:
            try:
                self.mlx_manager = EnhancedMLXManager()
                self.logger.info("Enhanced MLX manager initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize MLX manager: {e}")
        
        # Initialize macOS service
        if MACOS_SERVICE_AVAILABLE:
            try:
                service_config = ServiceConfig(
                    server_port=self.server_port,
                    auto_start_server=False,  # We'll handle server startup
                    minimize_to_tray=self.minimize_to_tray,
                    log_level=self.log_level
                )
                self.macos_service = MacOSService(service_config)
                self.logger.info("macOS service initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize macOS service: {e}")
    
    def start_server(self):
        """Start the Flask server"""
        try:
            server_path = Path(__file__).parent / "gerdsen_ai_server" / "src" / "main.py"
            
            if not server_path.exists():
                self.logger.error(f"Server file not found: {server_path}")
                return False
            
            # Set environment variables for the server
            env = os.environ.copy()
            env['PYTHONPATH'] = str(Path(__file__).parent)
            
            # Start server process
            self.server_process = subprocess.Popen([
                sys.executable, str(server_path)
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.logger.info(f"Started Flask server with PID: {self.server_process.pid}")
            
            # Wait for server to start
            time.sleep(3)
            
            # Check if server is running
            if self.server_process.poll() is None:
                self.logger.info("Flask server started successfully")
                return True
            else:
                stdout, stderr = self.server_process.communicate()
                self.logger.error(f"Server failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the Flask server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.logger.info("Flask server stopped successfully")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.logger.warning("Flask server killed after timeout")
            except Exception as e:
                self.logger.error(f"Error stopping server: {e}")
            finally:
                self.server_process = None
    
    def get_system_status(self):
        """Get comprehensive system status"""
        status = {
            'timestamp': time.time(),
            'server_running': self.server_process is not None,
            'server_port': self.server_port,
            'components': {
                'apple_silicon_detector': APPLE_SILICON_AVAILABLE,
                'mlx_manager': MLX_MANAGER_AVAILABLE,
                'macos_service': MACOS_SERVICE_AVAILABLE,
            }
        }
        
        # Add Apple Silicon info if available
        if self.apple_detector:
            try:
                status['apple_silicon'] = {
                    'detected': self.apple_detector.is_apple_silicon,
                    'chip_info': self.apple_detector.chip_info,
                    'system_info': self.apple_detector.system_info,
                }
            except Exception as e:
                self.logger.error(f"Error getting Apple Silicon status: {e}")
                status['apple_silicon'] = {'error': str(e)}
        
        # Add MLX manager info if available
        if self.mlx_manager:
            try:
                status['mlx'] = self.mlx_manager.get_system_status()
            except Exception as e:
                self.logger.error(f"Error getting MLX status: {e}")
                status['mlx'] = {'error': str(e)}
        
        return status
    
    def start(self, mode='service'):
        """Start the launcher in specified mode"""
        self.is_running = True
        self.logger.info(f"Starting GerdsenAI MLX Manager in {mode} mode")
        
        # Start Flask server if configured
        if self.auto_start_server:
            if not self.start_server():
                self.logger.error("Failed to start server, continuing anyway...")
        
        # Start in appropriate mode
        if mode == 'service' and self.macos_service:
            # Run as macOS service with menu bar
            self.logger.info("Starting macOS service mode")
            self.macos_service.start()
        elif mode == 'console':
            # Run in console mode
            self.logger.info("Starting console mode")
            self._console_mode()
        elif mode == 'server-only':
            # Run server only
            self.logger.info("Starting server-only mode")
            self._server_only_mode()
        else:
            self.logger.error(f"Unknown mode: {mode}")
            self.stop()
    
    def _console_mode(self):
        """Run in console mode"""
        print(f"\n🧠 GerdsenAI MLX Manager - Console Mode")
        print("=" * 60)
        
        # Show system status
        status = self.get_system_status()
        print(f"🖥️  Server: {'Running' if status['server_running'] else 'Stopped'}")
        print(f"🔗 URL: http://localhost:{self.server_port}")
        
        if status.get('apple_silicon', {}).get('detected'):
            chip_info = status['apple_silicon']['chip_info']
            if chip_info:
                print(f"🍎 Chip: {chip_info.get('name', 'Unknown')}")
                print(f"💾 Memory: {chip_info.get('memory_gb', 'Unknown')} GB")
        
        print("\nCommands:")
        print("  start   - Start the server")
        print("  stop    - Stop the server")
        print("  open    - Open dashboard in browser")
        print("  status  - Show detailed status")
        print("  restart - Restart the server")
        print("  quit    - Quit the application")
        print("=" * 60)
        
        while self.is_running:
            try:
                command = input("\n🤖 Enter command: ").strip().lower()
                
                if command == "start":
                    if not self.server_process:
                        self.start_server()
                    else:
                        print("Server is already running")
                elif command == "stop":
                    if self.server_process:
                        self.stop_server()
                    else:
                        print("Server is not running")
                elif command == "open":
                    webbrowser.open(f"http://localhost:{self.server_port}")
                    print("Opened dashboard in browser")
                elif command == "status":
                    status = self.get_system_status()
                    print(json.dumps(status, indent=2))
                elif command == "restart":
                    if self.server_process:
                        self.stop_server()
                        time.sleep(1)
                    self.start_server()
                elif command == "quit":
                    break
                else:
                    print("Unknown command. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        self.stop()
    
    def _server_only_mode(self):
        """Run in server-only mode"""
        print(f"🚀 Starting server on http://localhost:{self.server_port}")
        
        if not self.server_process:
            if not self.start_server():
                print("❌ Failed to start server")
                return
        
        print("✅ Server started successfully")
        print("Press Ctrl+C to stop...")
        
        try:
            # Wait for server process
            while self.is_running and self.server_process:
                if self.server_process.poll() is not None:
                    print("❌ Server process ended unexpectedly")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
        
        self.stop()
    
    def stop(self):
        """Stop all components"""
        self.is_running = False
        self.logger.info("Stopping GerdsenAI MLX Manager")
        
        # Stop server
        self.stop_server()
        
        # Stop macOS service
        if self.macos_service:
            self.macos_service.stop()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="GerdsenAI MLX Manager")
    parser.add_argument("--mode", choices=['service', 'console', 'server-only'], 
                       default='service', help="Run mode")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    parser.add_argument("--no-auto-start", action="store_true", 
                       help="Don't auto-start server")
    parser.add_argument("--install-service", action="store_true",
                       help="Install as macOS Launch Agent")
    parser.add_argument("--uninstall-service", action="store_true",
                       help="Uninstall macOS Launch Agent")
    
    args = parser.parse_args()
    
    # Handle service installation/uninstallation
    if args.install_service or args.uninstall_service:
        if not MACOS_SERVICE_AVAILABLE:
            print("❌ macOS service functionality not available")
            sys.exit(1)
        
        config = ServiceConfig(server_port=args.port, log_level=args.log_level)
        manager = LaunchAgentManager(config)
        
        if args.install_service:
            python_path = sys.executable
            script_path = os.path.abspath(__file__)
            
            if manager.create_launch_agent(python_path, script_path):
                if manager.install_launch_agent():
                    print("✅ Launch Agent installed successfully")
                else:
                    print("❌ Failed to install Launch Agent")
            else:
                print("❌ Failed to create Launch Agent")
        
        if args.uninstall_service:
            if manager.uninstall_launch_agent():
                print("✅ Launch Agent uninstalled successfully")
            else:
                print("❌ Failed to uninstall Launch Agent")
        
        return
    
    # Create launcher configuration
    config = {
        'server_port': args.port,
        'log_level': args.log_level,
        'auto_start_server': not args.no_auto_start,
        'minimize_to_tray': True,
    }
    
    # Create and start launcher
    launcher = GerdsenAILauncher(config)
    
    try:
        launcher.start(mode=args.mode)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        launcher.stop()
    except Exception as e:
        print(f"❌ Error: {e}")
        launcher.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()

