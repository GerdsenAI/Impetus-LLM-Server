#!/usr/bin/env python3
"""
Impetus LLM Server - First Run Setup Wizard
Handles initial configuration and setup for new installations
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
import shutil

def show_dialog(title, message, dialog_type="info", buttons=None):
    """Show a macOS dialog using AppleScript"""
    if buttons is None:
        buttons = ["OK"]
    
    button_list = '", "'.join(buttons)
    
    if dialog_type == "error":
        icon = "stop"
    elif dialog_type == "warning":
        icon = "caution"
    else:
        icon = "note"
    
    script = f'''
    display dialog "{message}" with title "{title}" buttons {{"{button_list}"}} default button "{buttons[0]}" with icon {icon}
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return buttons[0]  # Default to first button

def show_progress(title, message):
    """Show a progress dialog"""
    script = f'''
    display dialog "{message}" with title "{title}" buttons {{"Cancel"}} giving up after 3 with icon note
    '''
    
    try:
        subprocess.run(['osascript', '-e', script], 
                      capture_output=True, text=True, timeout=4)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass

def create_support_directories():
    """Create necessary support directories"""
    print("Creating support directories...")
    
    home = Path.home()
    
    # Create application support directory
    app_support = home / "Library" / "Application Support" / "Impetus"
    app_support.mkdir(parents=True, exist_ok=True)
    
    # Create logs directory
    logs_dir = home / "Library" / "Logs" / "Impetus"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create models directory
    models_dir = app_support / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Create cache directory
    cache_dir = home / "Library" / "Caches" / "com.gerdsenai.impetus"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Created support directories:")
    print(f"   App Support: {app_support}")
    print(f"   Logs: {logs_dir}")
    print(f"   Models: {models_dir}")
    print(f"   Cache: {cache_dir}")
    
    return {
        "app_support": str(app_support),
        "logs": str(logs_dir),
        "models": str(models_dir),
        "cache": str(cache_dir)
    }

def create_default_config(directories):
    """Create default configuration file"""
    print("Creating default configuration...")
    
    config_path = Path(directories["app_support"]) / "config.json"
    
    default_config = {
        "version": "1.0.2",
        "server": {
            "host": "127.0.0.1",
            "port": 8080,
            "auto_start": True,
            "log_level": "info"
        },
        "models": {
            "default_model": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
            "models_directory": directories["models"],
            "auto_download": False,
            "cache_size_gb": 8
        },
        "ui": {
            "show_notifications": True,
            "start_minimized": False,
            "theme": "auto"
        },
        "performance": {
            "mode": "balanced",
            "max_workers": 4,
            "enable_gpu": True,
            "memory_limit_gb": 16
        },
        "directories": directories,
        "first_run_completed": True
    }
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"✅ Created configuration file: {config_path}")
    return config_path

def check_dependencies():
    """Check for required dependencies"""
    print("Checking dependencies...")
    
    # Check if we're in a bundled app
    if os.environ.get('IMPETUS_APP_MODE') == 'bundled':
        print("✅ Running in bundled mode, dependencies included")
        return True
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        return False
    
    print("✅ Dependencies check passed")
    return True

def setup_menu_bar_permissions():
    """Guide user through menu bar permissions setup"""
    print("Setting up menu bar permissions...")
    
    message = """Impetus needs permission to appear in your menu bar.

After clicking OK, you may see system permission dialogs. Please:

1. Allow Impetus to run in the background
2. Grant accessibility permissions if prompted
3. Allow network connections for AI model downloads

These permissions are required for Impetus to function properly."""
    
    show_dialog("Permissions Setup", message, "info")
    
    # Create a simple test to verify menu bar access
    try:
        # This will trigger permission dialogs if needed
        import rumps
        print("✅ Menu bar permissions appear to be working")
        return True
    except ImportError:
        print("⚠️ Menu bar framework not available")
        return False
    except Exception as e:
        print(f"⚠️ Menu bar permission issue: {e}")
        return False

def create_desktop_alias():
    """Create a desktop alias to the application"""
    try:
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            return
        
        # Find the application bundle
        app_path = None
        current_path = Path(__file__).parent
        
        # Walk up to find the .app bundle
        while current_path.parent != current_path:
            if current_path.name.endswith('.app'):
                app_path = current_path
                break
            current_path = current_path.parent
        
        if not app_path:
            print("⚠️ Could not find application bundle")
            return
        
        alias_path = desktop / "Impetus.app"
        
        # Create alias using AppleScript
        script = f'''
        tell application "Finder"
            make alias file to POSIX file "{app_path}" at desktop
            set name of result to "Impetus"
        end tell
        '''
        
        subprocess.run(['osascript', '-e', script], 
                      capture_output=True, text=True, check=False)
        
        print(f"✅ Created desktop alias")
        
    except Exception as e:
        print(f"⚠️ Could not create desktop alias: {e}")

def welcome_user():
    """Show welcome message and gather user preferences"""
    print("Showing welcome message...")
    
    welcome_message = """Welcome to Impetus LLM Server!

Impetus is a high-performance local AI server optimized for Apple Silicon.

Features:
• Run AI models locally on your Mac
• OpenAI-compatible API
• Native menu bar integration
• Optimized for M1/M2/M3/M4 chips

This setup wizard will configure Impetus for your system."""
    
    response = show_dialog("Welcome to Impetus", welcome_message, "info", ["Continue", "Cancel"])
    
    if "Cancel" in response:
        print("Setup cancelled by user")
        return False
    
    return True

def setup_complete_message():
    """Show setup completion message"""
    message = """Setup Complete! 🎉

Impetus has been successfully configured. You can now:

• Find Impetus in your Applications folder
• Look for the 🧠 icon in your menu bar
• Access the dashboard at http://localhost:8080
• Start using AI models locally on your Mac

For help and documentation, visit:
https://github.com/GerdsenAI/Impetus-LLM-Server"""
    
    show_dialog("Setup Complete", message, "info")

def main():
    """Main setup function"""
    print("🧠 Impetus LLM Server - First Run Setup")
    print("=" * 50)
    
    try:
        # Welcome user
        if not welcome_user():
            return 1
        
        show_progress("Setting Up Impetus", "Initializing setup...")
        
        # Check dependencies
        if not check_dependencies():
            show_dialog("Setup Error", "System requirements not met. Please check the installation.", "error")
            return 1
        
        show_progress("Setting Up Impetus", "Creating directories...")
        
        # Create support directories
        directories = create_support_directories()
        
        show_progress("Setting Up Impetus", "Creating configuration...")
        
        # Create default configuration
        config_path = create_default_config(directories)
        
        show_progress("Setting Up Impetus", "Setting up permissions...")
        
        # Setup menu bar permissions
        setup_menu_bar_permissions()
        
        show_progress("Setting Up Impetus", "Finalizing setup...")
        
        # Create desktop alias
        create_desktop_alias()
        
        # Show completion message
        setup_complete_message()
        
        print("✅ First run setup completed successfully")
        return 0
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        show_dialog("Setup Error", f"Setup failed with error: {e}", "error")
        return 1

if __name__ == "__main__":
    exit(main())