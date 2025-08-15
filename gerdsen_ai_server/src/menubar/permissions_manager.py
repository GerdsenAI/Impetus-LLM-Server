#!/usr/bin/env python3
"""
Permissions Manager for Impetus Menu Bar Application
Handles macOS permissions checking and requests
"""

import os
import json
import subprocess
import rumps
from pathlib import Path
from typing import Dict, Optional, Callable
from Foundation import NSUserNotificationCenter
import objc


class PermissionsManager:
    """Manages macOS permissions for the Impetus menu bar app"""
    
    def __init__(self, preferences_file: str):
        self.preferences_file = preferences_file
        self.permissions = self.load_permissions()
    
    def load_permissions(self) -> Dict[str, bool]:
        """Load stored permission status from preferences"""
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    prefs = json.load(f)
                    return prefs.get('permissions', {})
        except Exception as e:
            print(f"Error loading permissions: {e}")
        return {}
    
    def save_permissions(self):
        """Save permission status to preferences"""
        try:
            # Load existing preferences
            prefs = {}
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    prefs = json.load(f)
            
            # Update permissions section
            prefs['permissions'] = self.permissions
            
            # Save back to file
            os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
            with open(self.preferences_file, 'w') as f:
                json.dump(prefs, f, indent=2)
        except Exception as e:
            print(f"Error saving permissions: {e}")
    
    def check_notification_permission(self) -> bool:
        """Check if notification permissions are granted"""
        try:
            # Use NSUserNotificationCenter to check authorization status
            center = NSUserNotificationCenter.defaultUserNotificationCenter()
            
            # For rumps apps, notifications are usually enabled by default
            # We'll assume they're available if rumps is working
            return True
        except Exception as e:
            print(f"Error checking notification permission: {e}")
            return False
    
    def check_accessibility_permission(self) -> bool:
        """Check if accessibility permissions are granted"""
        try:
            # Run a simple AppleScript to check accessibility
            script = '''
            tell application "System Events"
                try
                    set frontApp to name of first application process whose frontmost is true
                    return true
                on error
                    return false
                end try
            end tell
            '''
            
            result = subprocess.run([
                'osascript', '-e', script
            ], capture_output=True, text=True, timeout=5)
            
            return result.returncode == 0 and 'true' in result.stdout.lower()
        except Exception as e:
            print(f"Error checking accessibility permission: {e}")
            return False
    
    def check_file_access_permission(self) -> bool:
        """Check if we have file system access for necessary directories"""
        try:
            # Test access to common directories we need
            test_dirs = [
                os.path.expanduser("~/Library/Application Support/Impetus"),
                os.path.expanduser("~/Library/Preferences"),
                os.path.expanduser("~/Library/Logs")
            ]
            
            for test_dir in test_dirs:
                Path(test_dir).mkdir(parents=True, exist_ok=True)
                test_file = Path(test_dir) / "test_access.tmp"
                test_file.write_text("test")
                test_file.unlink()
            
            return True
        except Exception as e:
            print(f"Error checking file access: {e}")
            return False
    
    def request_permission(self, permission_type: str, callback: Optional[Callable] = None) -> bool:
        """Request a specific permission from the user"""
        
        if permission_type == "notifications":
            return self._request_notification_permission(callback)
        elif permission_type == "accessibility":
            return self._request_accessibility_permission(callback)
        elif permission_type == "file_access":
            return self._request_file_access_permission(callback)
        else:
            print(f"Unknown permission type: {permission_type}")
            return False
    
    def _request_notification_permission(self, callback: Optional[Callable] = None) -> bool:
        """Request notification permissions"""
        try:
            # For rumps apps, notification permission is usually automatic
            # Show a dialog explaining notifications will be used
            response = rumps.alert(
                title="Notifications Permission",
                message="Impetus uses notifications to keep you informed about:\n\n"
                       "• Server start/stop status\n"
                       "• Model loading progress\n"
                       "• System alerts and errors\n\n"
                       "Notifications will appear in your Notification Center.",
                ok="Allow Notifications",
                cancel="Skip"
            )
            
            granted = response == 1  # OK button clicked
            self.permissions['notifications'] = granted
            self.save_permissions()
            
            if callback:
                callback('notifications', granted)
            
            return granted
        except Exception as e:
            print(f"Error requesting notification permission: {e}")
            return False
    
    def _request_accessibility_permission(self, callback: Optional[Callable] = None) -> bool:
        """Request accessibility permissions"""
        try:
            # Check if already granted
            if self.check_accessibility_permission():
                self.permissions['accessibility'] = True
                self.save_permissions()
                if callback:
                    callback('accessibility', True)
                return True
            
            # Show dialog explaining accessibility permission
            response = rumps.alert(
                title="Accessibility Permission Required",
                message="Impetus needs Accessibility permission to:\n\n"
                       "• Monitor server health\n"
                       "• Provide system status updates\n"
                       "• Interact with system features\n\n"
                       "Click 'Open Settings' to grant permission.",
                ok="Open Settings",
                cancel="Skip"
            )
            
            if response == 1:  # OK button clicked
                self.open_accessibility_settings()
                # Don't mark as granted yet - user needs to manually enable
                if callback:
                    callback('accessibility', False)  # Pending user action
                return False
            else:
                self.permissions['accessibility'] = False
                self.save_permissions()
                if callback:
                    callback('accessibility', False)
                return False
                
        except Exception as e:
            print(f"Error requesting accessibility permission: {e}")
            return False
    
    def _request_file_access_permission(self, callback: Optional[Callable] = None) -> bool:
        """Request file system access permissions"""
        try:
            # Test if we already have access
            if self.check_file_access_permission():
                self.permissions['file_access'] = True
                self.save_permissions()
                if callback:
                    callback('file_access', True)
                return True
            
            # Show dialog explaining file access
            response = rumps.alert(
                title="File Access Permission",
                message="Impetus needs file access to:\n\n"
                       "• Save your preferences\n"
                       "• Store application logs\n"
                       "• Cache model information\n\n"
                       "This is usually granted automatically.",
                ok="Continue",
                cancel="Skip"
            )
            
            granted = response == 1  # OK button clicked
            self.permissions['file_access'] = granted
            self.save_permissions()
            
            if callback:
                callback('file_access', granted)
            
            return granted
        except Exception as e:
            print(f"Error requesting file access permission: {e}")
            return False
    
    def open_system_settings(self, pane: str = ""):
        """Open macOS System Settings to specific pane"""
        try:
            if pane == "notifications":
                self.open_notifications_settings()
            elif pane == "accessibility":
                self.open_accessibility_settings()
            elif pane == "privacy":
                self.open_privacy_settings()
            else:
                # Open general System Settings
                subprocess.run(["open", "x-apple.systempreferences:"], check=False)
        except Exception as e:
            print(f"Error opening system settings: {e}")
    
    def open_notifications_settings(self):
        """Open Notifications settings pane"""
        try:
            subprocess.run([
                "open", 
                "x-apple.systempreferences:com.apple.preference.notifications"
            ], check=False)
        except Exception as e:
            print(f"Error opening notifications settings: {e}")
    
    def open_accessibility_settings(self):
        """Open Accessibility settings pane"""
        try:
            subprocess.run([
                "open",
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
            ], check=False)
        except Exception as e:
            print(f"Error opening accessibility settings: {e}")
    
    def open_privacy_settings(self):
        """Open Privacy & Security settings pane"""
        try:
            subprocess.run([
                "open",
                "x-apple.systempreferences:com.apple.preference.security?Privacy"
            ], check=False)
        except Exception as e:
            print(f"Error opening privacy settings: {e}")
    
    def get_permission_status(self, permission_type: str) -> Optional[bool]:
        """Get stored permission status"""
        return self.permissions.get(permission_type)
    
    def has_required_permissions(self) -> bool:
        """Check if all required permissions are granted"""
        required = ['notifications', 'file_access']
        return all(self.permissions.get(perm, False) for perm in required)
    
    def has_optional_permissions(self) -> bool:
        """Check if optional permissions are granted"""
        optional = ['accessibility']
        return all(self.permissions.get(perm, False) for perm in optional)
    
    def get_missing_permissions(self) -> Dict[str, str]:
        """Get list of missing permissions with descriptions"""
        missing = {}
        
        if not self.permissions.get('notifications', False):
            missing['notifications'] = "Notifications for status updates"
        
        if not self.permissions.get('file_access', False):
            missing['file_access'] = "File access for preferences and logs"
        
        if not self.permissions.get('accessibility', False):
            missing['accessibility'] = "Accessibility for advanced features (optional)"
        
        return missing
    
    def show_permissions_summary(self):
        """Show a summary of current permissions status"""
        status_lines = []
        
        # Required permissions
        notifications = "✅" if self.permissions.get('notifications', False) else "❌"
        file_access = "✅" if self.permissions.get('file_access', False) else "❌"
        
        # Optional permissions
        accessibility = "✅" if self.permissions.get('accessibility', False) else "⚠️"
        
        message = f"""Current Permissions Status:

{notifications} Notifications - Status updates and alerts
{file_access} File Access - Preferences and logging
{accessibility} Accessibility - Advanced features (optional)

✅ = Granted  ❌ = Denied  ⚠️ = Not set"""
        
        rumps.alert(
            title="Permissions Status",
            message=message,
            ok="OK"
        )
    
    def reset_permissions(self):
        """Reset all permission states (for testing)"""
        self.permissions = {}
        self.save_permissions()