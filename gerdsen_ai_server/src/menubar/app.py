#!/usr/bin/env python3
"""
Impetus Menu Bar Application
A native macOS menu bar app for managing the Impetus LLM Server
"""

import rumps
import webbrowser
import threading
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from .config import (
    APP_NAME, APP_VERSION, API_BASE_URL,
    ICON_IDLE, ICON_ACTIVE, ICON_ERROR, ICON_LOADING,
    DEFAULT_MODELS, PERFORMANCE_MODES,
    ensure_directories, PREFERENCES_FILE, LOGS_DIR
)
from .server_manager import ServerManager


class ImpetusMenuBarApp(rumps.App):
    """Main menu bar application for Impetus"""
    
    def __init__(self):
        super().__init__(
            name=APP_NAME,
            title=ICON_IDLE,
            quit_button=None  # We'll add a custom quit handler
        )
        
        # Ensure directories exist
        ensure_directories()
        
        # Initialize server manager
        self.server_manager = ServerManager(status_callback=self.update_status)
        
        # State tracking
        self.server_running = False
        self.current_model = None
        self.performance_mode = "balanced"
        
        # Load preferences
        self.load_preferences()
        
        # Create menu items
        self.setup_menu()
        
        # Start status monitoring
        self.start_monitoring()
    
    def setup_menu(self):
        """Set up the menu bar items"""
        
        # Server status
        self.status_item = rumps.MenuItem("Server: Stopped", callback=None)
        self.status_item.set_callback(None)  # Make it non-clickable
        
        # Start/Stop server
        self.toggle_server = rumps.MenuItem(
            "Start Server",
            callback=self.toggle_server_callback
        )
        
        # Dashboard
        self.dashboard_item = rumps.MenuItem(
            "Open Dashboard",
            callback=self.open_dashboard
        )
        
        # API Documentation
        self.api_docs_item = rumps.MenuItem(
            "API Documentation",
            callback=self.open_api_docs
        )
        
        # Model management submenu
        self.models_menu = rumps.MenuItem("Models")
        self.update_models_menu()
        
        # Performance mode submenu
        self.performance_menu = rumps.MenuItem("Performance Mode")
        for mode_id, mode_name in PERFORMANCE_MODES.items():
            item = rumps.MenuItem(
                mode_name,
                callback=lambda sender, mode=mode_id: self.set_performance_mode(mode)
            )
            if mode_id == self.performance_mode:
                item.state = True
            self.performance_menu.add(item)
        
        # Server stats
        self.stats_item = rumps.MenuItem(
            "Server Stats",
            callback=self.show_stats
        )
        
        # Logs
        self.logs_item = rumps.MenuItem(
            "View Logs",
            callback=self.open_logs
        )
        
        # Preferences
        self.preferences_item = rumps.MenuItem(
            "Preferences...",
            callback=self.show_preferences
        )
        
        # About
        self.about_item = rumps.MenuItem(
            f"About {APP_NAME}",
            callback=self.show_about
        )
        
        # Quit
        self.quit_item = rumps.MenuItem(
            f"Quit {APP_NAME}",
            callback=self.quit_application
        )
        
        # Build menu
        self.menu = [
            self.status_item,
            rumps.separator,
            self.toggle_server,
            rumps.separator,
            self.dashboard_item,
            self.api_docs_item,
            rumps.separator,
            self.models_menu,
            self.performance_menu,
            rumps.separator,
            self.stats_item,
            self.logs_item,
            rumps.separator,
            self.preferences_item,
            self.about_item,
            rumps.separator,
            self.quit_item
        ]
    
    def update_models_menu(self):
        """Update the models submenu"""
        # Clear existing items if menu is initialized
        if hasattr(self.models_menu, '_menu') and self.models_menu._menu:
            self.models_menu.clear()
        
        # Current model indicator
        if self.current_model:
            current_item = rumps.MenuItem(f"Current: {self.current_model}")
            current_item.set_callback(None)
            self.models_menu.add(current_item)
            self.models_menu.add(rumps.separator)
        
        # Available models
        for model_info in DEFAULT_MODELS:
            model_id = model_info["id"]
            model_name = model_info["name"]
            size = model_info["size_gb"]
            
            item_title = f"{model_name} ({size:.1f} GB)"
            item = rumps.MenuItem(
                item_title,
                callback=lambda sender, mid=model_id: self.load_model(mid)
            )
            
            # Mark current model
            if model_id == self.current_model:
                item.state = True
            
            self.models_menu.add(item)
        
        # Add custom model option
        self.models_menu.add(rumps.separator)
        self.models_menu.add(rumps.MenuItem(
            "Load Custom Model...",
            callback=self.load_custom_model
        ))
    
    def toggle_server_callback(self, sender):
        """Toggle server on/off"""
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()
    
    def start_server(self):
        """Start the server"""
        self.update_icon(ICON_LOADING)
        self.toggle_server.title = "Starting..."
        
        # Start in background thread
        def start_thread():
            if self.server_manager.start_server():
                rumps.notification(
                    title=APP_NAME,
                    subtitle="Server Started",
                    message="Impetus server is now running",
                    sound=False
                )
                self.server_running = True
                self.toggle_server.title = "Stop Server"
                self.update_icon(ICON_ACTIVE)
                
                # Auto-open dashboard on start
                if self.preferences.get("auto_open_dashboard", True):
                    self.open_dashboard(None)
            else:
                rumps.notification(
                    title=APP_NAME,
                    subtitle="Failed to Start",
                    message="Check logs for details",
                    sound=True
                )
                self.toggle_server.title = "Start Server"
                self.update_icon(ICON_ERROR)
        
        threading.Thread(target=start_thread, daemon=True).start()
    
    def stop_server(self):
        """Stop the server"""
        self.update_icon(ICON_LOADING)
        self.toggle_server.title = "Stopping..."
        
        def stop_thread():
            if self.server_manager.stop_server():
                rumps.notification(
                    title=APP_NAME,
                    subtitle="Server Stopped",
                    message="Impetus server has been stopped",
                    sound=False
                )
                self.server_running = False
                self.toggle_server.title = "Start Server"
                self.update_icon(ICON_IDLE)
                self.current_model = None
                self.update_models_menu()
            else:
                rumps.notification(
                    title=APP_NAME,
                    subtitle="Failed to Stop",
                    message="Server may still be running",
                    sound=True
                )
                self.update_icon(ICON_ERROR)
        
        threading.Thread(target=stop_thread, daemon=True).start()
    
    def load_model(self, model_id: str):
        """Load a specific model"""
        if not self.server_running:
            rumps.alert(
                title="Server Not Running",
                message="Please start the server first",
                ok="OK"
            )
            return
        
        rumps.notification(
            title=APP_NAME,
            subtitle="Loading Model",
            message=f"Loading {model_id}...",
            sound=False
        )
        
        def load_thread():
            if self.server_manager.load_model(model_id):
                self.current_model = model_id
                self.update_models_menu()
                rumps.notification(
                    title=APP_NAME,
                    subtitle="Model Loaded",
                    message=f"{model_id} is ready",
                    sound=False
                )
            else:
                rumps.notification(
                    title=APP_NAME,
                    subtitle="Failed to Load Model",
                    message=f"Could not load {model_id}",
                    sound=True
                )
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def load_custom_model(self, sender):
        """Load a custom model by ID"""
        response = rumps.Window(
            title="Load Custom Model",
            message="Enter the Hugging Face model ID:",
            default_text="mlx-community/",
            ok="Load",
            cancel="Cancel",
            dimensions=(320, 100)
        ).run()
        
        if response.clicked:
            model_id = response.text.strip()
            if model_id:
                self.load_model(model_id)
    
    def set_performance_mode(self, mode: str):
        """Set the performance mode"""
        self.performance_mode = mode
        
        # Update menu checkmarks
        for item in self.performance_menu.values():
            item.state = False
        
        # Set checkmark on selected mode
        for item in self.performance_menu.values():
            if PERFORMANCE_MODES.get(mode) in item.title:
                item.state = True
                break
        
        # Apply to server if running
        if self.server_running:
            # Would need to implement this in server_manager
            pass
        
        # Save preference
        self.save_preferences()
        
        rumps.notification(
            title=APP_NAME,
            subtitle="Performance Mode",
            message=f"Set to {PERFORMANCE_MODES[mode]}",
            sound=False
        )
    
    def open_dashboard(self, sender):
        """Open the dashboard in browser"""
        dashboard_url = "http://localhost:5173"
        webbrowser.open(dashboard_url)
    
    def open_api_docs(self, sender):
        """Open API documentation"""
        docs_url = f"{API_BASE_URL}/docs"
        webbrowser.open(docs_url)
    
    def show_stats(self, sender):
        """Show server statistics"""
        if not self.server_running:
            rumps.alert(
                title="Server Stats",
                message="Server is not running",
                ok="OK"
            )
            return
        
        stats = self.server_manager.get_server_stats()
        
        if "error" in stats:
            message = "Unable to get stats: " + stats["error"]
        else:
            cpu = stats.get("cpu_percent", 0)
            memory = stats.get("memory_mb", 0)
            uptime = stats.get("uptime", 0)
            
            # Format uptime
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)
            uptime_str = f"{hours}h {minutes}m {seconds}s"
            
            message = (
                f"CPU Usage: {cpu:.1f}%\n"
                f"Memory: {memory:.1f} MB\n"
                f"Uptime: {uptime_str}\n"
                f"Model: {self.current_model or 'None loaded'}"
            )
        
        rumps.alert(
            title="Server Statistics",
            message=message,
            ok="OK"
        )
    
    def open_logs(self, sender):
        """Open the logs folder"""
        subprocess.run(["open", str(LOGS_DIR)])
    
    def show_preferences(self, sender):
        """Show preferences dialog"""
        # For now, just show current settings
        message = (
            f"Performance Mode: {PERFORMANCE_MODES[self.performance_mode]}\n"
            f"Auto-open Dashboard: {'Yes' if self.preferences.get('auto_open_dashboard', True) else 'No'}\n"
            f"API Endpoint: {API_BASE_URL}\n\n"
            "Full preferences UI coming soon!"
        )
        
        rumps.alert(
            title="Preferences",
            message=message,
            ok="OK"
        )
    
    def show_about(self, sender):
        """Show about dialog"""
        message = (
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "High-performance local LLM inference server\n"
            "Optimized for Apple Silicon\n\n"
            "• 50-110 tokens/sec inference\n"
            "• OpenAI-compatible API\n"
            "• MLX acceleration\n"
            "• Real-time monitoring\n\n"
            "© 2024 GerdsenAI"
        )
        
        rumps.alert(
            title=f"About {APP_NAME}",
            message=message,
            ok="OK"
        )
    
    def quit_application(self, sender):
        """Quit the application"""
        if self.server_running:
            response = rumps.alert(
                title="Quit Impetus",
                message="The server is still running. Stop it before quitting?",
                ok="Stop & Quit",
                cancel="Cancel"
            )
            
            if response == 1:  # OK clicked
                self.server_manager.stop_server()
                rumps.quit_application()
        else:
            rumps.quit_application()
    
    def update_status(self, status: str):
        """Update status from server manager callback"""
        status_messages = {
            "starting": "Server: Starting...",
            "running": "Server: Running",
            "stopping": "Server: Stopping...",
            "stopped": "Server: Stopped",
            "error": "Server: Error"
        }
        
        self.status_item.title = status_messages.get(status, f"Server: {status}")
        
        # Update icon based on status
        icon_map = {
            "starting": ICON_LOADING,
            "running": ICON_ACTIVE,
            "stopping": ICON_LOADING,
            "stopped": ICON_IDLE,
            "error": ICON_ERROR
        }
        
        icon = icon_map.get(status, ICON_IDLE)
        self.update_icon(icon)
    
    def update_icon(self, icon: str):
        """Update the menu bar icon"""
        self.title = icon
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        def monitor_thread():
            import time
            while True:
                if self.server_running:
                    # Check if server is still healthy
                    if not self.server_manager.check_health():
                        self.update_status("error")
                    
                    # Check loaded models
                    models = self.server_manager.get_loaded_models()
                    if models and models[0] != self.current_model:
                        self.current_model = models[0] if models else None
                        self.update_models_menu()
                
                time.sleep(10)  # Check every 10 seconds
        
        thread = threading.Thread(target=monitor_thread, daemon=True)
        thread.start()
    
    def load_preferences(self):
        """Load user preferences"""
        self.preferences = {}
        
        if PREFERENCES_FILE.exists():
            try:
                # macOS preferences are usually plist, but we'll use JSON for simplicity
                pref_file = PREFERENCES_FILE.with_suffix('.json')
                if pref_file.exists():
                    with open(pref_file) as f:
                        self.preferences = json.load(f)
                        self.performance_mode = self.preferences.get("performance_mode", "balanced")
            except Exception:
                pass
    
    def save_preferences(self):
        """Save user preferences"""
        self.preferences["performance_mode"] = self.performance_mode
        
        try:
            pref_file = PREFERENCES_FILE.with_suffix('.json')
            pref_file.parent.mkdir(parents=True, exist_ok=True)
            with open(pref_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception:
            pass


def main():
    """Main entry point"""
    app = ImpetusMenuBarApp()
    app.run()


if __name__ == "__main__":
    main()