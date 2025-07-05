#!/usr/bin/env python3
"""
Structured logging configuration for production deployment
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import json

def setup_structured_logging(
    app_name: str = "impetus-llm-server",
    log_level: str = None,
    log_file: str = None,
    max_bytes: int = None,
    backup_count: int = None
):
    """
    Setup structured logging with rotation and JSON formatting
    
    Args:
        app_name: Application name for log entries
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    
    # Get configuration from environment or use defaults
    log_level = log_level or os.environ.get('LOG_LEVEL', 'INFO')
    log_file = log_file or os.environ.get('LOG_FILE', 'logs/impetus.log')
    max_bytes = max_bytes or int(os.environ.get('LOG_MAX_BYTES', '10485760'))  # 10MB
    backup_count = backup_count or int(os.environ.get('LOG_BACKUP_COUNT', '5'))
    
    # Create logs directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create custom JSON formatter
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'app': app_name,
                'process_id': os.getpid(),
                'thread_name': record.threadName,
            }
            
            # Add exception info if present
            if record.exc_info:
                log_entry['exception'] = self.formatException(record.exc_info)
            
            # Add extra fields
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'created', 'filename', 
                              'funcName', 'levelname', 'levelno', 'lineno', 
                              'module', 'msecs', 'pathname', 'process', 
                              'processName', 'relativeCreated', 'thread', 
                              'threadName', 'exc_info', 'exc_text', 'stack_info']:
                    log_entry[key] = value
            
            return json.dumps(log_entry)
    
    # Create formatters
    json_formatter = JsonFormatter()
    
    # Console formatter (human-readable)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation (JSON format)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler (separate file for errors)
    error_log_file = log_path.parent / f"{log_path.stem}_errors{log_path.suffix}"
    error_handler = logging.handlers.RotatingFileHandler(
        str(error_log_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)
    
    # Audit logger for security events
    audit_logger = logging.getLogger('audit')
    audit_log_file = log_path.parent / f"{log_path.stem}_audit{log_path.suffix}"
    audit_handler = logging.handlers.RotatingFileHandler(
        str(audit_log_file),
        maxBytes=max_bytes,
        backupCount=backup_count * 2,  # Keep more audit logs
        encoding='utf-8'
    )
    audit_handler.setFormatter(json_formatter)
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    
    # Log startup message
    root_logger.info(
        "Logging initialized",
        extra={
            'log_level': log_level,
            'log_file': str(log_file),
            'max_bytes': max_bytes,
            'backup_count': backup_count
        }
    )
    
    return root_logger

def get_audit_logger():
    """Get the audit logger for security events"""
    return logging.getLogger('audit')

def log_security_event(event_type: str, user: str = None, details: dict = None):
    """
    Log a security event to the audit log
    
    Args:
        event_type: Type of security event (login, access_denied, etc.)
        user: User associated with the event
        details: Additional event details
    """
    audit_logger = get_audit_logger()
    audit_logger.info(
        f"Security event: {event_type}",
        extra={
            'event_type': event_type,
            'user': user,
            'details': details or {},
            'ip_address': details.get('ip_address') if details else None
        }
    )

# Request logging middleware
def log_request(request, response_status: int, response_time_ms: float):
    """Log HTTP request details"""
    logger = logging.getLogger('http')
    
    logger.info(
        "HTTP Request",
        extra={
            'method': request.method,
            'path': request.path,
            'status': response_status,
            'response_time_ms': response_time_ms,
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'referer': request.headers.get('Referer')
        }
    )

# Export convenience functions
__all__ = [
    'setup_structured_logging',
    'get_audit_logger',
    'log_security_event',
    'log_request'
]