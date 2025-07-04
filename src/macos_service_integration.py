#!/usr/bin/env python3
"""
macOS Service and System Tray Integration
Provides functionality for running as a macOS service and system tray application
"""

import os
import sys
import json
import time
import threading
import subprocess
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import logging

# Configure logging
logger = logging.getLogger(__name__)

class MacOSServiceManager:
    """Manages macOS service functionality and system tray integration"""
    
    def __init__(self, app_name: str = "GerdsenAI", port: int = 8080):
        self.app_name = app_name
        self.port = port
        self.service_running = False
        self.tray_active = False
        self.server_process = None
        self.status_callback = None
        
        # Paths
        self.app_dir = Path.home() / "Library" / "Application Support" / self.app_name
        self.config_file = self.app_dir / "config.json"
        self.log_file = self.app_dir / "service.log"
        self.pid_file = self.app_dir / "service.pid"
        
        # Ensure directories exist
        self.app_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load service configuration"""
        default_config = {
            "auto_start": False,
            "minimize_to_tray": True,
            "start_minimized": False,
            "port": self.port,
            "log_level": "INFO",
            "update_check": True,
            "notifications": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    default_config.update(config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save service configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def create_launch_agent(self) -> bool:
        """Create macOS LaunchAgent for auto-start functionality"""
        try:
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            launch_agents_dir.mkdir(exist_ok=True)
            
            plist_file = launch_agents_dir / f"ai.gerdsen.{self.app_name.lower()}.plist"
            
            # Get the current Python executable and script path
            python_exe = sys.executable
            script_path = Path(__file__).parent / "production_main.py"
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.gerdsen.{self.app_name.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{script_path}</string>
        <string>--service</string>
        <string>--port</string>
        <string>{self.port}</string>
    </array>
    <key>RunAtLoad</key>
    <{str(self.config.get('auto_start', False)).lower()}/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{self.log_file}</string>
    <key>StandardErrorPath</key>
    <string>{self.log_file}</string>
    <key>WorkingDirectory</key>
    <string>{Path(__file__).parent}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>"""
            
            with open(plist_file, 'w') as f:
                f.write(plist_content)
            
            logger.info(f"Created LaunchAgent: {plist_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create LaunchAgent: {e}")
            return False
    
    def install_service(self) -> bool:
        """Install the service for auto-start"""
        try:
            if not self.create_launch_agent():
                return False
            
            # Load the service
            plist_file = Path.home() / "Library" / "LaunchAgents" / f"ai.gerdsen.{self.app_name.lower()}.plist"
            result = subprocess.run([
                "launchctl", "load", str(plist_file)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Service installed successfully")
                return True
            else:
                logger.error(f"Failed to load service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to install service: {e}")
            return False
    
    def uninstall_service(self) -> bool:
        """Uninstall the service"""
        try:
            plist_file = Path.home() / "Library" / "LaunchAgents" / f"ai.gerdsen.{self.app_name.lower()}.plist"
            
            if plist_file.exists():
                # Unload the service
                subprocess.run([
                    "launchctl", "unload", str(plist_file)
                ], capture_output=True, text=True)
                
                # Remove the plist file
                plist_file.unlink()
                logger.info("Service uninstalled successfully")
                return True
            else:
                logger.warning("Service not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to uninstall service: {e}")
            return False
    
    def start_service(self) -> bool:
        """Start the service"""
        try:
            if self.is_service_running():
                logger.info("Service is already running")
                return True
            
            # Start the server process
            python_exe = sys.executable
            script_path = Path(__file__).parent / "production_main.py"
            
            self.server_process = subprocess.Popen([
                python_exe, str(script_path),
                "--service",
                "--port", str(self.port)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(self.server_process.pid))
            
            # Wait a moment to check if it started successfully
            time.sleep(2)
            
            if self.server_process.poll() is None:
                self.service_running = True
                logger.info(f"Service started with PID: {self.server_process.pid}")
                
                if self.status_callback:
                    self.status_callback("Service started")
                
                return True
            else:
                logger.error("Service failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop the service"""
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
                self.server_process = None
            
            # Also try to kill by PID if file exists
            if self.pid_file.exists():
                try:
                    with open(self.pid_file, 'r') as f:
                        pid = int(f.read().strip())
                    
                    subprocess.run(["kill", str(pid)], check=False)
                    self.pid_file.unlink()
                except Exception:
                    pass
            
            self.service_running = False
            logger.info("Service stopped")
            
            if self.status_callback:
                self.status_callback("Service stopped")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            return False
    
    def restart_service(self) -> bool:
        """Restart the service"""
        logger.info("Restarting service...")
        self.stop_service()
        time.sleep(1)
        return self.start_service()
    
    def is_service_running(self) -> bool:
        """Check if the service is running"""
        try:
            if self.server_process and self.server_process.poll() is None:
                return True
            
            # Check by PID file
            if self.pid_file.exists():
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process exists
                result = subprocess.run(["ps", "-p", str(pid)], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            
            return False
            
        except Exception:
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        return {
            "running": self.is_service_running(),
            "port": self.port,
            "pid": self.server_process.pid if self.server_process else None,
            "auto_start": self.config.get("auto_start", False),
            "minimize_to_tray": self.config.get("minimize_to_tray", True),
            "config_file": str(self.config_file),
            "log_file": str(self.log_file),
            "app_url": f"http://localhost:{self.port}"
        }
    
    def open_app(self):
        """Open the application in the default browser"""
        url = f"http://localhost:{self.port}"
        webbrowser.open(url)
        logger.info(f"Opened application: {url}")
    
    def show_in_finder(self):
        """Show application directory in Finder"""
        subprocess.run(["open", str(self.app_dir)])
    
    def update_config(self, **kwargs):
        """Update configuration settings"""
        self.config.update(kwargs)
        self._save_config()
        logger.info("Configuration updated")
    
    def set_status_callback(self, callback: Callable[[str], None]):
        """Set callback for status updates"""
        self.status_callback = callback
    
    def create_menu_bar_app(self):
        """Create a simple menu bar application (requires additional dependencies)"""
        # This would typically use PyObjC or similar for native macOS integration
        # For now, we'll create a simple status monitoring script
        
        menu_script = f"""#!/usr/bin/env python3
import time
import subprocess
import sys
from pathlib import Path

def check_service_status():
    try:
        result = subprocess.run([
            "curl", "-s", "-o", "/dev/null", "-w", "%{{http_code}}", 
            "http://localhost:{self.port}/api/health"
        ], capture_output=True, text=True, timeout=5)
        return result.stdout == "200"
    except:
        return False

def main():
    print("GerdsenAI Service Monitor")
    print("Press Ctrl+C to exit")
    
    while True:
        try:
            if check_service_status():
                print("\\r✅ Service running", end="", flush=True)
            else:
                print("\\r❌ Service stopped", end="", flush=True)
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\\nExiting...")
            break

if __name__ == "__main__":
    main()
"""
        
        monitor_script = self.app_dir / "service_monitor.py"
        with open(monitor_script, 'w') as f:
            f.write(menu_script)
        
        # Make executable
        monitor_script.chmod(0o755)
        
        logger.info(f"Created service monitor: {monitor_script}")
        return monitor_script

class SystemTrayIntegration:
    """Handles system tray integration for macOS"""
    
    def __init__(self, service_manager: MacOSServiceManager):
        self.service_manager = service_manager
        self.tray_active = False
        
    def create_tray_icon(self):
        """Create system tray icon (simplified version)"""
        # This would typically require PyObjC for native macOS integration
        # For now, we'll create a dock icon alternative
        
        dock_script = f"""#!/usr/bin/env osascript
on run
    set appName to "GerdsenAI"
    set appURL to "http://localhost:{self.service_manager.port}"
    
    display dialog "GerdsenAI is running in the background.\\n\\nClick OK to open the application." \\
        with title appName \\
        buttons {{"Open App", "Quit"}} \\
        default button "Open App" \\
        with icon note
    
    set buttonPressed to button returned of result
    
    if buttonPressed is "Open App" then
        do shell script "open " & quoted form of appURL
    else if buttonPressed is "Quit" then
        do shell script "pkill -f 'python.*production_main.py'"
    end if
end run
"""
        
        dock_script_path = self.service_manager.app_dir / "dock_integration.scpt"
        with open(dock_script_path, 'w') as f:
            f.write(dock_script)
        
        return dock_script_path
    
    def minimize_to_tray(self):
        """Minimize application to system tray"""
        if self.service_manager.config.get("minimize_to_tray", True):
            logger.info("Application minimized to system tray")
            self.tray_active = True
            return True
        return False
    
    def restore_from_tray(self):
        """Restore application from system tray"""
        if self.tray_active:
            self.service_manager.open_app()
            self.tray_active = False
            logger.info("Application restored from system tray")
            return True
        return False

def create_app_bundle():
    """Create a basic macOS app bundle structure"""
    app_name = "GerdsenAI"
    bundle_dir = Path.home() / "Applications" / f"{app_name}.app"
    contents_dir = bundle_dir / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    # Create directories
    for directory in [bundle_dir, contents_dir, macos_dir, resources_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create Info.plist
    info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{app_name}</string>
    <key>CFBundleIdentifier</key>
    <string>ai.gerdsen.{app_name.lower()}</string>
    <key>CFBundleName</key>
    <string>{app_name}</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>"""
    
    with open(contents_dir / "Info.plist", 'w') as f:
        f.write(info_plist)
    
    # Create launcher script
    launcher_script = f"""#!/bin/bash
cd "$(dirname "$0")/../../.."
python3 -m src.production_main --app-bundle
"""
    
    launcher_path = macos_dir / app_name
    with open(launcher_path, 'w') as f:
        f.write(launcher_script)
    
    launcher_path.chmod(0o755)
    
    logger.info(f"Created app bundle: {bundle_dir}")
    return bundle_dir

# Example usage and testing functions
def main():
    """Main function for testing the service integration"""
    service_manager = MacOSServiceManager()
    tray_integration = SystemTrayIntegration(service_manager)
    
    print("GerdsenAI macOS Service Integration")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Start service")
        print("2. Stop service")
        print("3. Restart service")
        print("4. Check status")
        print("5. Install service (auto-start)")
        print("6. Uninstall service")
        print("7. Open application")
        print("8. Create app bundle")
        print("9. Exit")
        
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == "1":
            if service_manager.start_service():
                print("✅ Service started successfully")
            else:
                print("❌ Failed to start service")
        
        elif choice == "2":
            if service_manager.stop_service():
                print("✅ Service stopped successfully")
            else:
                print("❌ Failed to stop service")
        
        elif choice == "3":
            if service_manager.restart_service():
                print("✅ Service restarted successfully")
            else:
                print("❌ Failed to restart service")
        
        elif choice == "4":
            status = service_manager.get_service_status()
            print("\nService Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
        
        elif choice == "5":
            if service_manager.install_service():
                print("✅ Service installed for auto-start")
            else:
                print("❌ Failed to install service")
        
        elif choice == "6":
            if service_manager.uninstall_service():
                print("✅ Service uninstalled")
            else:
                print("❌ Failed to uninstall service")
        
        elif choice == "7":
            service_manager.open_app()
            print("✅ Application opened in browser")
        
        elif choice == "8":
            bundle_path = create_app_bundle()
            print(f"✅ App bundle created: {bundle_path}")
        
        elif choice == "9":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

