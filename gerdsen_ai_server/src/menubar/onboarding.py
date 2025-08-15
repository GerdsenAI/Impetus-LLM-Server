#!/usr/bin/env python3
"""
Onboarding Tour for Impetus Menu Bar Application
Provides a guided tour for first-time users
"""

import os
import json
import time
import threading
import rumps
from typing import Optional, Callable, Dict, Any


class OnboardingTour:
    """Manages the first-run onboarding experience"""
    
    def __init__(self, preferences_file: str, app_instance=None):
        self.preferences_file = preferences_file
        self.app_instance = app_instance
        self.tour_completed = False
        self.current_step = 0
        self.tour_steps = []
        self.completion_callback: Optional[Callable] = None
        
        # Load tour status
        self.load_tour_status()
        
        # Define tour steps
        self.setup_tour_steps()
    
    def load_tour_status(self):
        """Load tour completion status from preferences"""
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    prefs = json.load(f)
                    self.tour_completed = prefs.get('onboarding_completed', False)
        except Exception as e:
            print(f"Error loading tour status: {e}")
            self.tour_completed = False
    
    def save_tour_status(self):
        """Save tour completion status to preferences"""
        try:
            # Load existing preferences
            prefs = {}
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    prefs = json.load(f)
            
            # Update tour status
            prefs['onboarding_completed'] = self.tour_completed
            
            # Save back to file
            os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
            with open(self.preferences_file, 'w') as f:
                json.dump(prefs, f, indent=2)
        except Exception as e:
            print(f"Error saving tour status: {e}")
    
    def is_first_run(self) -> bool:
        """Check if this is the first run of the application"""
        return not self.tour_completed
    
    def setup_tour_steps(self):
        """Define the tour steps"""
        self.tour_steps = [
            {
                "title": "Welcome to Impetus! 🧠",
                "message": "Welcome to Impetus LLM Server!\n\n"
                          "Impetus is a high-performance local AI server optimized for Apple Silicon.\n\n"
                          "This quick tour will show you how to use the menu bar app to control your AI server.",
                "action": "welcome",
                "buttons": {"next": "Start Tour", "skip": "Skip Tour"},
                "notification": None
            },
            {
                "title": "Menu Bar Icon",
                "message": "Look for the brain icon (🧠) in your menu bar.\n\n"
                          "This icon shows your server status:\n"
                          "🧠 Server stopped\n"
                          "🟡 Server starting/stopping\n"
                          "🟢 Server running\n"
                          "🔴 Server error\n\n"
                          "Click the icon to access all features!",
                "action": "show_icon",
                "buttons": {"next": "Next", "skip": "Skip Tour"},
                "notification": "Click the brain icon (🧠) in your menu bar to continue"
            },
            {
                "title": "Server Control",
                "message": "Use 'Start Server' to begin serving AI models.\n\n"
                          "When running, you can:\n"
                          "• Access the dashboard in your browser\n"
                          "• Use the OpenAI-compatible API\n"
                          "• Load different AI models\n\n"
                          "Try starting the server now!",
                "action": "server_control",
                "buttons": {"next": "Next", "skip": "Skip Tour"},
                "notification": "Try clicking 'Start Server' to see it in action"
            },
            {
                "title": "Model Management",
                "message": "The 'Models' menu lets you:\n\n"
                          "• Load different AI models\n"
                          "• Switch between models instantly\n"
                          "• See model sizes and specs\n"
                          "• Load custom models\n\n"
                          "Models are automatically downloaded when needed.",
                "action": "model_management",
                "buttons": {"next": "Next", "skip": "Skip Tour"},
                "notification": "Explore the Models menu to see available AI models"
            },
            {
                "title": "Performance Modes",
                "message": "Optimize performance for your needs:\n\n"
                          "• Efficiency Mode - Lower power, longer battery\n"
                          "• Balanced Mode - Good performance and efficiency\n"
                          "• Performance Mode - Maximum speed\n\n"
                          "Your preference is saved automatically.",
                "action": "performance_modes",
                "buttons": {"next": "Next", "skip": "Skip Tour"},
                "notification": "Try switching performance modes to see the difference"
            },
            {
                "title": "Dashboard & API",
                "message": "Access your tools:\n\n"
                          "• Dashboard - Beautiful web interface for testing\n"
                          "• API Documentation - Complete API reference\n"
                          "• Server Stats - Monitor CPU, memory, and uptime\n\n"
                          "Everything opens in your browser automatically.",
                "action": "integrations",
                "buttons": {"next": "Next", "skip": "Skip Tour"},
                "notification": "Try 'Open Dashboard' to see the web interface"
            },
            {
                "title": "You're All Set! 🎉",
                "message": "Congratulations! You're ready to use Impetus.\n\n"
                          "Key features:\n"
                          "✅ High-performance local AI\n"
                          "✅ OpenAI-compatible API\n"
                          "✅ Easy model switching\n"
                          "✅ Beautiful dashboard\n"
                          "✅ Apple Silicon optimized\n\n"
                          "Start your server and begin using AI locally!",
                "action": "completion",
                "buttons": {"finish": "Get Started!", "help": "Need Help?"},
                "notification": "Welcome to Impetus! Start your server to begin."
            }
        ]
    
    def start_tour(self, completion_callback: Optional[Callable] = None):
        """Start the onboarding tour"""
        if self.tour_completed:
            print("Tour already completed")
            return False
        
        self.completion_callback = completion_callback
        self.current_step = 0
        
        # Start with welcome step
        self.show_current_step()
        return True
    
    def show_current_step(self):
        """Show the current tour step"""
        if self.current_step >= len(self.tour_steps):
            self.complete_tour()
            return
        
        step = self.tour_steps[self.current_step]
        
        # Show the main dialog
        self.show_step_dialog(step)
    
    def show_step_dialog(self, step: Dict[str, Any]):
        """Show a dialog for the current step"""
        try:
            title = step["title"]
            message = step["message"]
            buttons = step["buttons"]
            
            # Determine button configuration
            if "next" in buttons and "skip" in buttons:
                response = rumps.alert(
                    title=title,
                    message=message,
                    ok=buttons["next"],
                    cancel=buttons["skip"]
                )
                
                if response == 1:  # Next button
                    self.next_step()
                else:  # Skip button
                    self.skip_tour()
                    
            elif "finish" in buttons and "help" in buttons:
                response = rumps.alert(
                    title=title,
                    message=message,
                    ok=buttons["finish"],
                    cancel=buttons["help"]
                )
                
                if response == 1:  # Finish button
                    self.complete_tour()
                else:  # Help button
                    self.show_help()
                    self.complete_tour()
                    
            else:
                # Single button
                button_text = list(buttons.values())[0]
                rumps.alert(title=title, message=message, ok=button_text)
                self.next_step()
            
            # Show notification if specified
            if step.get("notification"):
                rumps.notification(
                    title="Impetus Tour",
                    subtitle=f"Step {self.current_step + 1} of {len(self.tour_steps)}",
                    message=step["notification"],
                    sound=False
                )
                
        except Exception as e:
            print(f"Error showing step dialog: {e}")
            self.next_step()
    
    def next_step(self):
        """Move to the next tour step"""
        self.current_step += 1
        
        # Small delay for better UX
        def delayed_next():
            time.sleep(1)
            self.show_current_step()
        
        threading.Thread(target=delayed_next, daemon=True).start()
    
    def skip_tour(self):
        """Skip the tour"""
        response = rumps.alert(
            title="Skip Tour?",
            message="Are you sure you want to skip the tour?\n\n"
                   "You can always restart it from the Help menu.",
            ok="Skip Tour",
            cancel="Continue Tour"
        )
        
        if response == 1:  # Skip confirmed
            self.complete_tour()
        else:  # Continue tour
            self.show_current_step()
    
    def complete_tour(self):
        """Complete the tour"""
        self.tour_completed = True
        self.save_tour_status()
        
        # Show completion notification
        rumps.notification(
            title="Tour Complete! 🎉",
            subtitle="Impetus is ready to use",
            message="Click the brain icon anytime to access features",
            sound=False
        )
        
        # Call completion callback if set
        if self.completion_callback:
            self.completion_callback()
    
    def show_help(self):
        """Show help information"""
        help_message = """Impetus Help & Resources:

🌐 Dashboard: http://localhost:5173
📚 API Docs: http://localhost:8080/docs
📊 Server Stats: Check the menu for real-time info

💡 Tips:
• Start with a small model like Phi 3.5 Mini
• Use Balanced mode for best experience  
• Check server stats to monitor performance
• The dashboard has a built-in chat interface

Need more help? Check our documentation or GitHub."""
        
        rumps.alert(
            title="Impetus Help",
            message=help_message,
            ok="Got it!"
        )
    
    def restart_tour(self):
        """Restart the tour (useful for help menu)"""
        response = rumps.alert(
            title="Restart Tour?",
            message="This will restart the complete onboarding tour.\n\n"
                   "Are you sure you want to continue?",
            ok="Restart Tour",
            cancel="Cancel"
        )
        
        if response == 1:  # Restart confirmed
            self.tour_completed = False
            self.current_step = 0
            self.start_tour()
    
    def show_welcome(self):
        """Show welcome message without full tour"""
        if not self.tour_completed:
            return  # Don't show if tour hasn't been completed
        
        welcome_msg = """Welcome back to Impetus! 🧠

Your high-performance local AI server is ready.

Quick reminder:
• Click the brain icon for all features
• Start the server to begin using AI
• Check the dashboard for a web interface

Ready to get started?"""
        
        response = rumps.alert(
            title="Welcome to Impetus",
            message=welcome_msg,
            ok="Start Server",
            cancel="Later"
        )
        
        if response == 1 and self.app_instance:
            # Try to start server if app instance available
            try:
                if hasattr(self.app_instance, 'start_server') and callable(self.app_instance.start_server):
                    self.app_instance.start_server(None)
            except:
                pass
    
    def reset_tour_status(self):
        """Reset tour status (for testing)"""
        self.tour_completed = False
        self.current_step = 0
        self.save_tour_status()