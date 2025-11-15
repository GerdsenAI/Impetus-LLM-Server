#!/usr/bin/env python3
"""
Single Instance Manager for Impetus Menu Bar Apps
Prevents multiple instances from running simultaneously
"""

import os
import sys
import fcntl
import atexit
import signal
import psutil
import time
from pathlib import Path
from typing import Optional, List, Dict

class SingleInstance:
    """Manages single instance locking for the menu bar application"""
    
    def __init__(self, app_id: str = "impetus_menubar"):
        """
        Initialize single instance manager
        
        Args:
            app_id: Unique identifier for this application
        """
        self.app_id = app_id
        self.lock_dir = Path("/tmp")
        self.lock_file_path = self.lock_dir / f".{app_id}.lock"
        self.pid_file_path = self.lock_dir / f".{app_id}.pid"
        self.lock_file = None
        self.acquired = False
        
    def acquire(self) -> bool:
        """
        Try to acquire the single instance lock
        
        Returns:
            True if lock acquired, False if another instance is running
        """
        try:
            # Try to create and lock the file
            self.lock_file = open(self.lock_file_path, 'w')
            fcntl.lockf(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write our PID
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()
            
            # Also write PID to separate file for easy reading
            self.pid_file_path.write_text(str(os.getpid()))
            
            # Register cleanup
            atexit.register(self.release)
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            
            self.acquired = True
            return True
            
        except IOError:
            # Lock failed - another instance is running
            if self.lock_file:
                self.lock_file.close()
                self.lock_file = None
            return False
    
    def release(self):
        """Release the lock and clean up"""
        if self.lock_file and self.acquired:
            try:
                fcntl.lockf(self.lock_file, fcntl.LOCK_UN)
                self.lock_file.close()
            except:
                pass
            
            # Clean up lock files
            try:
                self.lock_file_path.unlink()
            except:
                pass
            
            try:
                self.pid_file_path.unlink()
            except:
                pass
            
            self.acquired = False
            self.lock_file = None
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        self.release()
        sys.exit(0)
    
    def get_existing_pid(self) -> Optional[int]:
        """
        Get PID of existing instance if running
        
        Returns:
            PID of existing instance or None
        """
        try:
            if self.pid_file_path.exists():
                pid = int(self.pid_file_path.read_text().strip())
                # Verify process is actually running
                if psutil.pid_exists(pid):
                    try:
                        proc = psutil.Process(pid)
                        # Check if it's actually a Python process
                        if 'python' in proc.name().lower():
                            return pid
                    except:
                        pass
        except:
            pass
        return None
    
    def force_acquire(self) -> bool:
        """
        Force acquire lock by killing existing instance
        
        Returns:
            True if lock acquired after forcing, False otherwise
        """
        existing_pid = self.get_existing_pid()
        
        if existing_pid:
            try:
                # Try graceful termination first
                os.kill(existing_pid, signal.SIGTERM)
                time.sleep(1)
                
                # Check if still running
                if psutil.pid_exists(existing_pid):
                    # Force kill
                    os.kill(existing_pid, signal.SIGKILL)
                    time.sleep(0.5)
            except:
                pass
        
        # Clean up stale lock files
        try:
            self.lock_file_path.unlink()
        except:
            pass
        
        try:
            self.pid_file_path.unlink()
        except:
            pass
        
        # Try to acquire lock
        return self.acquire()


def find_menubar_processes() -> List[Dict]:
    """
    Find all running Impetus menu bar processes
    
    Returns:
        List of process info dictionaries
    """
    menubar_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            info = proc.info
            if info['cmdline'] and any('menubar' in str(arg) for arg in info['cmdline']):
                # Check if it's a Python process running our menu bar apps
                if any('run_menubar' in str(arg) for arg in info['cmdline']):
                    menubar_processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'cmdline': ' '.join(info['cmdline']),
                        'create_time': info['create_time']
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return menubar_processes


def kill_all_menubar_processes(except_pid: Optional[int] = None) -> int:
    """
    Kill all menu bar processes except the specified one
    
    Args:
        except_pid: PID to exclude from killing
        
    Returns:
        Number of processes killed
    """
    killed = 0
    processes = find_menubar_processes()
    
    for proc_info in processes:
        if proc_info['pid'] != except_pid and proc_info['pid'] != os.getpid():
            try:
                proc = psutil.Process(proc_info['pid'])
                proc.terminate()
                killed += 1
            except:
                pass
    
    if killed > 0:
        time.sleep(1)  # Give processes time to terminate
    
    return killed


def kill_menubar_process(pid: int) -> bool:
    """
    Kill a specific menu bar process by PID
    
    Args:
        pid: Process ID to kill
        
    Returns:
        True if process was killed, False otherwise
    """
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        time.sleep(0.5)
        if proc.is_running():
            proc.kill()
        return True
    except:
        return False