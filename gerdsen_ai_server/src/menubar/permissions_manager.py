#!/usr/bin/env python3
"""
Permissions Manager for Impetus LLM Server
Handles macOS permission requests and guides users to system settings
"""

import os
import subprocess

import rumps


class PermissionsManager:
    """Manages macOS permissions for the Impetus LLM Server"""

    def __init__(self):
        self.permissions_status = {
            'notifications': False,
            'file_access': False,
            'accessibility': False
        }
        self.check_permissions()

    def check_permissions(self) -> dict[str, bool]:
        """Check current permission status"""
        # Check notifications permission
        try:
            result = subprocess.run([
                'osascript', '-e',
                'tell application "System Events" to display notification "Permission Test" with title "Impetus"'
            ], capture_output=True, text=True, timeout=5)
            self.permissions_status['notifications'] = (result.returncode == 0)
        except Exception:
            self.permissions_status['notifications'] = False

        # Check file access (test write to Documents)
        try:
            test_file = os.path.expanduser("~/Documents/.impetus_permission_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            self.permissions_status['file_access'] = True
        except Exception:
            self.permissions_status['file_access'] = False

        # Accessibility is optional - assume false for now
        self.permissions_status['accessibility'] = False

        return self.permissions_status

    def request_permissions(self) -> bool:
        """Request necessary permissions from user"""
        self.show_permissions_intro()

        success_count = 0
        total_permissions = 2  # notifications + file_access (accessibility is optional)

        # Request notifications permission
        if self.request_notifications_permission():
            success_count += 1

        # Request file access permission
        if self.request_file_access_permission():
            success_count += 1

        # Optionally request accessibility
        self.offer_accessibility_permission()

        return success_count >= total_permissions

    def show_permissions_intro(self):
        """Show introduction dialog about permissions"""
        message = """Welcome to Impetus LLM Server!

To provide the best experience, Impetus needs a few permissions:

• Notifications: Get updates about server status
• File Access: Save preferences and access models
• Accessibility: Enhanced menu bar interaction (optional)

Let's set these up quickly..."""

        rumps.alert(
            title="Setup Permissions",
            message=message,
            ok="Continue",
            cancel=None
        )

    def request_notifications_permission(self) -> bool:
        """Request notifications permission"""
        message = """Impetus would like to send you notifications about:

• Server start/stop status
• Model loading progress
• Error alerts
• System updates

This helps you stay informed about your LLM server."""

        response = rumps.alert(
            title="Enable Notifications",
            message=message,
            ok="Enable Notifications",
            cancel="Skip"
        )

        if response == 1:  # OK pressed
            # Test notification to trigger permission request
            try:
                subprocess.run([
                    'osascript', '-e',
                    'tell application "System Events" to display notification "Notifications enabled! 🎉" with title "Impetus LLM Server"'
                ], timeout=5)
                self.permissions_status['notifications'] = True
                return True
            except Exception:
                self.open_notifications_settings()
                return False

        return False

    def request_file_access_permission(self) -> bool:
        """Request file access permission"""
        message = """Impetus needs file access to:

• Save your preferences and settings
• Access AI models in your Models folder
• Store logs and cache files
• Create configuration files

This is required for the app to function properly."""

        response = rumps.alert(
            title="Enable File Access",
            message=message,
            ok="Grant Access",
            cancel="Skip"
        )

        if response == 1:  # OK pressed
            # Test file access
            try:
                prefs_dir = os.path.expanduser("~/Library/Preferences")
                test_file = os.path.join(prefs_dir, "com.gerdsenai.impetus.test")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                self.permissions_status['file_access'] = True
                return True
            except Exception:
                self.open_privacy_settings()
                return False

        return False

    def offer_accessibility_permission(self):
        """Offer optional accessibility permission"""
        message = """Optional: Enhanced Menu Bar Access

Accessibility permission enables:
• Smoother menu interactions
• Better keyboard navigation
• Enhanced user experience

This is optional but recommended for the best experience."""

        response = rumps.alert(
            title="Enhanced Access (Optional)",
            message=message,
            ok="Setup Accessibility",
            cancel="Skip for Now"
        )

        if response == 1:  # OK pressed
            self.open_accessibility_settings()

    def open_notifications_settings(self):
        """Open System Preferences to Notifications"""
        rumps.alert(
            title="Enable Notifications",
            message="Please enable notifications for Impetus in System Preferences.\n\nOpening Notifications settings...",
            ok="Continue"
        )
        subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.notifications'])

    def open_privacy_settings(self):
        """Open System Preferences to Privacy & Security"""
        rumps.alert(
            title="Enable File Access",
            message="Please grant file access to Impetus in Privacy & Security settings.\n\nOpening Privacy settings...",
            ok="Continue"
        )
        subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security'])

    def open_accessibility_settings(self):
        """Open System Preferences to Accessibility"""
        rumps.alert(
            title="Setup Accessibility",
            message="To enable enhanced menu bar access:\n\n1. Open Privacy & Security\n2. Go to Accessibility\n3. Add Impetus to the list\n\nOpening Accessibility settings...",
            ok="Continue"
        )
        subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'])

    def show_permissions_status(self):
        """Show current permissions status"""
        self.check_permissions()

        status_text = "Current Permissions Status:\n\n"

        # Notifications
        status_icon = "✅" if self.permissions_status['notifications'] else "❌"
        status_text += f"{status_icon} Notifications: {'Enabled' if self.permissions_status['notifications'] else 'Disabled'}\n"

        # File Access
        status_icon = "✅" if self.permissions_status['file_access'] else "❌"
        status_text += f"{status_icon} File Access: {'Enabled' if self.permissions_status['file_access'] else 'Disabled'}\n"

        # Accessibility
        status_icon = "✅" if self.permissions_status['accessibility'] else "⚪"
        status_text += f"{status_icon} Accessibility: {'Enabled' if self.permissions_status['accessibility'] else 'Optional'}\n"

        if not all([self.permissions_status['notifications'], self.permissions_status['file_access']]):
            status_text += "\n⚠️ Some required permissions are missing."
        else:
            status_text += "\n🎉 All required permissions are enabled!"

        rumps.alert(
            title="Permissions Status",
            message=status_text,
            ok="OK"
        )

    def setup_permissions_dialog(self):
        """Show setup permissions dialog"""
        message = """Setup Missing Permissions

Would you like to open System Preferences to configure the required permissions?

This will help ensure Impetus works properly."""

        response = rumps.alert(
            title="Setup Permissions",
            message=message,
            ok="Open Settings",
            cancel="Later"
        )

        if response == 1:  # OK pressed
            subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security'])

    def has_required_permissions(self) -> bool:
        """Check if all required permissions are granted"""
        self.check_permissions()
        return self.permissions_status['notifications'] and self.permissions_status['file_access']

    def get_permissions_summary(self) -> tuple[int, int]:
        """Get summary of granted permissions (granted, total)"""
        self.check_permissions()
        granted = sum([
            self.permissions_status['notifications'],
            self.permissions_status['file_access'],
            self.permissions_status['accessibility']
        ])
        return granted, 3

    def get_missing_permissions(self) -> dict[str, str]:
        """Get missing permissions with descriptions"""
        self.check_permissions()
        missing = {}

        if not self.permissions_status['notifications']:
            missing['notifications'] = 'Notifications for server status updates'

        if not self.permissions_status['file_access']:
            missing['file_access'] = 'File access for preferences and models'

        if not self.permissions_status['accessibility']:
            missing['accessibility'] = 'Enhanced menu bar interactions (optional)'

        return missing

    def request_permission(self, permission_type: str, callback=None):
        """Request a specific permission"""
        if permission_type == 'notifications':
            success = self.request_notifications_permission()
        elif permission_type == 'file_access':
            success = self.request_file_access_permission()
        elif permission_type == 'accessibility':
            self.offer_accessibility_permission()
            success = True  # Always return True since it's optional
        else:
            success = False

        if callback:
            callback(permission_type, success)

    def show_permissions_summary(self):
        """Show permissions summary dialog"""
        self.show_permissions_status()

    @property
    def permissions(self) -> dict[str, bool]:
        """Get current permissions status"""
        return self.permissions_status.copy()
