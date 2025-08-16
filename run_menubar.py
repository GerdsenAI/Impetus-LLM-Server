#!/usr/bin/env python3
"""
Impetus MLX Server Menu Bar Application
macOS native menu bar controller with permissions and onboarding
"""

import rumps
import subprocess
import requests
import json
import os
import psutil
import threading
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gerdsen_ai_server'))

try:
    from gerdsen_ai_server.src.menubar.permissions_manager import PermissionsManager
    from gerdsen_ai_server.src.menubar.onboarding import OnboardingTour
    from gerdsen_ai_server.src.menubar.single_instance import (
        SingleInstance,
        find_menubar_processes,
        kill_all_menubar_processes
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)


class ImpetusMenuBar(rumps.App):
    """Menu bar application with permissions and onboarding"""
    
    def __init__(self):
        super(ImpetusMenuBar, self).__init__("🧠", title="Impetus MLX Server")

        # Application state
        self.server_process = None
        self.server_status = "stopped"
        self.current_model = None
        self.performance_mode = "Balanced Mode"
        self.start_time = None
        # Test mode flag to disable onboarding/permission prompts in automation
        self.test_mode = os.environ.get("IMPETUS_TEST_MODE", "0") == "1"

        # Preferences file
        self.preferences_file = os.path.expanduser("~/Library/Preferences/com.gerdsenai.impetus.json")

        # Initialize managers (skip heavy dialogs in test mode)
        if not self.test_mode:
            self.permissions_manager = PermissionsManager()
            self.onboarding_tour = OnboardingTour(self)
        else:
            self.permissions_manager = None
            self.onboarding_tour = None

        # Load preferences
        self.load_preferences()

        # Setup menu
        self.setup_menu()

        # Check first run and handle onboarding (skip in test mode)
        if not self.test_mode:
            self.handle_first_run()

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_server, daemon=True)
        self.monitor_thread.start()
    
    def load_preferences(self):
        """Load user preferences from JSON file"""
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    prefs = json.load(f)
                    self.performance_mode = prefs.get('performance_mode', 'Balanced Mode')
        except Exception as e:
            print(f"Error loading preferences: {e}")
    
    def save_preferences(self):
        """Save user preferences to JSON file"""
        try:
            # Load existing preferences
            prefs = {}
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    prefs = json.load(f)
            
            # Update performance mode
            prefs['performance_mode'] = self.performance_mode
            
            # Save to file
            os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
            with open(self.preferences_file, 'w') as f:
                json.dump(prefs, f, indent=2)
        except Exception as e:
            print(f"Error saving preferences: {e}")
    
    def handle_first_run(self):
        """Handle first run setup including permissions and onboarding"""
        if self.onboarding_tour.should_show_tour():
            # First run - show welcome and check permissions
            def first_run_setup():
                time.sleep(1)  # Let the app fully initialize
                
                # Schedule UI operations on the main thread using rumps timer
                rumps.Timer(self.delayed_first_run_setup, 0.1).start()
            
            threading.Thread(target=first_run_setup, daemon=True).start()
        else:
            # Not first run - check if we have required permissions
            if not self.permissions_manager.has_required_permissions():
                def check_permissions():
                    time.sleep(2)  # Brief delay
                    missing = self.permissions_manager.get_missing_permissions()
                    if missing:
                        self.show_missing_permissions_dialog(missing)
                
                threading.Thread(target=check_permissions, daemon=True).start()
    
    def delayed_first_run_setup(self, timer):
        """Execute first run setup on main thread"""
        timer.stop()  # Stop the timer since this is a one-time operation
        
        # Request permissions first
        self.request_initial_permissions()
        
        # Start onboarding tour
        self.onboarding_tour.start_tour(completion_callback=self.on_tour_completed)
    
    def request_initial_permissions(self):
        """Request initial permissions on first run"""
        try:
            # Request notifications
            self.permissions_manager.request_permission(
                'notifications',
                callback=self.permission_callback
            )
            
            # Request file access
            self.permissions_manager.request_permission(
                'file_access', 
                callback=self.permission_callback
            )
            
            # Optional: Request accessibility (only if user wants advanced features)
            response = rumps.alert(
                title="Enhanced Features",
                message="Would you like to enable enhanced features?\n\n"
                       "This includes advanced system monitoring and interactions.\n"
                       "(This step is optional)",
                ok="Enable",
                cancel="Skip"
            )
            
            if response == 1:  # Enable clicked
                self.permissions_manager.request_permission(
                    'accessibility',
                    callback=self.permission_callback
                )
                
        except Exception as e:
            print(f"Error requesting permissions: {e}")
    
    def permission_callback(self, permission_type: str, granted: bool):
        """Callback for permission requests"""
        if granted:
            rumps.notification(
                title="Permission Granted",
                subtitle=f"{permission_type.title()} access enabled",
                message="Thank you for enabling this permission",
                sound=False
            )
        else:
            print(f"Permission {permission_type} was denied or requires manual setup")
    
    def show_missing_permissions_dialog(self, missing: dict):
        """Show dialog about missing permissions"""
        if not missing:
            return
        
        message_lines = ["Some permissions are missing:\n"]
        for perm, desc in missing.items():
            message_lines.append(f"• {desc}")
        
        message_lines.append("\nWould you like to set them up now?")
        
        response = rumps.alert(
            title="Permissions Needed",
            message="\n".join(message_lines),
            ok="Setup Permissions",
            cancel="Later"
        )
        
        if response == 1:  # Setup clicked
            self.show_permissions_setup()
    
    def show_permissions_setup(self):
        """Show permissions setup options"""
        self.permissions_manager.show_permissions_summary()
    
    def on_tour_completed(self):
        """Called when onboarding tour is completed"""
        rumps.notification(
            title="Welcome to Impetus MLX Server! 🎉",
            subtitle="Setup complete",
            message="You're ready to start using your local AI server",
            sound=False
        )
    
    def setup_menu(self):
        """Setup the menu structure with enhanced options"""
        # Status item (non-clickable)
        self.status_item = rumps.MenuItem("Server: Stopped", callback=None)
        
        # Models submenu
        self.models_menu = rumps.MenuItem("Models")
        self.models_menu.add(rumps.MenuItem(
            "Mistral 7B (4-bit) (3.8 GB)", 
            callback=lambda s: self.load_model_by_name("Mistral 7B")
        ))
        self.models_menu.add(rumps.MenuItem(
            "Llama 3.2 3B (4-bit) (1.8 GB)",
            callback=lambda s: self.load_model_by_name("Llama 3.2 3B")
        ))
        self.models_menu.add(rumps.MenuItem(
            "Phi 3.5 Mini (4-bit) (2.2 GB)",
            callback=lambda s: self.load_model_by_name("Phi 3.5 Mini")
        ))
        self.models_menu.add(rumps.MenuItem(
            "Qwen 2.5 Coder 7B (4-bit) (4.0 GB)",
            callback=lambda s: self.load_model_by_name("Qwen 2.5 Coder 7B")
        ))
        self.models_menu.add(rumps.separator)
        self.models_menu.add(rumps.MenuItem("Load Custom Model...", callback=self.load_custom_model))
        
        # Performance mode submenu
        self.performance_menu = rumps.MenuItem("Performance Mode")
        self.performance_menu.add(rumps.MenuItem(
            "Efficiency Mode",
            callback=lambda s: self.set_performance_mode_by_name("Efficiency Mode")
        ))
        self.performance_menu.add(rumps.MenuItem(
            "Balanced Mode",
            callback=lambda s: self.set_performance_mode_by_name("Balanced Mode")
        ))
        self.performance_menu.add(rumps.MenuItem(
            "Performance Mode",
            callback=lambda s: self.set_performance_mode_by_name("Performance Mode")
        ))
        
        # Help submenu
        self.help_menu = rumps.MenuItem("Help")
        self.help_menu.add(rumps.MenuItem("Take Tour Again", callback=self.restart_tour))
        self.help_menu.add(rumps.MenuItem("Show Permissions", callback=self.show_permissions_status))
        self.help_menu.add(rumps.MenuItem("Setup Permissions", callback=self.setup_permissions))
        self.help_menu.add(rumps.separator)
        self.help_menu.add(rumps.MenuItem("About Impetus", callback=self.show_about))
        
        # Build the main menu
        self.menu = [
            self.status_item,
            rumps.separator,
            "Start Server",
            rumps.separator,
            "Open Dashboard",
            "API Documentation", 
            rumps.separator,
            self.models_menu,
            self.performance_menu,
            rumps.separator,
            "Server Stats",
            "View Logs",
            rumps.separator,
            self.help_menu,
            "Preferences...",
            rumps.separator,
            "Quit Impetus"
        ]
        
        # Set initial performance mode checkmark
        self.update_performance_mode_menu()
    
    @rumps.clicked("Start Server")
    def start_server(self, _):
        """Start the Impetus server"""
        if self.server_status == "running":
            return
        
        self.icon = "🟡"  # Loading state
        self.menu["Start Server"].title = "Starting..."
        
        def start_server_thread():
            try:
                # Change to project directory and start server
                project_dir = "/Volumes/M2 Raid0/GerdsenAI_Repositories/Impetus-LLM-Server"
                if os.path.exists(project_dir):
                    os.chdir(project_dir)
                
                # Try different server start methods
                server_commands = [
                    [sys.executable, "gerdsen_ai_server/src/main.py"],
                    ["python", "gerdsen_ai_server/src/main.py"],
                    ["python3", "gerdsen_ai_server/src/main.py"]
                ]
                
                for cmd in server_commands:
                    try:
                        self.server_process = subprocess.Popen(
                            cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            cwd=project_dir
                        )
                        break
                    except FileNotFoundError:
                        continue
                
                if not self.server_process:
                    raise Exception("Could not start server process")
                
                # Wait a moment for server to start
                time.sleep(3)
                
                # Check if server is responding
                try:
                    response = requests.get("http://localhost:8080/api/health", timeout=5)
                    if response.status_code == 200:
                        self.server_status = "running"
                        self.start_time = datetime.now()
                        self.icon = "🟢"
                        self.menu["Start Server"].title = "Stop Server"
                        self.status_item.title = "Server: Running"
                        rumps.notification(
                            "Impetus MLX Server", 
                            "Server Started", 
                            "Server is now running on port 8080",
                            sound=False
                        )
                    else:
                        raise Exception("Server not responding")
                except requests.exceptions.RequestException:
                    self.server_status = "error"
                    self.icon = "🔴"
                    self.menu["Start Server"].title = "Start Server"
                    rumps.notification(
                        "Impetus Server", 
                        "Start Failed", 
                        "Could not connect to server",
                        sound=True
                    )
                    
            except Exception as e:
                self.server_status = "error"
                self.icon = "🔴"
                self.menu["Start Server"].title = "Start Server"
                rumps.notification(
                    "Impetus Server", 
                    "Error", 
                    f"Failed to start server: {str(e)}",
                    sound=True
                )
        
        threading.Thread(target=start_server_thread, daemon=True).start()
    
    @rumps.clicked("Stop Server")
    def stop_server(self, _):
        """Stop the Impetus server"""
        if self.server_status != "running":
            return
        
        self.icon = "🟡"  # Loading state
        self.menu["Stop Server"].title = "Stopping..."
        
        def stop_server_thread():
            try:
                if self.server_process:
                    self.server_process.terminate()
                    try:
                        self.server_process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        self.server_process.kill()
                        self.server_process.wait()
                
                # Also kill any remaining processes
                try:
                    subprocess.run(["pkill", "-f", "python.*main.py"], 
                                 capture_output=True, timeout=5)
                except:
                    pass
                
                self.server_status = "stopped"
                self.start_time = None
                self.current_model = None
                self.icon = "🧠"
                self.menu["Stop Server"].title = "Start Server"
                self.status_item.title = "Server: Stopped"
                self.update_models_menu()
                
                rumps.notification(
                    "Impetus Server", 
                    "Server Stopped", 
                    "Server has been stopped",
                    sound=False
                )
                
            except Exception as e:
                rumps.notification(
                    "Impetus Server", 
                    "Error", 
                    f"Error stopping server: {str(e)}",
                    sound=True
                )
        
        threading.Thread(target=stop_server_thread, daemon=True).start()
    
    @rumps.clicked("Open Dashboard")
    def open_dashboard(self, _):
        """Open the dashboard in browser"""
        subprocess.run(["open", "http://localhost:5173"])
    
    @rumps.clicked("API Documentation")
    def open_api_docs(self, _):
        """Open API documentation in browser"""
        subprocess.run(["open", "http://localhost:8080/docs"])
    
    def load_model(self, sender):
        """Load a specific model"""
        if self.server_status != "running":
            rumps.alert("Server Not Running", "Please start the server first")
            return
        
        model_name = sender.title.split(" (")[0]  # Extract model name
        rumps.notification(
            "Impetus Server", 
            "Loading Model", 
            f"Loading {model_name}...",
            sound=False
        )
        
        def load_model_thread():
            try:
                # Simulate model loading (in real implementation, make API call)
                time.sleep(2)
                self.current_model = model_name
                self.update_models_menu()
                rumps.notification(
                    "Impetus Server", 
                    "Model Loaded", 
                    f"{model_name} is now active",
                    sound=False
                )
            except Exception as e:
                rumps.notification(
                    "Impetus Server", 
                    "Load Error", 
                    f"Failed to load {model_name}",
                    sound=True
                )
        
        threading.Thread(target=load_model_thread, daemon=True).start()
    
    def load_model_by_name(self, model_name):
        """Load a model by simplified name"""
        model_map = {
            "Mistral 7B": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
            "Llama 3.2 3B": "mlx-community/Llama-3.2-3B-Instruct-4bit", 
            "Phi 3.5 Mini": "mlx-community/Phi-3.5-mini-instruct-4bit",
            "Qwen 2.5 Coder 7B": "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"
        }
        model_id = model_map.get(model_name, model_name)
        
        # Create a mock sender object with the original title
        class MockSender:
            def __init__(self, title):
                self.title = title
        
        sender = MockSender(f"{model_name} (4-bit)")
        self.load_model(sender)
    
    @rumps.clicked("Load Custom Model...")
    def load_custom_model(self, _):
        """Load a custom model"""
        if self.server_status != "running":
            rumps.alert("Server Not Running", "Please start the server first")
            return
        
        # Get model ID from user
        response = rumps.Window(
            title="Load Custom Model",
            message="Enter the Hugging Face model ID:",
            default_text="mlx-community/",
            ok="Load",
            cancel="Cancel",
            dimensions=(350, 100)
        ).run()
        
        if response.clicked and response.text.strip():
            model_id = response.text.strip()
            self.load_custom_model_by_id(model_id)
    
    def load_custom_model_by_id(self, model_id: str):
        """Load a custom model by ID"""
        rumps.notification(
            "Impetus Server", 
            "Loading Custom Model", 
            f"Loading {model_id}...",
            sound=False
        )
        
        def load_thread():
            try:
                # In real implementation, make API call to load model
                time.sleep(3)  # Simulate loading
                self.current_model = model_id
                self.update_models_menu()
                rumps.notification(
                    "Impetus Server", 
                    "Model Loaded", 
                    f"{model_id} is ready",
                    sound=False
                )
            except Exception as e:
                rumps.notification(
                    "Impetus Server", 
                    "Load Error", 
                    f"Failed to load {model_id}",
                    sound=True
                )
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def set_performance_mode(self, sender):
        """Set performance mode"""
        self.performance_mode = sender.title
        self.update_performance_mode_menu()
        self.save_preferences()
        
        rumps.notification(
            "Impetus Server", 
            "Performance Mode", 
            f"Switched to {self.performance_mode}",
            sound=False
        )
    
    def set_performance_mode_by_name(self, mode_name):
        """Set performance mode by name"""
        # Create a mock sender object
        class MockSender:
            def __init__(self, title):
                self.title = title
        
        sender = MockSender(mode_name)
        self.set_performance_mode(sender)
    
    def update_performance_mode_menu(self):
        """Update performance mode menu with checkmarks"""
        # Update checkmarks on performance mode menu items
        if hasattr(self, 'performance_menu'):
            # Access menu items through the values() method
            for item in self.performance_menu.values():
                if hasattr(item, 'title') and hasattr(item, 'state'):
                    item.state = (item.title == self.performance_mode)
    
    def update_models_menu(self):
        """Update models menu with checkmarks"""
        if hasattr(self, 'models_menu'):
            # Access menu items through the values() method
            for item in self.models_menu.values():
                if hasattr(item, 'title') and hasattr(item, 'state'):
                    model_name = item.title.split(" (")[0]
                    item.state = (model_name == self.current_model)
    
    @rumps.clicked("Server Stats")
    def show_server_stats(self, _):
        """Show server statistics"""
        if self.server_status != "running":
            rumps.alert("Server Stats", "Server is not running")
            return
        
        try:
            # Get system stats
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            
            # Calculate uptime
            uptime_str = "Unknown"
            if self.start_time:
                uptime = datetime.now() - self.start_time
                hours = int(uptime.total_seconds() // 3600)
                minutes = int((uptime.total_seconds() % 3600) // 60)
                seconds = int(uptime.total_seconds() % 60)
                uptime_str = f"{hours}h {minutes}m {seconds}s"
            
            model_str = self.current_model if self.current_model else "None loaded"
            
            stats_message = f"""CPU Usage: {cpu_percent:.1f}%
Memory: {memory_mb:.1f} MB
Uptime: {uptime_str}
Model: {model_str}
Performance: {self.performance_mode}"""
            
            rumps.alert("Server Statistics", stats_message)
            
        except Exception as e:
            rumps.alert("Server Stats", f"Error getting stats: {str(e)}")
    
    @rumps.clicked("View Logs")
    def view_logs(self, _):
        """View server logs"""
        log_paths = [
            os.path.expanduser("~/Library/Application Support/Impetus/logs/impetus_server.log"),
            os.path.expanduser("~/Library/Logs/Impetus/server.log"),
            "./logs/impetus_server.log",
            "./impetus_server.log"
        ]
        
        log_found = False
        for log_path in log_paths:
            if os.path.exists(log_path):
                subprocess.run(["open", "-a", "Console", log_path])
                log_found = True
                break
        
        if not log_found:
            rumps.alert("Logs", "Log file not found\n\nLogs may not be generated yet.")
    
    @rumps.clicked("Take Tour Again")
    def restart_tour(self, _):
        """Restart the onboarding tour"""
        self.onboarding_tour.restart_tour()
    
    @rumps.clicked("Show Permissions")
    def show_permissions_status(self, _):
        """Show current permissions status"""
        self.permissions_manager.show_permissions_summary()
    
    @rumps.clicked("Setup Permissions")
    def setup_permissions(self, _):
        """Setup permissions"""
        missing = self.permissions_manager.get_missing_permissions()
        if not missing:
            rumps.alert(
                "Permissions",
                "All permissions are properly configured! ✅",
                ok="Great!"
            )
            return
        
        # Show setup options
        response = rumps.alert(
            title="Setup Permissions",
            message="Choose what to set up:\n\n"
                   "• All Permissions - Complete setup\n"
                   "• Individual - Choose specific permissions",
            ok="All Permissions",
            cancel="Individual"
        )
        
        if response == 1:  # All permissions
            self.request_all_permissions()
        else:  # Individual
            self.show_individual_permissions_setup()
    
    def request_all_permissions(self):
        """Request all permissions"""
        for perm_type in ['notifications', 'file_access', 'accessibility']:
            self.permissions_manager.request_permission(
                perm_type, 
                callback=self.permission_callback
            )
    
    def show_individual_permissions_setup(self):
        """Show individual permissions setup"""
        missing = self.permissions_manager.get_missing_permissions()
        
        for perm_type, description in missing.items():
            response = rumps.alert(
                title=f"Setup {perm_type.title()}",
                message=f"Setup {description}?",
                ok="Yes",
                cancel="Skip"
            )
            
            if response == 1:
                self.permissions_manager.request_permission(
                    perm_type,
                    callback=self.permission_callback
                )
    
    @rumps.clicked("About Impetus")
    def show_about(self, _):
        """Show about dialog"""
        about_message = f"""Impetus MLX Server v1.0.0

High-performance local LLM server optimized for Apple Silicon

Features:
• 50-110+ tokens/sec inference with MLX {self.get_mlx_version()}
• OpenAI-compatible API
• Real-time performance monitoring  
• Beautiful dashboard interface
• Multiple model support

© 2024 GerdsenAI
MIT License"""
        
        rumps.alert("About Impetus", about_message)
    
    def get_mlx_version(self):
        """Get MLX version string"""
        try:
            import mlx
            return f"v{mlx.__version__}"
        except:
            return ""
    
    @rumps.clicked("Preferences...")
    def show_preferences(self, _):
        """Show preferences dialog"""
        prefs_message = f"""Current Settings:

Performance Mode: {self.performance_mode}
Server Status: {self.server_status.title()}
Current Model: {self.current_model or 'None'}

Permissions Status:
{self._get_permissions_summary()}

Advanced preferences coming soon!"""
        
        rumps.alert("Preferences", prefs_message)
    
    def _get_permissions_summary(self):
        """Get permissions summary for preferences"""
        permissions = self.permissions_manager.permissions
        notifications = "✅" if permissions.get('notifications', False) else "❌"
        file_access = "✅" if permissions.get('file_access', False) else "❌"
        accessibility = "✅" if permissions.get('accessibility', False) else "⚠️"
        
        return f"• Notifications: {notifications}\n• File Access: {file_access}\n• Accessibility: {accessibility}"
    
    @rumps.clicked("Quit Impetus")
    def quit_application(self, _):
        """Quit the application"""
        if self.server_status == "running":
            response = rumps.alert(
                "Quit Impetus", 
                "The server is still running. Stop it before quitting?",
                ok="Stop & Quit", 
                cancel="Cancel"
            )
            if response == 1:  # OK pressed
                def quit_after_stop():
                    self.stop_server(None)
                    time.sleep(3)  # Wait for server to stop
                    rumps.quit_application()
                
                threading.Thread(target=quit_after_stop, daemon=True).start()
        else:
            rumps.quit_application()
    
    def monitor_server(self):
        """Monitor server health in background"""
        consecutive_failures = 0
        
        while True:
            try:
                if self.server_status == "running":
                    try:
                        response = requests.get("http://localhost:8080/api/health", timeout=5)
                        if response.status_code == 200:
                            consecutive_failures = 0
                            # Keep running status
                        else:
                            consecutive_failures += 1
                    except requests.exceptions.RequestException:
                        consecutive_failures += 1
                    
                    # If multiple failures, mark as error
                    if consecutive_failures >= 3:
                        self.server_status = "error"
                        self.icon = "🔴"
                        self.status_item.title = "Server: Error"
                        if hasattr(self.menu.get("Stop Server", None), 'title'):
                            self.menu["Stop Server"].title = "Start Server"
                        
                        rumps.notification(
                            "Impetus MLX Server", 
                            "Server Error", 
                            "Server appears to have crashed",
                            sound=True
                        )
                        consecutive_failures = 0  # Reset to avoid spam
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(10)


def main():
    """Main entry point"""
    # Ensure we're in the right directory
    project_dir = "/Volumes/M2 Raid0/GerdsenAI_Repositories/Impetus-LLM-Server"
    if os.path.exists(project_dir):
        os.chdir(project_dir)
    
    # Check for single instance
    instance_lock = SingleInstance("impetus_menubar")
    
    if not instance_lock.acquire():
        # Another instance is running
        response = rumps.alert(
            title="Impetus MLX Server Already Running",
            message="Another instance of Impetus MLX Server is already running.\n\n"
                   "Would you like to replace it?",
            ok="Replace",
            cancel="Cancel"
        )
        
        if response == 1:  # Replace
            # Kill all existing menu bar instances
            killed = kill_all_menubar_processes(except_pid=os.getpid())
            time.sleep(1)  # Give time for cleanup
            
            # Force acquire the lock
            if instance_lock.force_acquire():
                print(f"✅ Replaced {killed} existing instance(s)")
            else:
                rumps.alert("Error", "Could not start Impetus MLX Server")
                sys.exit(1)
        else:
            sys.exit(0)
    
    # Start the menu bar app
    try:
        app = ImpetusMenuBar()
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting app: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()