"""
Production configuration and hardening for Impetus LLM Server
"""

import logging
import os
import sys
from pathlib import Path

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from loguru import logger


def configure_production_environment():
    """Configure secure production environment settings"""

    # Security: Force localhost-only binding
    os.environ.setdefault('IMPETUS_HOST', '127.0.0.1')
    os.environ.setdefault('IMPETUS_PORT', '8080')

    # Disable debug mode explicitly
    os.environ.setdefault('IMPETUS_DEBUG', 'false')

    # Set conservative performance defaults
    os.environ.setdefault('IMPETUS_MAX_LOADED_MODELS', '2')
    os.environ.setdefault('IMPETUS_MAX_TOKENS', '1024')
    os.environ.setdefault('IMPETUS_PERFORMANCE_MODE', 'balanced')

    # Logging configuration
    os.environ.setdefault('IMPETUS_LOG_LEVEL', 'info')

    # Security: Lock down CORS to localhost only
    os.environ.setdefault('IMPETUS_CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173')

    # Set production cache and models directories
    app_support = Path.home() / "Library" / "Application Support" / "Impetus"
    os.environ.setdefault('IMPETUS_MODELS_DIR', str(app_support / "models"))
    os.environ.setdefault('IMPETUS_CACHE_DIR', str(Path.home() / "Library" / "Caches" / "com.gerdsenai.impetus"))

    # Conservative memory settings for user machines
    os.environ.setdefault('IMPETUS_MAX_MEMORY_GB', '8')

    # API security
    os.environ.setdefault('IMPETUS_API_KEY', '')  # Will be auto-generated on first run


def validate_production_security():
    """Validate that production security settings are correct"""

    host = os.environ.get('IMPETUS_HOST', '')
    debug = os.environ.get('IMPETUS_DEBUG', '').lower()

    security_issues = []

    # Check host binding
    if host not in ['127.0.0.1', 'localhost']:
        security_issues.append(f"⚠️  Insecure host binding: {host} (should be 127.0.0.1)")

    # Check debug mode
    if debug not in ['false', '0', '']:
        security_issues.append("⚠️  Debug mode enabled in production")

    # Check CORS origins
    cors_origins = os.environ.get('IMPETUS_CORS_ORIGINS', '')
    if '*' in cors_origins:
        security_issues.append("⚠️  Wildcard CORS allowed in production")

    if security_issues:
        print("🚨 SECURITY ISSUES DETECTED:")
        for issue in security_issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ Production security validation passed")
        return True


def configure_rate_limiting(app: Flask) -> Limiter:
    """Configure rate limiting for production"""
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
        strategy="fixed-window"
    )

    # Specific limits for expensive endpoints
    @limiter.limit("5 per minute")
    def limit_model_operations():
        pass

    @limiter.limit("10 per minute")
    def limit_inference():
        pass

    @limiter.limit("100 per minute")
    def limit_api_calls():
        pass

    return limiter


def configure_logging(app: Flask):
    """Configure production logging"""
    # Remove default handlers
    logger.remove()

    # Add production handlers
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        level="INFO",
        backtrace=False,
        diagnose=False
    )

    # Add file handler for errors
    logger.add(
        "logs/error.log",
        format="{time} | {level} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="100 MB",
        retention="30 days",
        backtrace=True,
        diagnose=True
    )

    # Add file handler for all logs
    logger.add(
        "logs/impetus.log",
        format="{time} | {level} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="500 MB",
        retention="7 days",
        compression="zip"
    )

    # Configure Flask logging
    app.logger.handlers = []
    app.logger.propagate = False

    # Intercept Flask logs
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            logger_opt = logger.opt(depth=6, exception=record.exc_info)
            logger_opt.log(record.levelname, record.getMessage())

    app.logger.addHandler(InterceptHandler())


def configure_security(app: Flask):
    """Configure security headers and settings"""
    @app.after_request
    def set_security_headers(response):
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # CORS headers are handled by flask-cors
        return response

    # Additional security settings
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=3600,  # 1 hour
        MAX_CONTENT_LENGTH=100 * 1024 * 1024  # 100MB max request size
    )


def configure_connection_pooling(app: Flask):
    """Configure connection pooling for concurrent requests"""
    # This is handled by eventlet/gevent at the WSGI server level
    # But we can configure some app-level pooling
    app.config.update(
        # Maximum concurrent model inference requests
        MAX_CONCURRENT_INFERENCES=10,
        # Request queue size
        REQUEST_QUEUE_SIZE=100,
        # Timeout for queued requests
        REQUEST_TIMEOUT=30,
        # Connection pool settings for any external services
        POOL_SIZE=20,
        POOL_MAX_OVERFLOW=40,
        POOL_TIMEOUT=30
    )


def configure_graceful_shutdown(app: Flask, socketio):
    """Configure graceful shutdown handlers"""
    import signal
    import sys

    def shutdown_handler(signum, frame):
        logger.info("Received shutdown signal, initiating graceful shutdown...")

        # Stop accepting new requests
        app.config['SHUTTING_DOWN'] = True

        # Wait for active requests to complete (with timeout)
        import time
        timeout = 30  # 30 seconds
        start = time.time()

        while True:
            active = app.config.get('ACTIVE_REQUESTS', 0)
            if active == 0:
                break
            if time.time() - start > timeout:
                logger.warning(f"Timeout waiting for {active} active requests")
                break
            time.sleep(0.1)

        # Clean shutdown
        socketio.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)


def apply_production_config(app: Flask, socketio):
    """Apply all production configurations"""
    # Set production mode
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False
    app.config['TESTING'] = False

    # Configure components
    limiter = configure_rate_limiting(app)
    configure_logging(app)
    configure_security(app)
    configure_connection_pooling(app)
    configure_graceful_shutdown(app, socketio)

    # Middleware for request tracking
    @app.before_request
    def track_request():
        if not app.config.get('SHUTTING_DOWN', False):
            app.config['ACTIVE_REQUESTS'] = app.config.get('ACTIVE_REQUESTS', 0) + 1

    @app.after_request
    def untrack_request(response):
        app.config['ACTIVE_REQUESTS'] = max(0, app.config.get('ACTIVE_REQUESTS', 0) - 1)
        return response

    return limiter
