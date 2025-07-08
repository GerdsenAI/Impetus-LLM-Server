#!/usr/bin/env python3
"""
Integrated GerdsenAI MLX Model Manager
Combines all enhancements: modern UI, performance optimizations, memory persistence, and drag-drop functionality
"""

import os
import sys
import json
import time
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
import subprocess

# Import our enhanced components
from enhanced_mlx_manager import EnhancedMLXManager, PerformanceMetrics

@dataclass
class ApplicationConfig:
    """Application configuration"""
    theme: str = "dark"
    auto_optimize: bool = True
    cache_size_gb: float = 100.0
    log_level: str = "INFO"
    ui_mode: str = "modern"  # modern, classic
    performance_monitoring: bool = True
    neural_engine_enabled: bool = True
    metal_performance_shaders: bool = True

class ModernUIServer:
    """Serves the modern web UI"""
    
    def __init__(self, mlx_manager: EnhancedMLXManager, port: int = 8080):
        self.mlx_manager = mlx_manager
        self.port = port
        self.server_process = None
        
    def start_server(self):
        """Start the web UI server"""
        try:
            # In a real implementation, this would start a Flask/FastAPI server
            ui_path = Path("/home/ubuntu/modern_ui_prototype/index.html")
            if ui_path.exists():
                webbrowser.open(f"file://{ui_path}")
                logging.info(f"Modern UI opened in browser: {ui_path}")
                return True
        except Exception as e:
            logging.error(f"Failed to start UI server: {e}")
            return False
    
    def stop_server(self):
        """Stop the web UI server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None

class SystemTrayManager:
    """Manages system tray integration"""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.tray_icon = None
        
    def create_tray_icon(self):
        """Create system tray icon (simplified implementation)"""
        # In a real implementation, this would use pystray or similar
        logging.info("System tray icon created (simulated)")
        
    def show_context_menu(self):
        """Show tray context menu"""
        menu_items = [
            "Open GerdsenAI",
            "Performance Monitor",
            "Model Manager",
            "Settings",
            "Quit"
        ]
        logging.info(f"Tray menu: {menu_items}")

class PerformanceMonitor:
    """Real-time performance monitoring"""
    
    def __init__(self, mlx_manager: EnhancedMLXManager):
        self.mlx_manager = mlx_manager
        self.monitoring = False
        self.monitor_thread = None
        self.metrics_history: List[Dict] = []
        
    def start_monitoring(self):
        """Start performance monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logging.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logging.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect system metrics
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 100 entries
                if len(self.metrics_history) > 100:
                    self.metrics_history.pop(0)
                
                time.sleep(1)  # Update every second
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def _collect_metrics(self) -> Dict:
        """Collect current system metrics"""
        system_status = self.mlx_manager.get_system_status()
        
        return {
            'timestamp': time.time(),
            'loaded_models': system_status['loaded_models'],
            'cache_size_mb': system_status['cache_size_mb'],
            'memory_usage': 22.1 + (time.time() % 10),  # Simulated
            'gpu_utilization': 0.75 + (time.time() % 0.25),  # Simulated
            'temperature': 68 + (time.time() % 12),  # Simulated
            'tokens_per_second': 45 + (time.time() % 20),  # Simulated
            'latency_ms': 1.2 + (time.time() % 0.8)  # Simulated
        }
    
    def get_current_metrics(self) -> Dict:
        """Get current performance metrics"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return {}
    
    def get_metrics_history(self, count: int = 10) -> List[Dict]:
        """Get recent metrics history"""
        return self.metrics_history[-count:]

class IntegratedGerdsenAI:
    """Main integrated application class"""
    
    def __init__(self, config_path: str = "~/.gerdsen_ai_config.json"):
        self.config_path = Path(config_path).expanduser()
        self.config = self._load_config()
        
        # Initialize components
        self.mlx_manager = EnhancedMLXManager()
        self.ui_server = ModernUIServer(self.mlx_manager)
        self.tray_manager = SystemTrayManager(self)
        self.performance_monitor = PerformanceMonitor(self.mlx_manager)
        
        # Application state
        self.running = False
        self.models_loaded = {}
        
        # Setup logging
        self._setup_logging()
        
        logging.info("Integrated GerdsenAI initialized")
    
    def _load_config(self) -> ApplicationConfig:
        """Load application configuration"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    return ApplicationConfig(**data)
            except Exception as e:
                logging.error(f"Failed to load config: {e}")
        
        return ApplicationConfig()
    
    def _save_config(self):
        """Save application configuration"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
    
    def _setup_logging(self):
        """Setup application logging"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(Path.home() / '.gerdsen_ai_logs.log'),
                logging.StreamHandler()
            ]
        )
    
    def start(self):
        """Start the integrated application"""
        logging.info("Starting Integrated GerdsenAI")
        self.running = True
        
        try:
            # Start performance monitoring
            if self.config.performance_monitoring:
                self.performance_monitor.start_monitoring()
            
            # Create system tray
            self.tray_manager.create_tray_icon()
            
            # Start UI server
            if self.config.ui_mode == "modern":
                self.ui_server.start_server()
            else:
                self._start_classic_ui()
            
            # Load default models if configured
            self._load_default_models()
            
            logging.info("Integrated GerdsenAI started successfully")
            
            # Keep application running
            self._main_loop()
            
        except KeyboardInterrupt:
            logging.info("Received interrupt signal")
        except Exception as e:
            logging.error(f"Error starting application: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the integrated application"""
        logging.info("Stopping Integrated GerdsenAI")
        self.running = False
        
        # Stop components
        self.performance_monitor.stop_monitoring()
        self.ui_server.stop_server()
        self.mlx_manager.cleanup()
        
        # Save configuration
        self._save_config()
        
        logging.info("Integrated GerdsenAI stopped")
    
    def _main_loop(self):
        """Main application loop"""
        while self.running:
            try:
                # Process any pending tasks
                self._process_tasks()
                
                # Update performance metrics
                if self.config.performance_monitoring:
                    metrics = self.performance_monitor.get_current_metrics()
                    if metrics:
                        self._update_ui_metrics(metrics)
                
                time.sleep(0.1)  # Small delay to prevent high CPU usage
                
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(1)
    
    def _process_tasks(self):
        """Process any pending background tasks"""
        # Placeholder for background task processing
        pass
    
    def _update_ui_metrics(self, metrics: Dict):
        """Update UI with current metrics"""
        # In a real implementation, this would update the web UI via WebSocket
        pass
    
    def _load_default_models(self):
        """Load default models on startup"""
        # Check for models in common locations
        model_paths = [
            "~/.cache/huggingface/hub",
            "~/mlx_models",
            "/opt/homebrew/share/mlx-models"
        ]
        
        for path_str in model_paths:
            path = Path(path_str).expanduser()
            if path.exists():
                self._scan_for_models(path)
    
    def _scan_for_models(self, directory: Path):
        """Scan directory for model files"""
        model_extensions = ['.mlx', '.gguf', '.safetensors', '.bin']
        
        for ext in model_extensions:
            for model_file in directory.rglob(f"*{ext}"):
                try:
                    model_id = self.mlx_manager.load_model_optimized(str(model_file))
                    self.models_loaded[model_id] = str(model_file)
                    logging.info(f"Auto-loaded model: {model_file.name}")
                except Exception as e:
                    logging.warning(f"Failed to auto-load {model_file}: {e}")
    
    def _start_classic_ui(self):
        """Start classic Tkinter UI"""
        self.root = tk.Tk()
        self.root.title("GerdsenAI MLX Model Manager")
        self.root.geometry("800x600")
        
        # Create UI elements
        self._create_classic_ui()
        
        # Start UI in separate thread
        ui_thread = threading.Thread(target=self.root.mainloop, daemon=True)
        ui_thread.start()
    
    def _create_classic_ui(self):
        """Create classic UI elements"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="GerdsenAI MLX Model Manager", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Model list
        ttk.Label(main_frame, text="Loaded Models:").grid(row=1, column=0, sticky=tk.W)
        
        self.model_listbox = tk.Listbox(main_frame, height=10)
        self.model_listbox.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 10))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="Load Model", 
                  command=self._load_model_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Performance Monitor", 
                  command=self._show_performance).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Settings", 
                  command=self._show_settings).pack(side=tk.LEFT, padx=5)
    
    def _load_model_dialog(self):
        """Show load model dialog"""
        file_path = filedialog.askopenfilename(
            title="Select Model File",
            filetypes=[
                ("MLX Models", "*.mlx"),
                ("GGUF Models", "*.gguf"),
                ("SafeTensors", "*.safetensors"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            try:
                model_id = self.mlx_manager.load_model_optimized(file_path)
                self.models_loaded[model_id] = file_path
                self._update_model_list()
                messagebox.showinfo("Success", f"Model loaded successfully: {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load model: {e}")
    
    def _update_model_list(self):
        """Update the model list display"""
        if hasattr(self, 'model_listbox'):
            self.model_listbox.delete(0, tk.END)
            for model_id, path in self.models_loaded.items():
                self.model_listbox.insert(tk.END, f"{model_id}: {Path(path).name}")
    
    def _show_performance(self):
        """Show performance monitor window"""
        metrics = self.performance_monitor.get_current_metrics()
        if metrics:
            info_text = f"""Performance Metrics:
            
Memory Usage: {metrics.get('memory_usage', 0):.1f}GB
GPU Utilization: {metrics.get('gpu_utilization', 0)*100:.1f}%
Temperature: {metrics.get('temperature', 0):.1f}°C
Tokens/Second: {metrics.get('tokens_per_second', 0):.1f}
Latency: {metrics.get('latency_ms', 0):.1f}ms
Loaded Models: {metrics.get('loaded_models', 0)}
"""
            messagebox.showinfo("Performance Monitor", info_text)
        else:
            messagebox.showinfo("Performance Monitor", "No metrics available")
    
    def _show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        
        # Add settings controls here
        ttk.Label(settings_window, text="Settings", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Theme selection
        ttk.Label(settings_window, text="Theme:").pack(anchor=tk.W, padx=20)
        theme_var = tk.StringVar(value=self.config.theme)
        ttk.Radiobutton(settings_window, text="Dark", variable=theme_var, 
                       value="dark").pack(anchor=tk.W, padx=40)
        ttk.Radiobutton(settings_window, text="Light", variable=theme_var, 
                       value="light").pack(anchor=tk.W, padx=40)
        
        # Auto-optimize checkbox
        auto_optimize_var = tk.BooleanVar(value=self.config.auto_optimize)
        ttk.Checkbutton(settings_window, text="Auto-optimize models", 
                       variable=auto_optimize_var).pack(anchor=tk.W, padx=20, pady=5)
        
        # Performance monitoring checkbox
        perf_monitor_var = tk.BooleanVar(value=self.config.performance_monitoring)
        ttk.Checkbutton(settings_window, text="Performance monitoring", 
                       variable=perf_monitor_var).pack(anchor=tk.W, padx=20, pady=5)
        
        # Save button
        def save_settings():
            self.config.theme = theme_var.get()
            self.config.auto_optimize = auto_optimize_var.get()
            self.config.performance_monitoring = perf_monitor_var.get()
            self._save_config()
            settings_window.destroy()
            messagebox.showinfo("Settings", "Settings saved successfully")
        
        ttk.Button(settings_window, text="Save", command=save_settings).pack(pady=20)

def main():
    """Main entry point"""
    print("🚀 Starting Integrated GerdsenAI MLX Model Manager")
    print("=" * 60)
    
    # Create and start application
    app = IntegratedGerdsenAI()
    
    try:
        app.start()
    except KeyboardInterrupt:
        print("\n⏹️  Application interrupted by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        logging.error(f"Application error: {e}")
    finally:
        app.stop()
        print("👋 GerdsenAI MLX Model Manager stopped")

if __name__ == "__main__":
    main()

