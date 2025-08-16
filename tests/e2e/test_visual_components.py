#!/usr/bin/env python3
"""Visual GUI Testing Suite with Screenshots"""

import subprocess
import time
import os
from datetime import datetime
from pathlib import Path

class VisualGUITester:
    def __init__(self):
        self.repo_path = Path('/Volumes/M2 Raid0/GerdsenAI_Repositories/Impetus-LLM-Server')
        self.screenshots_dir = self.repo_path / 'tests' / 'screenshots'
        self.screenshots_dir.mkdir(exist_ok=True)
        
    def log(self, message):
        print(f'[{datetime.now().strftime("%H:%M:%S")}] {message}')
    
    def take_screenshot(self, name, description=''):
        """Take a screenshot with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{timestamp}_{name}.png'
        filepath = self.screenshots_dir / filename
        
        try:
            # Take screenshot of entire screen
            subprocess.run(['screencapture', '-x', str(filepath)], check=True)
            self.log(f'📸 Screenshot: {filename} - {description}')
            return str(filepath)
        except Exception as e:
            self.log(f'❌ Screenshot failed: {e}')
            return None
    
    def take_window_screenshot(self, window_name, save_name):
        """Take screenshot of specific window"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{timestamp}_{save_name}.png'
        filepath = self.screenshots_dir / filename
        
        try:
            # Use AppleScript to focus window and then screenshot
            applescript = f'''
            tell application "System Events"
                set frontmost of first process whose name contains "{window_name}" to true
            end tell
            delay 0.5
            '''
            subprocess.run(['osascript', '-e', applescript])
            time.sleep(0.5)
            
            subprocess.run(['screencapture', '-x', str(filepath)], check=True)
            self.log(f'📸 Window screenshot: {filename} - {window_name}')
            return str(filepath)
        except Exception as e:
            self.log(f'❌ Window screenshot failed: {e}')
            return None
    
    def check_menubar_app(self):
        """Check if menu bar app is running and take screenshots"""
        self.log('🔍 Testing Menu Bar Application...')
        
        # Check if Python process is running (menu bar app)
        try:
            result = subprocess.run(['pgrep', '-f', 'run_menubar.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log('✅ Menu bar app process found')
                
                # Take screenshot of desktop with menu bar
                self.take_screenshot('menubar_desktop', 'Desktop with menu bar app')
                
                # Try to click on menu bar item (this is tricky)
                try:
                    applescript = '''
                    tell application "System Events"
                        tell process "Python"
                            click menu bar item 1 of menu bar 1
                        end tell
                    end tell
                    '''
                    subprocess.run(['osascript', '-e', applescript], timeout=5)
                    time.sleep(1)
                    self.take_screenshot('menubar_menu_open', 'Menu bar menu opened')
                    
                    # Click elsewhere to close menu
                    applescript_close = '''
                    tell application "System Events"
                        key code 53  -- ESC key
                    end tell
                    '''
                    subprocess.run(['osascript', '-e', applescript_close])
                    
                except Exception as e:
                    self.log(f'⚠️  Could not interact with menu bar: {e}')
                
                return True
            else:
                self.log('❌ Menu bar app not running')
                return False
                
        except Exception as e:
            self.log(f'❌ Error checking menu bar app: {e}')
            return False
    
    def check_dashboard(self):
        """Check dashboard availability and take screenshots"""
        self.log('🔍 Testing Dashboard Interface...')
        
        # Try to open dashboard in browser
        try:
            import requests
            response = requests.get('http://localhost:5173', timeout=5)
            if response.status_code == 200:
                self.log('✅ Dashboard is responding')
                
                # Open dashboard in browser for screenshot
                subprocess.run(['open', 'http://localhost:5173'])
                time.sleep(5)  # Wait for page to load
                
                # Take screenshot of browser
                self.take_window_screenshot('Brave', 'dashboard_browser')
                self.take_window_screenshot('Safari', 'dashboard_safari')
                self.take_window_screenshot('Chrome', 'dashboard_chrome')
                
                return True
            else:
                self.log(f'❌ Dashboard returned {response.status_code}')
                return False
                
        except Exception as e:
            self.log(f'❌ Dashboard not available: {e}')
            return False
    
    def check_terminal_output(self):
        """Check and screenshot terminal windows"""
        self.log('🔍 Capturing Terminal Output...')
        
        # Take screenshot of any open terminal windows
        self.take_window_screenshot('Terminal', 'terminal_output')
        self.take_window_screenshot('iTerm', 'iterm_output')
        
        # Check for server logs
        try:
            log_files = [
                '~/Library/Application Support/Impetus/logs/impetus_server.log',
                self.repo_path / 'server.log',
                self.repo_path / 'nohup.out'
            ]
            
            for log_file in log_files:
                if isinstance(log_file, str):
                    log_path = Path(log_file).expanduser()
                else:
                    log_path = log_file
                    
                if log_path.exists():
                    self.log(f'📄 Found log file: {log_path}')
                    # Read last 20 lines
                    try:
                        with open(log_path, 'r') as f:
                            lines = f.readlines()
                            recent_lines = lines[-20:] if len(lines) > 20 else lines
                            
                        # Save recent logs to screenshot directory
                        log_summary_file = self.screenshots_dir / f'recent_logs_{log_path.name}.txt'
                        with open(log_summary_file, 'w') as f:
                            f.write(f'Recent logs from {log_path}
')
                            f.write('=' * 50 + '
')
                            f.writelines(recent_lines)
                            
                        self.log(f'📝 Saved recent logs to {log_summary_file}')
                        
                    except Exception as e:
                        self.log(f'⚠️  Could not read log file {log_path}: {e}')
                        
        except Exception as e:
            self.log(f'❌ Error checking logs: {e}')
    
    def test_system_state(self):
        """Test and document system state"""
        self.log('🔍 Testing System State...')
        
        system_info = {}
        
        # Check Python processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            python_processes = [line for line in result.stdout.split('
') 
                              if 'python' in line.lower() and ('impetus' in line or 'main.py' in line or 'menubar' in line)]
            
            system_info['python_processes'] = python_processes
            self.log(f'🐍 Found {len(python_processes)} relevant Python processes')
            
        except Exception as e:
            self.log(f'❌ Error checking processes: {e}')
        
        # Check port usage
        try:
            result = subprocess.run(['lsof', '-i', ':8080'], capture_output=True, text=True)
            if result.returncode == 0:
                system_info['port_8080'] = result.stdout
                self.log('🌐 Port 8080 is in use')
            else:
                self.log('❌ Port 8080 not in use')
                
        except Exception as e:
            self.log(f'⚠️  Could not check port 8080: {e}')
        
        # Check port 5173 (dashboard)
        try:
            result = subprocess.run(['lsof', '-i', ':5173'], capture_output=True, text=True)
            if result.returncode == 0:
                system_info['port_5173'] = result.stdout
                self.log('🌐 Port 5173 is in use (Dashboard)')
            else:
                self.log('❌ Port 5173 not in use')
                
        except Exception as e:
            self.log(f'⚠️  Could not check port 5173: {e}')
        
        # Save system state
        system_state_file = self.screenshots_dir / f'system_state_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(system_state_file, 'w') as f:
            f.write('System State Summary
')
            f.write('=' * 30 + '
')
            f.write(f'Timestamp: {datetime.now().isoformat()}

')
            
            for key, value in system_info.items():
                f.write(f'{key}:
')
                if isinstance(value, list):
                    for item in value:
                        f.write(f'  {item}
')
                else:
                    f.write(f'  {value}
')
                f.write('
')
        
        self.log(f'💾 System state saved to {system_state_file}')
        
        return system_info
    
    def run_visual_tests(self):
        """Run comprehensive visual testing"""
        self.log('🎨 Starting Visual GUI Testing Suite')
        self.log('=' * 50)
        
        # Initial desktop state
        self.take_screenshot('00_initial_desktop', 'Initial desktop state')
        
        # Test system state
        system_info = self.test_system_state()
        
        # Test menu bar app
        menubar_result = self.check_menubar_app()
        
        # Test dashboard
        dashboard_result = self.check_dashboard()
        
        # Check terminal output
        self.check_terminal_output()
        
        # Final desktop state
        self.take_screenshot('99_final_desktop', 'Final desktop state')
        
        # Generate visual test summary
        self.generate_visual_summary(menubar_result, dashboard_result, system_info)
    
    def generate_visual_summary(self, menubar_result, dashboard_result, system_info):
        """Generate summary of visual tests"""
        self.log('
📊 VISUAL TESTING SUMMARY')
        self.log('=' * 50)
        
        # Count screenshots taken
        screenshots = list(self.screenshots_dir.glob('*.png'))
        self.log(f'📸 Screenshots captured: {len(screenshots)}')
        
        # Component status
        self.log(f'🖥️  Menu Bar App: {"✅ Running" if menubar_result else "❌ Not detected"}')
        self.log(f'🌐 Dashboard: {"✅ Available" if dashboard_result else "❌ Not available"}')
        
        # System info
        if 'python_processes' in system_info:
            self.log(f'🐍 Python Processes: {len(system_info["python_processes"])}')
        
        # List all captured screenshots
        self.log('
📁 Captured Screenshots:')
        for screenshot in sorted(screenshots):
            self.log(f'  - {screenshot.name}')
        
        # Save summary to file
        summary_file = self.screenshots_dir / f'visual_test_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(summary_file, 'w') as f:
            f.write('Visual Testing Summary
')
            f.write('=' * 30 + '
')
            f.write(f'Test Date: {datetime.now().isoformat()}
')
            f.write(f'Screenshots Captured: {len(screenshots)}
')
            f.write(f'Menu Bar App: {"Running" if menubar_result else "Not detected"}
')
            f.write(f'Dashboard: {"Available" if dashboard_result else "Not available"}

')
            
            f.write('Screenshot Files:
')
            for screenshot in sorted(screenshots):
                f.write(f'  {screenshot.name}
')
        
        self.log(f'
📄 Visual summary saved to {summary_file}')

if __name__ == '__main__':
    tester = VisualGUITester()
    tester.run_visual_tests()

