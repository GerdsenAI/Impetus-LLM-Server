#!/usr/bin/env python3
"""
Simple Menu Bar Test - Testing rumps functionality
"""

import rumps
import time
import threading

class SimpleMenuTest(rumps.App):
    """Simple test of menu bar app"""
    
    def __init__(self):
        super(SimpleMenuTest, self).__init__("🧠", title="Test App")
        self.status = "idle"
        self.setup_menu()
    
    def setup_menu(self):
        """Setup simple menu"""
        self.menu = [
            "Status: Idle",
            None,
            "Test Action",
            None,
            "Quit"
        ]
    
    @rumps.clicked("Test Action")
    def test_action(self, _):
        """Test action"""
        self.status = "working"
        self.menu["Status: Idle"].title = "Status: Working"
        
        def reset_status():
            time.sleep(2)
            self.status = "idle"
            self.menu["Status: Working"].title = "Status: Idle"
        
        threading.Thread(target=reset_status, daemon=True).start()
    
    @rumps.clicked("Quit")
    def quit_app(self, _):
        """Quit app"""
        rumps.quit_application()

if __name__ == "__main__":
    app = SimpleMenuTest()
    print("Starting simple test app...")
    app.run()