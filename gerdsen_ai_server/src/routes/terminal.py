#!/usr/bin/env python3
"""
Terminal and Logging API Routes
Provides terminal interface and comprehensive logging functionality
"""

from flask import Blueprint, jsonify, request
from flask_socketio import emit
import logging
import subprocess
import threading
import time
import os
import json
from datetime import datetime
from typing import Dict, List, Any
from collections import deque
import shlex

terminal_bp = Blueprint('terminal', __name__)

# Global terminal sessions and logs storage
terminal_sessions = {}
system_logs = deque(maxlen=10000)  # Keep last 10000 log entries
log_lock = threading.Lock()

class TerminalSession:
    """Manages a terminal session with command execution and history"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history = deque(maxlen=1000)
        self.current_directory = os.path.expanduser("~")
        self.environment = os.environ.copy()
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command and return the result"""
        self.last_activity = datetime.now()
        
        # Add command to history
        self.history.append({
            'type': 'command',
            'content': command,
            'timestamp': datetime.now().isoformat(),
            'directory': self.current_directory
        })
        
        try:
            # Handle built-in commands
            if command.strip() == 'clear':
                self.history.clear()
                return {
                    'success': True,
                    'output': '',
                    'type': 'clear'
                }
            
            elif command.strip().startswith('cd '):
                return self._handle_cd_command(command)
            
            elif command.strip() == 'pwd':
                output = self.current_directory
                self._add_output(output)
                return {
                    'success': True,
                    'output': output,
                    'type': 'output'
                }
            
            elif command.strip() == 'history':
                history_output = '\n'.join([
                    f"{i+1:4d}  {entry['content']}" 
                    for i, entry in enumerate(self.history) 
                    if entry['type'] == 'command'
                ])
                self._add_output(history_output)
                return {
                    'success': True,
                    'output': history_output,
                    'type': 'output'
                }
            
            elif command.strip() in ['exit', 'quit']:
                return {
                    'success': True,
                    'output': 'Terminal session ended',
                    'type': 'exit'
                }
            
            # Handle system commands
            else:
                return self._execute_system_command(command)
                
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            self._add_output(error_msg, 'error')
            log_system_event('error', f"Terminal command error: {error_msg}")
            return {
                'success': False,
                'output': error_msg,
                'type': 'error'
            }
    
    def _handle_cd_command(self, command: str) -> Dict[str, Any]:
        """Handle cd command"""
        try:
            parts = shlex.split(command)
            if len(parts) == 1:
                # cd with no arguments goes to home
                new_dir = os.path.expanduser("~")
            else:
                new_dir = parts[1]
                if not os.path.isabs(new_dir):
                    new_dir = os.path.join(self.current_directory, new_dir)
                new_dir = os.path.abspath(new_dir)
            
            if os.path.isdir(new_dir):
                self.current_directory = new_dir
                self.environment['PWD'] = new_dir
                output = f"Changed directory to: {new_dir}"
                self._add_output(output)
                return {
                    'success': True,
                    'output': output,
                    'type': 'output',
                    'directory_changed': True,
                    'new_directory': new_dir
                }
            else:
                error_msg = f"cd: {new_dir}: No such file or directory"
                self._add_output(error_msg, 'error')
                return {
                    'success': False,
                    'output': error_msg,
                    'type': 'error'
                }
                
        except Exception as e:
            error_msg = f"cd: {str(e)}"
            self._add_output(error_msg, 'error')
            return {
                'success': False,
                'output': error_msg,
                'type': 'error'
            }
    
    def _execute_system_command(self, command: str) -> Dict[str, Any]:
        """Execute a system command"""
        try:
            # Security: Only allow safe commands
            safe_commands = [
                'ls', 'dir', 'pwd', 'whoami', 'date', 'echo', 'cat', 'head', 'tail',
                'grep', 'find', 'ps', 'top', 'df', 'du', 'free', 'uname', 'uptime',
                'which', 'whereis', 'file', 'wc', 'sort', 'uniq', 'cut', 'awk',
                'python3', 'python', 'pip3', 'pip', 'node', 'npm', 'git'
            ]
            
            command_parts = shlex.split(command)
            if not command_parts:
                return {
                    'success': False,
                    'output': 'Empty command',
                    'type': 'error'
                }
            
            base_command = command_parts[0]
            
            # Check if command is safe
            if base_command not in safe_commands and not base_command.startswith('./'):
                error_msg = f"Command '{base_command}' is not allowed for security reasons"
                self._add_output(error_msg, 'error')
                return {
                    'success': False,
                    'output': error_msg,
                    'type': 'error'
                }
            
            # Execute the command
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.current_directory,
                env=self.environment,
                timeout=30  # 30 second timeout
            )
            
            stdout, stderr = process.communicate()
            
            # Combine output
            output = ""
            if stdout:
                output += stdout
            if stderr:
                if output:
                    output += "\n"
                output += stderr
            
            # Add to history
            self._add_output(output, 'error' if process.returncode != 0 else 'output')
            
            return {
                'success': process.returncode == 0,
                'output': output,
                'type': 'error' if process.returncode != 0 else 'output',
                'return_code': process.returncode
            }
            
        except subprocess.TimeoutExpired:
            error_msg = "Command timed out after 30 seconds"
            self._add_output(error_msg, 'error')
            return {
                'success': False,
                'output': error_msg,
                'type': 'error'
            }
        except Exception as e:
            error_msg = f"Command execution failed: {str(e)}"
            self._add_output(error_msg, 'error')
            return {
                'success': False,
                'output': error_msg,
                'type': 'error'
            }
    
    def _add_output(self, output: str, output_type: str = 'output'):
        """Add output to history"""
        self.history.append({
            'type': output_type,
            'content': output,
            'timestamp': datetime.now().isoformat(),
            'directory': self.current_directory
        })
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get terminal history"""
        return list(self.history)[-limit:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get terminal session status"""
        return {
            'session_id': self.session_id,
            'current_directory': self.current_directory,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'history_length': len(self.history)
        }

def log_system_event(level: str, message: str, category: str = 'system', **kwargs):
    """Log a system event"""
    with log_lock:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.upper(),
            'category': category,
            'message': message,
            'session_id': kwargs.get('session_id'),
            'user_id': kwargs.get('user_id'),
            'extra_data': {k: v for k, v in kwargs.items() if k not in ['session_id', 'user_id']}
        }
        
        system_logs.append(log_entry)
        
        # Also log to Python logging system
        logger = logging.getLogger(f'gerdsen_ai.{category}')
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{category}] {message}")

@terminal_bp.route('/create-session', methods=['POST'])
def create_terminal_session():
    """Create a new terminal session"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id', f"terminal_{int(time.time())}")
        
        if session_id in terminal_sessions:
            return jsonify({
                'success': False,
                'error': 'Session already exists'
            }), 400
        
        session = TerminalSession(session_id)
        terminal_sessions[session_id] = session
        
        log_system_event('info', f'Terminal session created: {session_id}', 'terminal', session_id=session_id)
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id,
                'status': session.get_status()
            }
        })
        
    except Exception as e:
        log_system_event('error', f'Failed to create terminal session: {str(e)}', 'terminal')
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/execute', methods=['POST'])
def execute_command():
    """Execute a command in a terminal session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({
                'success': False,
                'error': 'Command is required'
            }), 400
        
        # Get or create session
        if session_id not in terminal_sessions:
            terminal_sessions[session_id] = TerminalSession(session_id)
        
        session = terminal_sessions[session_id]
        result = session.execute_command(command)
        
        log_system_event('info', f'Command executed: {command}', 'terminal', 
                        session_id=session_id, command=command, success=result['success'])
        
        return jsonify({
            'success': True,
            'data': result,
            'session_status': session.get_status()
        })
        
    except Exception as e:
        log_system_event('error', f'Command execution failed: {str(e)}', 'terminal')
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/history/<session_id>', methods=['GET'])
def get_terminal_history(session_id):
    """Get terminal history for a session"""
    try:
        if session_id not in terminal_sessions:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        session = terminal_sessions[session_id]
        limit = request.args.get('limit', 100, type=int)
        history = session.get_history(limit)
        
        return jsonify({
            'success': True,
            'data': {
                'history': history,
                'session_status': session.get_status()
            }
        })
        
    except Exception as e:
        log_system_event('error', f'Failed to get terminal history: {str(e)}', 'terminal')
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/sessions', methods=['GET'])
def list_terminal_sessions():
    """List all terminal sessions"""
    try:
        sessions_info = {}
        for session_id, session in terminal_sessions.items():
            sessions_info[session_id] = session.get_status()
        
        return jsonify({
            'success': True,
            'data': {
                'sessions': sessions_info,
                'total_sessions': len(terminal_sessions)
            }
        })
        
    except Exception as e:
        log_system_event('error', f'Failed to list terminal sessions: {str(e)}', 'terminal')
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/close-session/<session_id>', methods=['DELETE'])
def close_terminal_session(session_id):
    """Close a terminal session"""
    try:
        if session_id not in terminal_sessions:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        del terminal_sessions[session_id]
        log_system_event('info', f'Terminal session closed: {session_id}', 'terminal', session_id=session_id)
        
        return jsonify({
            'success': True,
            'message': f'Session {session_id} closed'
        })
        
    except Exception as e:
        log_system_event('error', f'Failed to close terminal session: {str(e)}', 'terminal')
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/logs', methods=['GET'])
def get_system_logs():
    """Get system logs with filtering options"""
    try:
        # Get query parameters
        level = request.args.get('level', '').upper()
        category = request.args.get('category', '')
        limit = request.args.get('limit', 1000, type=int)
        since = request.args.get('since', '')  # ISO timestamp
        
        # Filter logs
        filtered_logs = []
        
        with log_lock:
            for log_entry in system_logs:
                # Filter by level
                if level and log_entry['level'] != level:
                    continue
                
                # Filter by category
                if category and log_entry['category'] != category:
                    continue
                
                # Filter by timestamp
                if since:
                    try:
                        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                        log_dt = datetime.fromisoformat(log_entry['timestamp'])
                        if log_dt < since_dt:
                            continue
                    except ValueError:
                        pass  # Invalid timestamp format, ignore filter
                
                filtered_logs.append(log_entry)
        
        # Apply limit
        filtered_logs = filtered_logs[-limit:]
        
        return jsonify({
            'success': True,
            'data': {
                'logs': filtered_logs,
                'total_logs': len(filtered_logs),
                'filters_applied': {
                    'level': level or 'all',
                    'category': category or 'all',
                    'limit': limit,
                    'since': since or 'none'
                }
            }
        })
        
    except Exception as e:
        log_system_event('error', f'Failed to get system logs: {str(e)}', 'logging')
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/logs/categories', methods=['GET'])
def get_log_categories():
    """Get available log categories"""
    try:
        categories = set()
        levels = set()
        
        with log_lock:
            for log_entry in system_logs:
                categories.add(log_entry['category'])
                levels.add(log_entry['level'])
        
        return jsonify({
            'success': True,
            'data': {
                'categories': sorted(list(categories)),
                'levels': sorted(list(levels)),
                'total_logs': len(system_logs)
            }
        })
        
    except Exception as e:
        log_system_event('error', f'Failed to get log categories: {str(e)}', 'logging')
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/logs/export', methods=['GET'])
def export_logs():
    """Export logs as JSON or text"""
    try:
        format_type = request.args.get('format', 'json').lower()
        level = request.args.get('level', '').upper()
        category = request.args.get('category', '')
        
        # Filter logs
        filtered_logs = []
        
        with log_lock:
            for log_entry in system_logs:
                if level and log_entry['level'] != level:
                    continue
                if category and log_entry['category'] != category:
                    continue
                filtered_logs.append(log_entry)
        
        if format_type == 'text':
            # Export as text format
            text_lines = []
            for log_entry in filtered_logs:
                line = f"{log_entry['timestamp']} [{log_entry['level']}] [{log_entry['category']}] {log_entry['message']}"
                text_lines.append(line)
            
            response_data = '\n'.join(text_lines)
            mimetype = 'text/plain'
        else:
            # Export as JSON
            response_data = json.dumps(filtered_logs, indent=2)
            mimetype = 'application/json'
        
        from flask import Response
        return Response(
            response_data,
            mimetype=mimetype,
            headers={
                'Content-Disposition': f'attachment; filename=gerdsen_ai_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{format_type}'
            }
        )
        
    except Exception as e:
        log_system_event('error', f'Failed to export logs: {str(e)}', 'logging')
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/logs/clear', methods=['DELETE'])
def clear_logs():
    """Clear system logs"""
    try:
        with log_lock:
            system_logs.clear()
        
        log_system_event('info', 'System logs cleared', 'logging')
        
        return jsonify({
            'success': True,
            'message': 'System logs cleared'
        })
        
    except Exception as e:
        log_system_event('error', f'Failed to clear logs: {str(e)}', 'logging')
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/logs/stats', methods=['GET'])
def get_log_stats():
    """Get logging statistics"""
    try:
        stats = {
            'total_logs': 0,
            'by_level': {},
            'by_category': {},
            'recent_activity': []
        }
        
        with log_lock:
            stats['total_logs'] = len(system_logs)
            
            # Count by level and category
            for log_entry in system_logs:
                level = log_entry['level']
                category = log_entry['category']
                
                stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Get recent activity (last 10 entries)
            stats['recent_activity'] = list(system_logs)[-10:]
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        log_system_event('error', f'Failed to get log stats: {str(e)}', 'logging')
        return jsonify({'error': str(e)}), 500

# Initialize logging
log_system_event('info', 'Terminal and logging system initialized', 'system')

# Cleanup old sessions periodically
def cleanup_old_sessions():
    """Clean up old inactive terminal sessions"""
    while True:
        try:
            current_time = datetime.now()
            sessions_to_remove = []
            
            for session_id, session in terminal_sessions.items():
                # Remove sessions inactive for more than 1 hour
                if (current_time - session.last_activity).total_seconds() > 3600:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del terminal_sessions[session_id]
                log_system_event('info', f'Cleaned up inactive terminal session: {session_id}', 'terminal')
            
            time.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            log_system_event('error', f'Session cleanup error: {str(e)}', 'terminal')
            time.sleep(300)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_sessions, daemon=True)
cleanup_thread.start()

