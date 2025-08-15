#!/usr/bin/env python3
"""
Onboarding Tour System for Impetus LLM Server
Provides guided introduction to application features
"""

import rumps
import time
import threading
from typing import List, Dict, Callable, Optional

class OnboardingTour:
    """Manages the onboarding tour for new users"""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.current_step = 0
        self.tour_active = False
        self.tour_steps = self._create_tour_steps()
    
    def _create_tour_steps(self) -> List[Dict]:
        """Create the tour steps"""
        return [
            {
                'title': '🎉 Welcome to Impetus!',
                'message': '''Welcome to Impetus LLM Server!

Your personal AI assistant is now running locally on your Mac, powered by Apple Silicon and MLX.

Impetus provides:
• High-performance local LLM inference
• Multiple AI models at your fingertips  
• Privacy-first approach (everything stays local)
• Native macOS integration

Let's take a quick tour to get you started!''',
                'button': 'Start Tour',
                'action': None
            },
            {
                'title': '🧠 Your Menu Bar Control Center',
                'message': '''The brain emoji (🧠) in your menu bar is your control center.

Icon states:
🧠 Server stopped
🟢 Server running  
🟡 Loading/processing
🔴 Error state

Click the brain anytime to access all features. The icon changes color to show you what's happening at a glance.''',
                'button': 'Next',
                'action': 'highlight_menubar'
            },
            {
                'title': '⚡ Server Control',
                'message': '''Start and stop your LLM server with one click.

When you start the server:
• The icon turns green 🟢
• You'll get a notification
• The API becomes available at localhost:8080

The server runs in the background, ready to handle your AI requests instantly.''',
                'button': 'Next',
                'action': 'highlight_server_control'
            },
            {
                'title': '🤖 Model Management',
                'message': '''Choose from multiple pre-configured AI models:

• Mistral 7B - Great for general conversation
• Llama 3.2 3B - Fast and efficient
• Phi 3.5 Mini - Perfect for coding
• Qwen 2.5 Coder - Advanced code generation

Or load your own custom models! All models are optimized for Apple Silicon with MLX.''',
                'button': 'Next',
                'action': 'highlight_models'
            },
            {
                'title': '🚀 Performance Modes',
                'message': '''Optimize performance for your needs:

• Efficiency Mode - Best battery life
• Balanced Mode - Good performance & efficiency  
• Performance Mode - Maximum speed

Your choice is automatically saved and will persist between app restarts.''',
                'button': 'Next',
                'action': 'highlight_performance'
            },
            {
                'title': '🌐 Dashboard & API Access',
                'message': '''Access your LLM server through:

• Web Dashboard - User-friendly interface
• REST API - OpenAI-compatible endpoints
• Swagger Documentation - Complete API reference

Perfect for integrating with other apps or building your own AI-powered tools!''',
                'button': 'Next',
                'action': 'highlight_dashboard'
            },
            {
                'title': '🎯 You\'re All Set!',
                'message': '''Congratulations! You're ready to use Impetus.

Quick tips:
• Server Stats shows CPU, memory, and uptime
• Help menu lets you retake this tour anytime
• Preferences are automatically saved
• Quit dialog prevents accidental server shutdown

Enjoy your local AI assistant! 🚀

Need help? Check the Help menu or visit our documentation.''',
                'button': 'Finish Tour',
                'action': 'complete_tour'
            }
        ]
    
    def start_tour(self, completion_callback=None):
        """Start the onboarding tour"""
        if self.tour_active:
            return
        
        self.tour_active = True
        self.current_step = 0
        self.completion_callback = completion_callback
        self._show_current_step()
    
    def restart_tour(self):
        """Restart the tour from the beginning"""
        response = rumps.alert(
            title="Restart Tour",
            message="Would you like to take the onboarding tour again?\n\nThis will walk you through all the features of Impetus LLM Server.",
            ok="Start Tour",
            cancel="Cancel"
        )
        
        if response == 1:  # OK pressed
            self.start_tour()
    
    def _show_current_step(self):
        """Show the current tour step"""
        if not self.tour_active or self.current_step >= len(self.tour_steps):
            self._complete_tour()
            return
        
        step = self.tour_steps[self.current_step]
        
        # Execute any pre-step action
        if step.get('action') and hasattr(self, f"_action_{step['action']}"):
            getattr(self, f"_action_{step['action']}")()
        
        # Show the step dialog
        response = rumps.alert(
            title=step['title'],
            message=step['message'],
            ok=step['button'],
            cancel="Skip Tour" if self.current_step > 0 else None
        )
        
        if response == 1:  # OK pressed
            self.current_step += 1
            # Small delay for better UX
            threading.Timer(0.5, self._show_current_step).start()
        else:  # Cancel or skip
            self._complete_tour()
    
    def _complete_tour(self):
        """Complete the tour and mark as completed"""
        self.tour_active = False
        self.current_step = 0
        
        # Mark tour as completed in preferences
        if hasattr(self.app, 'save_preference'):
            self.app.save_preference('onboarding_completed', True)
        
        # Call completion callback if provided
        if hasattr(self, 'completion_callback') and self.completion_callback:
            self.completion_callback()
        
        # Show completion notification
        rumps.notification(
            title="Impetus LLM Server",
            subtitle="Tour Complete!",
            message="You're ready to use your local AI assistant. Happy computing! 🎉"
        )
    
    # Tour step actions (visual highlights/guidance)
    
    def _action_highlight_menubar(self):
        """Highlight the menu bar icon"""
        # Since we can't directly highlight, we'll use notification
        rumps.notification(
            title="Look Up! 👆",
            subtitle="Menu Bar Icon",
            message="Find the brain emoji (🧠) in your menu bar at the top of the screen"
        )
    
    def _action_highlight_server_control(self):
        """Highlight server control features"""
        rumps.notification(
            title="Server Control",
            subtitle="Start/Stop Server",
            message="Click the brain icon and look for 'Start Server' option"
        )
    
    def _action_highlight_models(self):
        """Highlight model management"""
        rumps.notification(
            title="AI Models",
            subtitle="Models Submenu",
            message="Click the brain icon → Models to see available AI models"
        )
    
    def _action_highlight_performance(self):
        """Highlight performance modes"""
        rumps.notification(
            title="Performance Modes",
            subtitle="Optimize Settings",
            message="Click the brain icon → Performance Mode to optimize for your needs"
        )
    
    def _action_highlight_dashboard(self):
        """Highlight dashboard access"""
        rumps.notification(
            title="Dashboard & API",
            subtitle="Web Access",
            message="Click the brain icon → Open Dashboard or API Documentation"
        )
    
    def _action_complete_tour(self):
        """Complete the tour"""
        # This is handled by _complete_tour method
        pass
    
    def should_show_tour(self) -> bool:
        """Check if tour should be shown (first run)"""
        if hasattr(self.app, 'get_preference'):
            return not self.app.get_preference('onboarding_completed', False)
        return True
    
    def get_tour_progress(self) -> tuple:
        """Get current tour progress (current_step, total_steps)"""
        return (self.current_step, len(self.tour_steps))
    
    def skip_tour(self):
        """Skip the tour and mark as completed"""
        response = rumps.alert(
            title="Skip Tour",
            message="Are you sure you want to skip the tour?\n\nYou can always restart it later from the Help menu.",
            ok="Skip Tour",
            cancel="Continue Tour"
        )
        
        if response == 1:  # OK pressed
            self._complete_tour()
            return True
        return False
