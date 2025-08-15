#!/usr/bin/env python3
"""
Impetus LLM Server Menu Bar Application
macOS native menu bar controller for the Impetus MLX inference server
"""

import rumps
import subprocess
import requests
import json
import os
import psutil
import threading
import time
from datetime import datetime, timedelta

class ImpetusMenuBar(rumps.App):
    def __init__(self):
        super(ImpetusMenuBar, self).__init__("🧠", title="Impetus LLM Server")
        self.server_process = None
        self.server_status = "stopped"
        self.current_model = None
        self.performance_mode = "Balanced Mode"
        self.start_time = None
        
        # Load preferences
        self.preferences_file = os.path.expanduser("~/Library/Preferences/com.gerdsenai.impetus.json")
        self.load_preferences()
        
        # Setup menu
        self.setup_menu()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_server, daemon=True)
        self.monitor_thread.start()
    
    def setup_menu(self):
        """Setup the initial menu structure"""
        self.menu = [
            "Server: Stopped",
            None,  # Separator
            "Start Server",
            None,  # Separator
            "Open Dashboard",
            "API Documentation", 
            None,  # Separator
            {
                "Models": {
                    "Mistral 7B (4-bit) (3.8 GB)": self.load_model,
                    "Llama 3.2 3B (4-bit) (1.8 GB)": self.load_model,
                    "Phi 3.5 Mini (4-bit) (2.2 GB)": self.load_model,
                    "Qwen 2.5 Coder 7B (4-bit) (4.0 GB)": self.load_model,
                    None: None,
                    "Load Custom Model...": self.load_custom_model
                }
            },
            {
                "Performance Mode": {
                    "Efficiency Mode": self.set_performance_mode,
                    "Balanced Mode": self.set_performance_mode,
                    "Performance Mode": self.set_performance_mode
                }
            },
            None,  # Separator
            "Server Stats",
            "View Logs",
            None,  # Separator
            "Preferences...",
            "About Impetus",
            None,  # Separator
            "Quit Impetus"
        ]
        
        # Set initial performance mode checkmark
        self.update_performance_mode_menu()
    
    def load_preferences(self):
        """Load preferences from JSON file"""
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    prefs = json.load(f)
                    self.performance_mode = prefs.get('performance_mode', 'Balanced Mode')
        except Exception as e:
            print(f"Error loading preferences: {e}")
    
    def save_preferences(self):
        """Save preferences to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
            prefs = {
                'performance_mode': self.performance_mode
            }
            with open(self.preferences_file, 'w') as f:
                json.dump(prefs, f, indent=2)
        except Exception as e:
            print(f"Error saving preferences: {e}")
    
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
                os.chdir(project_dir)
                
                # Start server process
                self.server_process = subprocess.Popen([
                    "python", "main.py"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
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
                        self.menu["Server: Stopped"].title = "Server: Running"
                        rumps.notification("Impetus Server", "Server Started", "Server is now running on port 8080")
                    else:
                        raise Exception("Server not responding")
                except:
                    self.server_status = "error"
                    self.icon = "🔴"
                    self.menu["Start Server"].title = "Start Server"
                    rumps.notification("Impetus Server", "Start Failed", "Could not start server")
                    
            except Exception as e:
                self.server_status = "error"
                self.icon = "🔴"
                self.menu["Start Server"].title = "Start Server"
                rumps.notification("Impetus Server", "Error", f"Failed to start server: {str(e)}")
        
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
                    self.server_process.wait(timeout=10)
                
                # Also kill any remaining processes
                subprocess.run(["pkill", "-f", "python.*main.py"], capture_output=True)
                
                self.server_status = "stopped"
                self.start_time = None
                self.icon = "🧠"
                self.menu["Stop Server"].title = "Start Server"
                self.menu["Server: Running"].title = "Server: Stopped"
                rumps.notification("Impetus Server", "Server Stopped", "Server has been stopped")
                
            except Exception as e:
                rumps.notification("Impetus Server", "Error", f"Error stopping server: {str(e)}")
        
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
        rumps.notification("Impetus Server", "Loading Model", f"Loading {model_name}...")
        
        # In a real implementation, this would make an API call to load the model
        # For testing, we'll just simulate it
        def load_model_thread():
            time.sleep(2)  # Simulate loading time
            self.current_model = model_name
            self.update_models_menu()
            rumps.notification("Impetus Server", "Model Loaded", f"{model_name} is now active")
        
        threading.Thread(target=load_model_thread, daemon=True).start()
    
    @rumps.clicked("Load Custom Model...")
    def load_custom_model(self, _):
        """Load a custom model"""
        if self.server_status != "running":
            rumps.alert("Server Not Running", "Please start the server first")
            return
        
        rumps.notification("Impetus Server", "Custom Model", "Custom model loading not implemented in test version")
    
    def set_performance_mode(self, sender):
        """Set performance mode"""
        self.performance_mode = sender.title
        self.update_performance_mode_menu()
        self.save_preferences()
        rumps.notification("Impetus Server", "Performance Mode", f"Switched to {self.performance_mode}")
    
    def update_performance_mode_menu(self):
        """Update performance mode menu with checkmarks"""
        for mode in ["Efficiency Mode", "Balanced Mode", "Performance Mode"]:
            if mode == self.performance_mode:
                self.menu["Performance Mode"][mode].state = 1
            else:
                self.menu["Performance Mode"][mode].state = 0
    
    def update_models_menu(self):
        """Update models menu with checkmarks"""
        for item in self.menu["Models"]:
            if hasattr(self.menu["Models"][item], 'state'):
                model_name = item.split(" (")[0]
                if model_name == self.current_model:
                    self.menu["Models"][item].state = 1
                else:
                    self.menu["Models"][item].state = 0
    
    @rumps.clicked("Server Stats")
    def show_server_stats(self, _):
        """Show server statistics"""
        if self.server_status != "running":
            rumps.alert("Server Stats", "Server is not running")
            return
        
        # Get system stats
        cpu_percent = psutil.cpu_percent(interval=1)
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
Model: {model_str}"""
        
        rumps.alert("Server Statistics", stats_message)
    
    @rumps.clicked("View Logs")
    def view_logs(self, _):
        """View server logs"""
        log_path = os.path.expanduser("~/Library/Application Support/Impetus/logs/impetus_server.log")
        if os.path.exists(log_path):
            subprocess.run(["open", "-a", "Console", log_path])
        else:
            rumps.alert("Logs", "Log file not found")
    
    @rumps.clicked("Preferences...")
    def show_preferences(self, _):
        """Show preferences dialog"""
        rumps.alert("Preferences", "Preferences dialog not implemented in test version")
    
    @rumps.clicked("About Impetus")
    def show_about(self, _):
        """Show about dialog"""
        rumps.alert("About Impetus", 
                   "Impetus LLM Server\nVersion 0.1.0\n\nHigh-performance local LLM server\noptimized for Apple Silicon\n\nGerdsenAI")
    
    @rumps.clicked("Quit Impetus")
    def quit_application(self, _):
        """Quit the application"""
        if self.server_status == "running":
            response = rumps.alert("Quit Impetus", 
                                 "The server is still running. Stop it before quitting?",
                                 ok="Stop & Quit", cancel="Cancel")
            if response == 1:  # OK pressed
                self.stop_server(None)
                time.sleep(2)  # Wait for server to stop
                rumps.quit_application()
        else:
            rumps.quit_application()
    
    def monitor_server(self):
        """Monitor server health in background"""
        while True:
            try:
                if self.server_status == "running":
                    try:
                        response = requests.get("http://localhost:8080/api/health", timeout=5)
                        if response.status_code != 200:
                            raise Exception("Server not responding")
                    except:
                        # Server appears to have crashed
                        self.server_status = "error"
                        self.icon = "🔴"
                        self.menu["Server: Running"].title = "Server: Error"
                        if hasattr(self.menu, "Stop Server"):
                            self.menu["Stop Server"].title = "Start Server"
                        rumps.notification("Impetus Server", "Server Error", "Server appears to have crashed")
                
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    # Ensure we're in the right directory
    project_dir = "/Volumes/M2 Raid0/GerdsenAI_Repositories/Impetus-LLM-Server"
    if os.path.exists(project_dir):
        os.chdir(project_dir)
    
    # Start the menu bar app
    app = ImpetusMenuBar()
    app.run()
